# Game Lift Starter for Unreal Editor
This plugin makes it easy to setup and tear down GameLift deployments within Unreal Editor.  It uses the [FleetManagerPlugin](https://github.com/spayne/FleetManagerPlugin).

<p align="center">
<img width="800" src="Docs/GUI1.png?raw=true" alt="Game Lift Starter"/>
</p>

The backend design is based on Amazon's video series [Building Games on AWS: Amazon GameLift & UE4](https://www.youtube.com/playlist?list=PLuGWzrvNze7LEn4db8h3Jl325-asqqgP2).

# How to deploy a game server with the Game Lift Starter
The following will take you from start to finish to building and deploy a UE 5.1 GameLift server.  These steps are also demonstrated in the YouTube video [Demo: How to get from Zero to Gamelift Multiplayer project in UE5.1](https://www.youtube.com/watch?v=3AYDX9jRGl8).

## Prerequisites
1. Starting with a source [build](https://github.com/EpicGames/UnrealEngine) of Unreal engine
2. Have an AWS account setup and can run the AWS cli using a [Named profile](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-profiles.html)
    * to confirm, run the following in a windows cmd shell:
    ```
      aws configure list-profiles
      aws gamelift list-fleets --profile [NamedProfileName] --region us-west-2
    ```
3. Install [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html)
    * to confirm, run the following in a windows cmd shell:
    ```
      pip show boto3
    ```

## Step 1 - Create a project
1. Create a new **third person template** C++ project

## Step 2 - Add the plugins
1. Create your project Plugins folder at the same level as Source and clone the following into it: 
```
git clone https://github.com/spayne/FleetManagerPlugin.git FleetManager
git clone https://github.com/spayne/GameLiftStarterPlugin GameLiftStarter
git clone https://github.com/spayne/AWSGameLiftServerSDK GameLiftServerSDK
```

2. Generate Visual Studio project files and then build the Development Editor | Win64 target for your project.  
3. Open the Platforms menu and confirm that you can now see the **Fleet Manager GUI** from the Platforms menu.  Note that opening the Fleet Manager will generate warnings until you specify project settings for it in Step 5 below.
<p align="center">
<img width="400" src="Docs/FleetManagerMenu.png?raw=true" alt="Fleet Manager Menu"/>
</p>

## Step 3 - Setup dedicated server
1. Follow Epic's instructions on [Setting Up Dedicated Servers](https://docs.unrealengine.com/4.27/en-US/InteractiveExperiences/Networking/HowTo/DedicatedServers/).  Read **Note** below. Once you have finished that you will have:
    * the server target,
    * a packaged server build (in the Packaged folder if you used their example)
    * a ProjectNameServer.exe,
    * an Entry Map that Opens 127.0.0.1 on BeginPlay
    * a Server Default map (e.g. Third Person Example Map)
    * __Note: Epic's instructions have you package and build a standalone NoEditor Client, it's faster to do you can do all client side development (including connecting to the AWS servers) with an Editor build (ake PIE) using the "Play Standalone" netmode with a single client and then worry about multiple clients and the NoEditor client once you have it working in PIE with just the one client.

## Step 4 - Check dedicated server works
1. Make sure it works on a single machine

## Step 5 - Modify your project to support GameLift
1. We will now update your project to get the deploy on GameLift:

2. Fill in the GameLiftStarter project settings in the Plugins category:
<p align="center">
<img width="880" src="Docs/ExampleSettings.png?raw=true" alt="Example Settings"/>
</p>

3. Modify the Entry Map Blueprint to open GameLiftOfflineMainMenu (Use CreateWidget and then choose the GameLiftOfflineMainMenu as the class):
<p align="center">
<img width="600" src="Docs/EntryMapBeginPlay.png?raw=true" alt="Entry Map Blueprint"/>
</p>

4. Compile and Save that map.  Now from the Main Editor, click on the three 'vertical buttons' and confirm you have Num Players: 1 and Play Standalone selected:
<p align="center">
<img width="300" src="Docs/OnePlayerStandalone.png?raw=true" alt="New Login Options"/>
</p>

5. Press the Play button in the Editor and confirm you have Login Options on the bottom right in game:
<p align="center">
<img width="200" src="Docs/NewLoginOptions.png?raw=true" alt="New Login Options"/>
</p>

6. Open the ThirdPersonMap and select the world Override Options, use "Select GameModeBase Class" to select GameLiftGameMode.  **Remember to save this map***
<p align="center">
<img width="250" src="Docs/SetGameModeOfThirdPersonMap.png?raw=true" alt="Set Game Mode of the Third Person map"/>
</p>

7. Copy the Plugins/GameLiftStarter/Scripts/install.bat file to the Server Package Root.

8. From within the editor, re-package the server package to make sure everything is going to be in sync between what is on your local machine and the server side. (e.g. the modifications to the ThirdPersonMap).

9. Run the Fleet Manager and click on "Check" to check the Dedicated Server is Packaged.  Confirm that the Ready column shows OK:
<p align="center">
<img width="400" src="Docs/ConfirmDedicatedServerisPackaged.png?raw=true" alt="Confirm Dedicated Server is Packaged"/>
</p>

## Step 6 - Deploy and Test It
1. Click on Upload to upload the Server to GameLift.  This will open a blank window and take a moment (30s-1min) to start uploading.  Eventually you will see a stream of output in both the FleetManager window as well as in the output log showing upload progress.  The window will close and the checkmark for this will go green.

2. Click on Launch to start the fleet.  This will show fleet status is NEW and the status will *not* turn to a checkmark.  This is expected.  Fleet deployment can take about 30 minutes to continue.

3. While the fleet is deploying, click on Create for the remaining 3 items (Cognito, Lambdas, Rest API).  They will all go green and your status should look like this:
<p align="center">
<img width="400" src="Docs/WaitingForFleetToBecomeActive.png?raw=true" alt="Waiting For Fleet To Become Active"/>
</p>

4. Take note of the invoke_url from the Rest API step.  Close the Fleet Manager.  Copy this URL into the APIGatewayEndpoint value in UGameLiftOfflineMenuBase::UGameLiftOfflineMenuBase. (We will figure out a better way to do this later) 
<p align="center">
<img width="400" src="Docs/CopyInvokeURL.png?raw=true" alt="Copy Invoke URL"/>
</p>

5. Rebuild the Development Editor target (to build the update to UGameLiftOfflineMenuBase)

6. Wait for the Fleet to become Active.  You can press the "Check" button to check, or the 'AWS' button to view the status from the AWS console.

7. When the fleet is active, run multiple instances of the Windows client.  If you are using PIE clients, then disable 'Run under one process' in Advanced Settings.  Login using 'user0' and 'test12' as the password
<p align="center">
<img width="400" src="Docs/GameLiftGameSession.png?raw=true" alt="Game Lift Session"/>
</p>

8. Click on the AWS button on the Fleet Row.  Then choose the fleet and then game sessions.  You will see a game session.  From there select Player Session and you will see the player details:
<p align="center">
<img width="400" src="Docs/PlayerSessions.png?raw=true" alt="Player Sessions"/>
</p>

## Step 7 - Tear down the backend
1. When you are done, remember to shutdown all of the AWS service to avoid unnecessary usage charges.

## Next Steps - WSL2
Now that you have a working server on Windows you could try cross compiling and testing on Linux and WSL.  My notes on how to do this are [linux_server_build.md](Docs/linux_server_build.md)
