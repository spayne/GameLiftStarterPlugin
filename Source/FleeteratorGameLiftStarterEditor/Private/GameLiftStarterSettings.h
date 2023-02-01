// Copyright Sean Payne All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameLiftStarterSettings.generated.h"




UCLASS(config = Editor, defaultconfig)
class FLEETERATORGAMELIFTSTARTEREDITOR_API UGameLiftStarterSettings : public UObject
{
	GENERATED_UCLASS_BODY()
public:

	/** Choose a unique lowercase name to help track resources. */
	UPROPERTY(EditAnywhere, config)
	FString FleetPrefix;

	/** Use your AWS named profile */
	UPROPERTY(EditAnywhere, config)
	FString AWSProfile;

	/** Choose a nearby AWS region */
	UPROPERTY(EditAnywhere, config)
	FString AWSRegion;

	/** Use pip show boto3 to find this */
	UPROPERTY(EditAnywhere, config)
	FString BOTO3Path;

	/** The directory where your server package is.  For Windows, this path will end in WindowsServer */
	UPROPERTY(EditAnywhere, config)
	FString ServerPackageRoot;

	/** This has to have the prefix c:/game and then the path to the exe */
	UPROPERTY(EditAnywhere, config)
	FString FleetLaunchPath;

};


