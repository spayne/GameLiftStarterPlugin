// Copyright Sean Payne All Rights Reserved.

#include "FleeteratorGameLiftStarterEditor.h"
#include "IFleetManagerModule.h"
#include "ISettingsModule.h"
#include "FleetFactory.h"
#include "GameLiftStarterSettings.h"
#include "GenericPlatform/GenericPlatformHttp.h"
#include "Misc/MessageDialog.h"

#define LOCTEXT_NAMESPACE "FFleeteratorGameLiftStarterEditor"

class GameLiftStarterParams : public IFleetTypeSpecificParams
{

	virtual FString GetPythonPrefixScript() override
	{
		const UGameLiftStarterSettings* Settings = GetDefault<UGameLiftStarterSettings>();
		const FString BOTO3PATH = *Settings->BOTO3Path;
		FString PrefixScript = FString::Printf(TEXT("sys.path.insert(0,'%s')"), *BOTO3PATH);
		return PrefixScript;
	}

	virtual FString GetBackendPathPart() override
	{
		return FString(TEXT("aws_backend/1"));
	}

	virtual FString GetQueryString() override
	{
		const UGameLiftStarterSettings* Settings = GetDefault<UGameLiftStarterSettings>();
		FString ProjectDir = FPaths::ProjectDir();
		FString ProjectRoot = IFileManager::Get().ConvertToAbsolutePathForExternalAppForRead(*ProjectDir);
		FString QueryString = FString::Printf(TEXT("?profile_name=%s&region_name=%s&prefix=%s&server_package_root=\"%s\"&fleet_launch_path=\"%s\"&project_root=\"%s\""),
			*Settings->AWSProfile,
			*Settings->AWSRegion,
			*Settings->FleetPrefix,
			*FGenericPlatformHttp::UrlEncode(Settings->ServerPackageRoot),
			*FGenericPlatformHttp::UrlEncode(Settings->FleetLaunchPath),
			*FGenericPlatformHttp::UrlEncode(ProjectRoot)
		);
		return QueryString;
	}
};

void FFleeteratorGameLiftStarterEditor::StartupModule()
{
	ParamHelper = MakeShared< GameLiftStarterParams>();
	IModularFeatures::Get().RegisterModularFeature(GetModularFeatureName(), this);

	RegisterSettings();
	OnPropertyChangedDelegateHandle = 
		FCoreUObjectDelegates::OnObjectPropertyChanged.AddRaw(this, &FFleeteratorGameLiftStarterEditor::OnPropertyChanged);
}

void FFleeteratorGameLiftStarterEditor::RegisterSettings()
{
	if (ISettingsModule* SettingsModule = FModuleManager::GetModulePtr<ISettingsModule>("Settings"))
	{
		SettingsModule->RegisterSettings("Project", "Plugins", "GameLiftStarter",
			LOCTEXT("RuntimeSettingsName", "Game Lift Starter"),
			LOCTEXT("RuntimeSettingsDescription", "Configures the Game Lift Starter plugin"),
			GetMutableDefault<UGameLiftStarterSettings>());
	}
}


// rule from aws pool subdomain prefix is ^[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?
// * so lowercase alpha numeric and no '-' prefix or suffix
// * the aws_backend.py will also use the fleet prefix and add a 6 character "-login" suffix so the acceptable fleet prefix
//   needs to be ^[a-z0-9](?:[a-z0-9\-]{0,56}
// * but consider: who knows what other limits aws has and how it mixes with other suffixes
// * so I'll just choose to only allow upto 32 characters for the fleet prefix:
//   needs to be ^[a-z0-9](?:[a-z0-9\-]{0,31}
static bool ValidateFleetPrefix(const FString& FleetPrefix)
{
	const FRegexPattern ValidFleetPrefixPatten(TEXT("^[a-z0-9][a-z0-9-]{0,31}$"));
	FRegexMatcher Matcher(ValidFleetPrefixPatten, FleetPrefix);
	bool bFindNext = Matcher.FindNext();
	return bFindNext;
}


void FFleeteratorGameLiftStarterEditor::OnPropertyChanged(UObject* ObjectBeingModified, FPropertyChangedEvent& PropertyChangedEvent)
{
	if (UGameLiftStarterSettings* Settings = Cast<UGameLiftStarterSettings>(ObjectBeingModified))
	{
		FProperty* PropertyThatChanged = PropertyChangedEvent.Property;
		static const FString FleetPrefix = TEXT("FleetPrefix");
		if (PropertyThatChanged != nullptr && PropertyThatChanged->GetName() == FleetPrefix)
		{
			if (!ValidateFleetPrefix(Settings->FleetPrefix))
			{
				static FName NAME_FMErrors("FleetManagerPlugin");
				FMessageLog SettingsError(NAME_FMErrors);
				TSharedRef<FTokenizedMessage> Message = SettingsError.Error();

				Message->AddToken(FTextToken::Create(LOCTEXT("InvalidFleetPrefix1", "The Fleet Prefix")));
				Message->AddToken(FTextToken::Create(FText::FromString(Settings->FleetPrefix)));
				Message->AddToken(FTextToken::Create(LOCTEXT("InvalidFleetPrefix2", "is invalid. Ensure you are using lowercase")));
				SettingsError.Notify();
			}
		}
	}
}



void FFleeteratorGameLiftStarterEditor::UnregisterSettings()
{
	if (ISettingsModule* SettingsModule = FModuleManager::GetModulePtr<ISettingsModule>("Settings"))
	{
		SettingsModule->UnregisterSettings("Project", "Plugins", "Fleeterator");
	}
}

void FFleeteratorGameLiftStarterEditor::ShutdownModule()
{
	IModularFeatures::Get().UnregisterModularFeature(GetModularFeatureName(), this);
	// This function may be called during shutdown to clean up your module.  For modules that support dynamic reloading,
	// we call this function before unloading the module.
	UnregisterSettings();
}

TSharedPtr<IFleet> FFleeteratorGameLiftStarterEditor::CreateFleet()
{
	return FFleetFactory::Create(TEXT("GameLiftStarter"), ParamHelper);
}

#undef LOCTEXT_NAMESPACE
	
IMPLEMENT_MODULE(FFleeteratorGameLiftStarterEditor, FleeteratorGameLiftStarterEditor)
