// Copyright Sean Payne All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "GameLiftGameMode.generated.h"

DECLARE_LOG_CATEGORY_EXTERN(LogGameLift, Log, All);

UCLASS(minimalapi)
class AGameLiftGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	AGameLiftGameMode();

private:
	void SetupGameLift();
	virtual void PreLogin(const FString& Options, const FString& Address, const FUniqueNetIdRepl& UniqueId, FString& ErrorMessage) override;
	bool UseGameLift;
};



