## How to cross compile and run a linux dedicated server using WSL 2
1. https://docs.unrealengine.com/5.1/en-US/linux-development-requirements-for-unreal-engine/ for 5.1 has a link to the (clang 13.01-based)[https://cdn.unrealengine.com/CrossToolchain_Linux/v20_clang-13.0.1-centos7.exe] toolchain.
    * the installer will allow you to choose where to install the toolchain.  I thought I chose E instead of C (E:\UnrealToolchains\v20_clang-13.0.1-centos7). but it ended up in C

2. https://docs.unrealengine.com/4.26/en-US/SharingAndReleasing/Linux/GettingStarted/ suggests running
```
%LINUX_MULTIARCH_ROOT%x86_64-unknown-linux-gnu\bin\clang++ -v
```
And that worked for me as well.

3. After you regenerate the project files the linux target will show up in Visual Studio.

4. Go into UE and package for Linux.  It'll build (1:15pm) (406 @1:28)
```
Building 739 actions with 6 processes...
UATHelper: Packaging (Linux): [1/739] Generate Header GPUSkinVertexFactory.ispc
UATHelper: Packaging (Linux): [2/739] Generate Header BonePose.ispc
LogViewport: Scene viewport resized to 1444x160, mode Windowed.
```

5. before running the server, in wsl find the ip address from ifconfig.  you need to connect to this IP from windows (otherwise windows will try to connect to it's own localhost and not this one itself).  e.g. 172.18.217.193.  (ref: https://superuser.com/questions/1594420/cant-access-127-0-0-180-outside-of-wsl2-ubuntu-20-04)

