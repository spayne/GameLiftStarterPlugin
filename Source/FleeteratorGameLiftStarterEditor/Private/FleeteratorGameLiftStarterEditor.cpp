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

static void DisplayPrefixError(const FString& FleetPrefix)
{
	static FName NAME_FMErrors("FleetManagerPlugin");
	FMessageLog SettingsError(NAME_FMErrors);
	TSharedRef<FTokenizedMessage> Message = SettingsError.Error();

	Message->AddToken(FTextToken::Create(LOCTEXT("InvalidFleetPrefix1", "The Fleet Prefix")));
	Message->AddToken(FTextToken::Create(FText::FromString(FleetPrefix)));
	Message->AddToken(FTextToken::Create(LOCTEXT("InvalidFleetPrefix2", "is invalid. Ensure you are using lowercase")));
	SettingsError.Notify();
}

static bool ValidateBoto3Path(const FString& Boto3Path)
{
	bool bValid = FPaths::DirectoryExists(Boto3Path);
	return bValid;
}

static void DisplayBoto3PathError(const FString& Boto3Path)
{
	static FName NAME_FMErrors("FleetManagerPlugin");
	FMessageLog SettingsError(NAME_FMErrors);
	TSharedRef<FTokenizedMessage> Message = SettingsError.Error();

	Message->AddToken(FTextToken::Create(LOCTEXT("InvalidBoto3Path1", "The BOTO3 Path")));
	Message->AddToken(FTextToken::Create(FText::FromString(Boto3Path)));
	Message->AddToken(FTextToken::Create(LOCTEXT("InvalidBoto3Path2", "is invalid. Ensure you have installed BOTO3 and have updated project settings")));
	Message->AddToken(FTextToken::Create(LOCTEXT("InvalidBoto3Path2", "See https://github.com/spayne/GameLiftStarterPlugin#step-5---modify-your-project-to-support-gamelift")));
	SettingsError.Notify();
}



void FFleeteratorGameLiftStarterEditor::OnPropertyChanged(UObject* ObjectBeingModified, FPropertyChangedEvent& PropertyChangedEvent)
{
	if (UGameLiftStarterSettings* Settings = Cast<UGameLiftStarterSettings>(ObjectBeingModified))
	{
		FProperty* PropertyThatChanged = PropertyChangedEvent.Property;
		static const FString FleetPrefix = TEXT("FleetPrefix");
		static const FString Boto3Path = TEXT("BOTO3Path");
		if (PropertyThatChanged != nullptr && PropertyThatChanged->GetName() == FleetPrefix)
		{
			if (!ValidateFleetPrefix(Settings->FleetPrefix))
			{
				DisplayPrefixError(Settings->FleetPrefix);
			}
		}
		else if (PropertyThatChanged != nullptr && PropertyThatChanged->GetName() == Boto3Path)
		{
			if (!ValidateBoto3Path(Settings->BOTO3Path))
			{
				DisplayBoto3PathError(Settings->BOTO3Path);
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

// Verifying the fleet prefix and the boto3path
// the other settings are checked in the python script
bool FFleeteratorGameLiftStarterEditor::VerifySettings()
{
	const UGameLiftStarterSettings* Settings = GetDefault<UGameLiftStarterSettings>();
	bool bSettingsValid = true;
	if (!ValidateFleetPrefix(Settings->FleetPrefix))
	{
		DisplayPrefixError(Settings->FleetPrefix);
		bSettingsValid = false;
	}
	else if (!ValidateBoto3Path(Settings->BOTO3Path))
	{
		DisplayBoto3PathError(Settings->BOTO3Path);
		bSettingsValid = false;
	}
	return bSettingsValid;
}

// This will be called by the Module level to spawn a new GUI.
// the ParamHelper contains the details (e.g Python configuration) required to interface with the particular backend.
TSharedPtr<IFleet> FFleeteratorGameLiftStarterEditor::CreateFleet()
{
	return FFleetFactory::Create(TEXT("GameLiftStarter"), ParamHelper);
}

#undef LOCTEXT_NAMESPACE
	
IMPLEMENT_MODULE(FFleeteratorGameLiftStarterEditor, FleeteratorGameLiftStarterEditor)
