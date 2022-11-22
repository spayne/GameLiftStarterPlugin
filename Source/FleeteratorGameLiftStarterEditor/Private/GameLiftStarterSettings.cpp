// Copyright Sean Payne All Rights Reserved.

#pragma once
#include "GameLiftStarterSettings.h"

UGameLiftStarterSettings::UGameLiftStarterSettings(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer),
		FleetPrefix(TEXT("testfleet")),
		AWSProfile(TEXT("sean_backend")),
		AWSRegion(TEXT("us-west-2")),
		BOTO3Path(TEXT("c:/Users/seand/AppData/Local/Programs/Python/Python310/lib/site-packages"))
{

}

