// Copyright Sean Payne All Rights Reserved.


#include "GameLiftOfflineMenuBase.h"
#include "Json.h"
#include "JsonUtilities.h"
#include "Kismet/GameplayStatics.h"
#include "Logging/LogMacros.h"

UGameLiftOfflineMenuBase::UGameLiftOfflineMenuBase(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	Http = &FHttpModule::Get();
	ApiGatewayEndpoint = FString::Printf(TEXT("https://82cao6j0oc.execute-api.us-west-2.amazonaws.com/testfleet-api-test-stage"));
	LoginURI = FString::Printf(TEXT("/login"));
	StartSessionURI = FString::Printf(TEXT("/startsession"));
}

void UGameLiftOfflineMenuBase::OnLoginClicked()
{
	LoginRequest(user, pass);
}

void UGameLiftOfflineMenuBase::LoginRequest(FString usr, FString pwd)
{
	TSharedPtr<FJsonObject> JsonObject = MakeShareable(new FJsonObject());
	JsonObject->SetStringField(TEXT("username"), *FString::Printf(TEXT("%s"), *usr));
	JsonObject->SetStringField(TEXT("password"), *FString::Printf(TEXT("%s"), *pwd));

	UE_LOG(LogGameLift, Warning, TEXT("About to make login request to %s with %s/%s"), 
		*ApiGatewayEndpoint, *usr, *pwd);

	// stick it into JsonBody
	FString JsonBody;
	TSharedRef<TJsonWriter<TCHAR>> JsonWriter = TJsonWriterFactory<>::Create(&JsonBody);
	FJsonSerializer::Serialize(JsonObject.ToSharedRef(), JsonWriter);

	// make http request
	TSharedRef<IHttpRequest, ESPMode::ThreadSafe> LoginHttpRequest = Http->CreateRequest();
	LoginHttpRequest->SetVerb("POST");
	LoginHttpRequest->SetURL(ApiGatewayEndpoint + LoginURI);
	LoginHttpRequest->SetHeader("Content-Type", "application/json");
	LoginHttpRequest->SetContentAsString(JsonBody);
	LoginHttpRequest->OnProcessRequestComplete().BindUObject(this, &UGameLiftOfflineMenuBase::OnLoginResponse);
	LoginHttpRequest->ProcessRequest();

}

//
// For details on the types of responses that can be returned - look at the login-function lamba
// 
// The successful response will be 200, status: "success"
// Otherwise it is a failure
//
void UGameLiftOfflineMenuBase::OnLoginResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bRequestWasSuccessful)
{
	FString LoginError;
	FString IdToken;

	if (!bRequestWasSuccessful)
	{
		LoginError = TEXT("Got Failed Login - Request could not be made - Check your ApiGatewayEndpoint value");
	}
	else if (!Response.IsValid())
	{
		LoginError = TEXT("Got Failed Login - Response is not valid");
	}
	else
	{
		TSharedPtr<FJsonObject> JsonObject;
		TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Response->GetContentAsString());
		if (!FJsonSerializer::Deserialize(Reader, JsonObject))
		{
			LoginError = TEXT("Got Failed Login - Could not deserialize response");
		}
		else if (!JsonObject->HasField("status"))
		{
			LoginError = TEXT("Got Failed Login - No status field");
		}
		else 
		{
			FString StatusValue = JsonObject->GetStringField("status");
			if (StatusValue != "success")
			{
				LoginError = TEXT("Got Failed Login - Status is not success");
			}
			else if (!JsonObject->HasField("tokens"))
			{
				LoginError = TEXT("Got Failed Login - No tokens field");
			}
			else
			{
				IdToken = JsonObject->GetObjectField("tokens")->GetStringField("IdToken");
			}
		}
	}

	if (LoginError.IsEmpty())
	{
		StartSessionRequest(IdToken);
	}
	else
	{
		UE_LOG(LogGameLift, Warning, TEXT("%s"), *LoginError);
		if (Response.IsValid())
		{
			UE_LOG(LogGameLift, Warning, TEXT("%s"), *Response->GetContentAsString());
		}
	}
}

void UGameLiftOfflineMenuBase::StartSessionRequest(FString idt)
{
	TSharedRef<IHttpRequest, ESPMode::ThreadSafe> StartSessionHttpRequest = Http->CreateRequest();
	StartSessionHttpRequest->SetVerb("GET");
	StartSessionHttpRequest->SetURL(ApiGatewayEndpoint + StartSessionURI);
	StartSessionHttpRequest->SetHeader("Content-Type", "application/json");
	StartSessionHttpRequest->SetHeader("Authorization", idt);
	StartSessionHttpRequest->OnProcessRequestComplete().BindUObject(this, &UGameLiftOfflineMenuBase::OnStartSessionResponse);
	StartSessionHttpRequest->ProcessRequest();

}
void UGameLiftOfflineMenuBase::OnStartSessionResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful)
{
	if (bWasSuccessful)
	{
		TSharedPtr<FJsonObject> JsonObject;
		TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Response->GetContentAsString());

		if (FJsonSerializer::Deserialize(Reader, JsonObject))
		{
			FString PlayerSessionId = JsonObject->GetObjectField("PlayerSession")->GetStringField("PlayerSessionId");
			FString IpAddress = JsonObject->GetObjectField("PlayerSession")->GetStringField("IpAddress");
			FString Port = JsonObject->GetObjectField("PlayerSession")->GetStringField("Port");

			FString LevelName = IpAddress + ":" + Port;
			FString Options = "?PlayerSessionId=" + PlayerSessionId;

			UGameplayStatics::OpenLevel(GetWorld(), FName(*LevelName), false, Options);
		}
	}
}
