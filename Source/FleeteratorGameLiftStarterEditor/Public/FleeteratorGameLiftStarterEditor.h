// Copyright Sean Payne All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"
#include "IFleetManagerModule.h"

class IFleetTypeSpecificParams;

class FFleeteratorGameLiftStarterEditor : public IFleetManagerModule
{
public:
	/** IModuleInterface implementation */
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;

	virtual TSharedPtr<IFleet> CreateFleet() override;

private:
	void OnPropertyChanged(UObject* ObjectBeingModified, FPropertyChangedEvent& PropertyChangedEvent);
	void RegisterSettings();
	void UnregisterSettings();
	TSharedPtr<IFleetTypeSpecificParams> ParamHelper;
	FDelegateHandle OnPropertyChangedDelegateHandle;
};
