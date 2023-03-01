# Existing fleet manager backend design
The code that knows how to write to communicate to cloud services (e.g. AWS) has a Python side and an Editor/C++ side.   The following describes what classes do.

## Python side
**fleet_bridge.py**. The 'main' of the fleet bridge: 
  * entry point is start_servers() that creates a FleetBridge.
  * FleetBridge then uses fleet_bridge_http to handle http requests, fleet_bridge_ws to act as a websocket_service, fleet_bridge_logging to send logs via fleet_bridge_ws

**fleet_bridge_http.py**.  Requests are processed by fleet_bridge_http.py:
  * it has a global has called initialized backend
  * it has a global logging_handler
  * it will process the first two parameters of a request and load or reload the backend as required
  * Two classes:
    * The HTTPRequestHandler derives from BaseHTTRequestHandler to do_POST and other requests 

**fleet_bridge_ws.py**:
  * allows a single connection to receive asyncrhonous messages. disconnection will shut it down
	* deals with the derpy asycio_coroutines provided by the 'websockets' module ie the call to asyncio_run_coroutine_threadsafe
	* dead code - the lock
  * entry points are start_thread and jointhread.
	  * start thread starts websocket main that serves and waits for close
	   * join_thread runs a coroutine to close the thread withch will trigger the asyncio to finish running, and then joins the thread 
	* Websocket Algorithm:
	  * main calls serve and wait_for_first with a handler this will close if it receives anything on the websocket otherwise 'send on websocket' will take json_string and send them to the connected sockets
	 if any connector disconnects, the whole thing shuts down

**fleet_bridge_logging.py** :
	* two main entry points stat_thread and join_thread
  * Algorithm:
	  * installs itself as a queued logging handler, if it receives a log message it sends the log across the websocket.

**aws_backend.py**: 
  * GameLiftStarter/Content/Python has
    * aws_backend.py - this has both a command line and function call interfaces into the AWSBackendClass

## Editor/C++ side
  * FleetBridge.cpp 
	* starts the fleet_bridge python side by calling fleet_bridge_start_servers
	* has void SubmitRequest(const FString& Request, const FString& Verb, const FFleetRequestCompleteDelegate &);
	* bool IsRequestOutstanding(FString* RequestOut);
	* IFleet::FNewLogDelegate& OnNewLog() { return NewLogDelegate;  }


## How The Backend Gets Identified (e.g. aws_backend)
FleeteratorGameLiftStarterEditor.cpp:
* Defines a GameLiftStarterParams which returns "aws_backend/1" for GetBackendPathPart.
FleetBridge.cpp:
* uses this string to prefix all reqeusts.  ie see variable HttpPrefixWithBackend in FleetBridge.cpp
fleet_bridge_http.py:
* Notice that in fleet_bridge_http.py - every time a request is received the backend name and id is looked at in check_backend that will invoke
importlib.import_module if it hasn't seen that backend yet.  or it will reload the backend!  I think this is to make it easier to iterate on.

