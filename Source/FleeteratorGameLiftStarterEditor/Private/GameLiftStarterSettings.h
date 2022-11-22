// Copyright Sean Payne All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameLiftStarterSettings.generated.h"




UCLASS(config = Editor, defaultconfig)
class FLEETERATORGAMELIFTSTARTEREDITOR_API UGameLiftStarterSettings : public UObject
{
	GENERATED_UCLASS_BODY()
public:

	UPROPERTY(EditAnywhere, config)
	FString FleetPrefix;

	UPROPERTY(EditAnywhere, config)
	FString AWSProfile;

	UPROPERTY(EditAnywhere, config)
	FString AWSRegion;

	UPROPERTY(EditAnywhere, config)
	FString BOTO3Path;

	UPROPERTY(EditAnywhere, config)
	FString ServerPackageRoot;

	UPROPERTY(EditAnywhere, config)
	FString FleetLaunchPath;

};


