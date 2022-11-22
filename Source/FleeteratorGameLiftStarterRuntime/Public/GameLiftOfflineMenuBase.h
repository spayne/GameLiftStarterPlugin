// Copyright Sean Payne All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Http.h"
#include "GameLiftOfflineMenuBase.generated.h"

/**
 * 
 */
UCLASS()
class UGameLiftOfflineMenuBase : public UUserWidget
{
	GENERATED_BODY()
	
public:
	UGameLiftOfflineMenuBase(const FObjectInitializer& ObjectInitializer);

	UFUNCTION(BlueprintCallable)
	void OnLoginClicked();

	UPROPERTY(EditAnywhere)
	FString ApiGatewayEndpoint;

	UPROPERTY(EditAnywhere)
	FString LoginURI;

	UPROPERTY(EditAnywhere)
	FString StartSessionURI;

	UPROPERTY(BluePrintReadWrite)
	FString user;

	UPROPERTY(BluePrintReadWrite)
	FString pass;

private:
	FHttpModule* Http;
	void LoginRequest(FString usr, FString pwd);
	void OnLoginResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful);
	void StartSessionRequest(FString idt);
	void OnStartSessionResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful);
};
