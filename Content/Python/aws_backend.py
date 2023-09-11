#!/usr/bin/env python

# Copyright 2022 Sean Payne
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import sys
import os
import argparse
import time
import logging
import json
import zipfile
import io
import subprocess
import re
import uuid
from pathlib import Path
import webbrowser
import boto3
from botocore.exceptions import ClientError,ProfileNotFound

OK_STRING="...ok"

fleet_description = \
    '<Header>GameLift Starter Script</>\n' \
    '<a id=\"source\" href=\"[FILE_PATH]" style=\"Hyperlink\">aws_backend.py</>\n\n' \
    'This script allows you to check, install and tear down the backend design described in the video series <a id=\"browser\" href=\"https://www.youtube.com/playlist?list=PLuGWzrvNze7LEn4db8h3Jl325-asqqgP2\" style=\"Hyperlink\">Building Games on AWS: GameLift & UE4</>, ' 
    

fleet_description = fleet_description.replace("[FILE_PATH]", __file__)


fleet_metadata_json = {
"Overall Result": "True",
"Details" : {
	"Fleet Type": "GameLiftBasic",
	"Fleet Description": fleet_description,

	"Components": [

        {
		"Name": "Dedicated Server is Packaged",
		"Description": "\n"
        "Before you can deploy, you need to prepare your client and server binaries.  The detailed steps are described in references at the bottom.\n\n"
        "Your dedicated server needs to:\n"
        "   \u2022 Be linked against the GameLift SDK\n"
        "   \u2022 Have handlers for:\n"
        "      \u2022 Activation requests\n"
        "      \u2022 Start game session requests\n"
        "      \u2022 OnTerminate requests\n"
        "      \u2022 OnHealthCheck requests\n"
        "      \u2022 And marks itself as ready to receive game sessions\n"
        "   \u2022 Be built using the ServerTarget\n"
        "   \u2022 Have maps and modes for the offline and online maps\n"
        "   \u2022 Have a main menu to handle login (client side only)\n"
        "   \u2022 Include an install.bat that is used to run UEPrereqSetup\n"
        "\n"
        "The check action checks that install.bat and the executable is in the server build root folder.\n"
        "\n"
        "References:\n"
        '  My notes: <a id=\"browser\" href=\"https://github.com/spayne/unreal-multiplayer-server-in-aws/blob/main/doc/ue_project_setup.md" style=\"Hyperlink\">ue_project_setup</>\n'
        '  AWS video series:\n'
        '    <a id=\"browser\" href=\"https://youtu.be/cUcTJjqSCos" style=\"Hyperlink\">Episode 2: Build the UE Game Client maps and UE server target.</>\n'
        '    <a id=\"browser\" href=\"https://www.youtube.com/watch?v=Sl_i6YIgQqg" style=\"Hyperlink\">Episode 3: Integrate GameLiftServer SDK with UE4.</>\n'
        ,

		"Requests": [
            { "Name": "Check", "RequestPath": "/deployment/packaged_build/check" }
         ]
		},

        {
		"Name": "Server is Uploaded to GameLift",
		"Description": "\n"
        "Once you have a server build, you need to upload it to GameLift\n"
        "\n"
        "Button actions:\n"
        " \u2022 Check: Ensure that there is an uploaded build with the expected name\n"
        " \u2022 Upload: Upload the local build to GameLift\n"
        " \u2022 Delete: Deletes all remote builds with the expected name\n"
        " \u2022 AWS: Opens the AWS GameLift Console\n",
		"Requests": [
            { "Name": "Check", "RequestPath": "/deployment/uploaded_build/check" },
            { "Name": "Upload", "RequestPath": "/deployment/uploaded_build/create" },
            { "Name": "Delete", "RequestPath": "/deployment/uploaded_build/delete" },
            { "Name": "AWS", "RequestPath": "/deployment/uploaded_build/browse" },
        ]
        },

        {
		"Name": "Fleet is Active",
		"Description": "\n"
        "The uploaded build needs to launched as a fleet."
        "This fleet will be launched for the region you have configured in the plugin settings.\n\n"
        "Note that launching the fleet is time consuming (~20min) to finish.  However you are able to execute the rest "
        "of the tasks while this fleet is launching.\n"
        "\n"
        "Button actions:\n"
        " \u2022 Check: Is there a fleet with the expected name AND in the ACTIVE state\n"
        " \u2022 Launch: Creates the fleet.  Takes awhile, see above.\n"
        " \u2022 Delete: Requests deletion of the fleet.  Note that GameLift won't allow deletion until the fleet is ACTIVE\n"
        " \u2022 AWS: Opens the AWS fleet console\n"
        ,
		"Requests": [
            { "Name": "Check", "RequestPath": "/deployment/fleet/check" },
            { "Name": "Launch", "RequestPath": "/deployment/fleet/create" },
            { "Name": "Delete", "RequestPath": "/deployment/fleet/delete" },
            { "Name": "AWS", "RequestPath": "/deployment/fleet/browse" },
        ]
        },

        {
		"Name": "Cognito User Pool Created",
		"Description": "\n"
        "To authenticate logins, this script uses the AWS Cognito service.\n"
        "\n"
        "Button actions:\n"
        " \u2022 Check: Is there a user pool with the expected name?\n"
        " \u2022 Create: Creates the user pool and creates 32 test accounts:\n"
        "                    user1/pass12\n"
        "                    user2/pass12 etc...\n"
        " \u2022 Delete: Deletes the user pool \n"
        " \u2022 AWS: Opens the AWS Cognito home page\n",
		"Requests": [
            { "Name": "Check", "RequestPath": "/deployment/user_pool/check" },
            { "Name": "Create", "RequestPath": "/deployment/user_pool/create" },
            { "Name": "Delete", "RequestPath": "/deployment/user_pool/delete" },
            { "Name": "AWS", "RequestPath": "/deployment/user_pool/browse" },
        ]
        },

        {
		"Name": "Lambdas Installed",
		"Description": "\n"
        "Two lambda scripts are uploaded to AWS:\n"
        "  \u2022 A login script to handle authentication\n"
        "  \u2022 A start session script that gives the requestor a server ip to connect to\n"
        "\n"
        "This step *requires* a fleet id and a user pool id - so make sure you have started those before starting this step"
        "\n\n"
        "Button actions:\n"
        " \u2022 Check: Are both lambda scripts uploaded?\n"
        " \u2022 Create: Uses the fleet ids and the cognito app ids to install a login script and a start session script\n"
        " \u2022 Delete: Deletes the two lambdas\n"
        " \u2022 AWS: Opens the AWS Lambda dashboard\n",
		"Requests": [
            { "Name": "Check", "RequestPath": "/deployment/lambdas/check" },
            { "Name": "Create", "RequestPath": "/deployment/lambdas/create" },
            { "Name": "Delete", "RequestPath": "/deployment/lambdas/delete" },
            { "Name": "AWS", "RequestPath": "/deployment/lambdas/browse" },
        ]
        },

        {
		"Name": "Rest APIs Installed",
		"Description": "\n"
        "Sets up REST APIS in the AWS API Gateway.  This is how the clients communicate to the backend.\n"
        "\n"
        "This step requires that all other steps have been completed. ie it will fail if it can't find the lambdas to associate with the APIs"
        "\n\n"
        "Button actions:\n"
        " \u2022 Check: Has the API been added to API Gateway?\n"
        " \u2022 Create:\n"
        "         \u2022 Creates the API:\n"
        "         \u2022 Sets up an Authorizer\n"
        "         \u2022 Creates a POST login resource\n"
        "         \u2022 Creates a GET start session resource\n"
        "         \u2022 Deploys the API to a test stage\n"
        " \u2022 Delete: Deletes the rest api\n"
        " \u2022 AWS: Opens the AWS API Gateway dashboard\n",
		"Requests": [
            { "Name": "Check", "RequestPath": "/deployment/rest_api/check" },
            { "Name": "Create", "RequestPath": "/deployment/rest_api/create" },
            { "Name": "Delete", "RequestPath": "/deployment/rest_api/delete" },
            { "Name": "AWS", "RequestPath": "/deployment/rest_api/browse" },
        ]
        },
	]
}
    }

can_cognito_json = {
            "Version": "2012-10-17",
            "Statement": [
            {
                "Sid": "VisualEditor0",
                "Effect": "Allow",
                "Action": "cognito-idp:InitiateAuth",
                "Resource": "*"
            }
            ]
        }

can_execute_lambda_policy_json = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }

can_gamelift_session_control_policy_json = {
            "Version": "2012-10-17",
            "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "gamelift:CreateGameSession",
                    "gamelift:CreatePlayerSession",
                    "gamelift:CreatePlayerSessions",
                    "gamelift:DescribeGameSessionDetails",
                    "gamelift:DescribeGameSessions",
                    "gamelift:ListFleets",
                    "gamelift:ListGameServerGroups",
                    "gamelift:SearchGameSessions"
                ],
                "Resource": "*"
            }
        ]
    }

aws_logger = logging.getLogger(__name__)

log_debug = aws_logger.debug    # detailed information
log_info = aws_logger.info # confirmation that things are working
log_warn = aws_logger.warn # something unexpected but still working
log_error = aws_logger.error    # something failed
log_exception = aws_logger.exception    # level is ERROR. log the exception too
log_critical = aws_logger.critical      # program failed

def PopOneOrBadRequest(queue):
    try:
        item1 = queue.popleft()
    except IndexError:
        raise(BadRequest)
    return item1


def PopTwoOrBadRequest(queue):
    try:
        item1 = queue.popleft()
        item2 = queue.popleft()
    except IndexError:
        raise(BadRequest)
    return item1,item2


def handle_request(part_queue, query_dict, verb):
    resource = PopOneOrBadRequest(part_queue)
    try: 
        default_config=make_backend_config_from_dict(query_dict)
    except:
        log_exception("handle_request")
        return 200, {"Overall Result": "Invalid Settings"}
    if resource == "metadata":
        return 200, fleet_metadata_json
    elif resource == "config":
        return 200, default_config
    elif resource == "deployment":
        subresource,op = PopTwoOrBadRequest(part_queue)
        a = AwsBackend(default_config)
        method_name = '_'.join([op, subresource])  # make something like 'check_uploaded_build'
        try: 
            result = getattr(a, method_name)(default_config)
        except:
            print(f"exception calling method {method_name}")
            raise 
        time.sleep(0.5) # give websocket messages time to have been processed before closing socket
        return 200, {"Overall Result": str(result)}
    else:
        raise BadResource


class AwsBackend:
    def __init__(self, backend_config):
        try:
            self.session = boto3.Session(
                profile_name=backend_config["profile_name"],
                region_name=backend_config["region_name"])
        except ProfileNotFound:
            log_error(f'AWSProfile {backend_config["profile_name"]} could not be found.  Check your Game Lift Starter Plugin settings')
            return
        except: 
            log_exception("boto3.Session")

        try:
            self.iam_client = self.session.client('iam')
            self.gamelift_client = self.session.client('gamelift')
            self.cognitoidp_client = self.session.client('cognito-idp')
            self.lambda_client = self.session.client('lambda')
            self.apigateway_client = self.session.client('apigateway')
            self.sts_client = self.session.client('sts')
        except:
            log_exception("")

    def __del__(self):
        #close services to avoid unclosed SSL warning logs
        # ref: https://github.com/boto/boto3/issues/454#issuecomment-1150557124
        try:
            self.iam_client.close()
            self.gamelift_client.close()
            self.cognitoidp_client.close()
            self.lambda_client.close()
            self.apigateway_client.close()
            self.sts_client.close()
        except:
            pass

    def log_missing_dependency(self, msg):
        log_info(" Missing: " + msg)

    def check_packaged_build(self, backend_config):
        log_info("check_packaged_build()")

        server_package_root = backend_config["server_package_root"]
        package_root = Path(server_package_root)
        ret = True
        log_info(f"checking server build root \"{server_package_root}\" directory exists")
        if package_root.is_dir():
            log_info(OK_STRING)
        else:
            log_info('FAIL: Directory Missing.  Check the Server Build Root value in the Plugin settings')
            ret = False
        log_info(f"checking install.bat exists in \"{server_package_root}\"")
        q = package_root / 'install.bat'
        if q.is_file():
            log_info(OK_STRING)
        else:
            log_info('FAIL: File Missing')
            ret = False

        fleet_launch_path = backend_config["fleet_launch_path"]
        log_info(f"checking the fleet launch_path: {fleet_launch_path}")
        match = re.match("[cC]:/game/(.*)", fleet_launch_path)
        if match:
            log_info(OK_STRING)
        else:
            log_info('FAIL: the launch path should have a "c:/game" prefix.  e.g. something like c:/game/quickstart4/Binaries/Win64/quickstart4Server.exe')
            ret = False

        # check the exe file in the launch path is where we expect it to be in the package root
        fleet_launch_suffix = match.group(1) # e.g. quickstart4/Binaries/Win64/quickstart4Server.exe
        packaged_exe_path = package_root / fleet_launch_suffix
        packaged_exe_path_str = str(packaged_exe_path)
        log_info(f"checking the corresponding packaged exe exists: {packaged_exe_path_str}")
        packaged_exe_exists = False
        if packaged_exe_path.is_file():
            log_info(OK_STRING)
            packaged_exe_exists = True
        else:
            log_info(f'FAIL: {packaged_exe_path_str} Missing')
            ret = False
    
        # see if the most recent built version of the server matches 
        project_root_string = backend_config["project_root"]
        project_root = Path(project_root_string)

        if packaged_exe_exists:
            log_info("checking packaged exe date")
            match = re.match("[cC]:/game/([^/]*)/(.*)", fleet_launch_path)
            if (match):
                project_exe_path = project_root / match.group(2)
                project_exe_path_str = str(project_exe_path)
                project_exe_time = os.path.getmtime(project_exe_path_str)
                package_exe_time = os.path.getmtime(packaged_exe_path_str)
                if (package_exe_time < project_exe_time ):
                    log_warn(f"warning - package exe is older than project exe {project_exe_path_str}")
                    log_warn(f"you may need to repackage the server target")
                elif (package_exe_time == project_exe_time ):
                    log_info(f"ok...package exe is same date as project exe")
                else:
                    log_info(f"ok...weird but ok. package exe is older than project exe")

        return ret


    def _lookup_build_id(self, uploaded_server_package_name):
        list_uploaded_builds_response = self.gamelift_client.list_builds()
        uploaded_builds = list_uploaded_builds_response["Builds"]
        for uploaded_build in uploaded_builds:
            if uploaded_build["Name"] == uploaded_server_package_name:
                return uploaded_build["BuildId"]
        return None

    # return true if there is a uploaded_build with the expected name
    def check_uploaded_build(self, backend_config):
        log_info("check_uploaded_build()")
        uploaded_build_id = self._lookup_build_id(backend_config["server_package_name"])
        if uploaded_build_id is None:
            self.log_missing_dependency('uploaded_build_id')
            log_info(f'...no builds named {backend_config["server_package_name"]}')
            return False
        else:
            log_info(f'found remote build id {uploaded_build_id} with name {backend_config["server_package_name"]}')
            log_info(OK_STRING)
            return True

    def create_uploaded_build(self, backend_config):
        log_info("create_uploaded_build()")
        log_info(f'uploading build from path: {backend_config["server_package_root"]}')

        # TODO: the following subprocess should be replaced with a boto3 friendly mechanism
        command_list = ["aws",
                    "gamelift", "upload-build",
                    "--operating-system", backend_config["server_package_os"],
                    "--build-root", backend_config["server_package_root"],
                    "--name", backend_config["server_package_name"],
                    "--build-version", backend_config["server_package_version"],
                    "--region", backend_config["region_name"],
                    "--profile", backend_config["profile_name"],
                    "--no-cli-pager"]
        log_info(' '.join(command_list))

        #completed_process = subprocess.run(command_list, capture_output=True)
        last_line = None
        si = subprocess.STARTUPINFO()
        si.dwFlags = subprocess.SW_HIDE 
        p = subprocess.Popen(command_list, 
                startupinfo=si,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0, text=True
            )
        with p.stdout:
            for line in iter(p.stdout.readline, b''):
                if len(line) == 0:
                    break
                last_line = line.rstrip()
                log_info(last_line)
        log_info("done")
        
        match = re.search(
            "Build ID: (.*)$",
            last_line) # line.decode('utf-8'))

        if match:
            uploaded_build_id = match.group(1)
            uploaded_build_id = uploaded_build_id.rstrip()
            log_info(f"successfully uploaded build ID: {uploaded_build_id}")
        else:
            log_error("failed")
            log_error(completed_process.stderr.decode('utf-8'))

    def delete_uploaded_build(self, backend_config):
        log_info("delete_uploaded_build()")
        uploaded_build_id = self._lookup_build_id(backend_config["server_package_name"])
        while uploaded_build_id:
            log_info(f"deleting uploaded_build {uploaded_build_id}")
            self.gamelift_client.delete_build(BuildId=uploaded_build_id)
            uploaded_build_id = self._lookup_build_id(backend_config["server_package_name"])
        return True
        
    def browse_uploaded_build(self, backend_config):
        url = f'https://{backend_config["region_name"]}.console.aws.amazon.com/gamelift/builds'
        log_info(f"url {url}")
        webbrowser.open(url)
        return True

    def _lookup_fleet_id(self, fleet_name):
        response = self.gamelift_client.describe_fleet_attributes() # No FleetID -> return all fleets
        fleet_attributes = response["FleetAttributes"]
        for fleet in fleet_attributes:
            if fleet["Name"] == fleet_name:
                fleet_id = fleet["FleetId"]
                return fleet_id
        return None

    def _lookup_fleet_status(self, fleet_id):
        response = self.gamelift_client.describe_fleet_attributes(FleetIds=[fleet_id]) # No FleetID -> return all fleets
        fleet_attributes = response["FleetAttributes"][0]
        log_info(fleet_attributes)
        return fleet_attributes["Status"]

    def check_fleet(self, backend_config):
        log_info("check_fleet()")
        fleet_id = self._lookup_fleet_id(backend_config["fleet_name"])
        ret = True
        if fleet_id is None:
            log_info(f"fleet not ready: fleet {backend_config['fleet_name']} not found")
            ret = False
        else:
            log_info(f"found fleet {backend_config['fleet_name']}")
            log_info(fleet_id)
            log_info(OK_STRING)

        if ret == True:
            log_info("checking fleet status is ACTIVE")
            status = self._lookup_fleet_status(fleet_id)
            if status == "ACTIVE":
                log_info(OK_STRING)
            else:
                log_info(f"fleet not ready: fleet status is {status}")
                ret = False
        return ret

    def create_fleet(self, backend_config):
        log_info("create_fleet()")
        uploaded_build_id = self._lookup_build_id(backend_config["server_package_name"])
        ret = True

        # handle the case where the build is so new, that it isn't not be ready to be used in a fleet
        log_info("checking we have a build")
        if uploaded_build_id:
            describe_build_resp = self.gamelift_client.describe_build(BuildId=uploaded_build_id)
            while describe_build_resp["Build"]["Status"] != "READY":
                log_info("waiting for uploaded build to be ready\n")
                time.sleep(1)
                describe_build_resp = self.gamelift_client.describe_build(
                    BuildId=uploaded_build_id)

            try:
                create_fleet_resp = self.gamelift_client.create_fleet(
                    Name=backend_config["fleet_name"],
                    BuildId=uploaded_build_id,
                    ServerLaunchPath=backend_config["fleet_launch_path"],
                    ServerLaunchParameters="-WithGameLift",
                    EC2InstanceType=backend_config["fleet_ec2_instance_type"],
                    FleetType="ON_DEMAND",
                    EC2InboundPermissions=[
                    {
                        'FromPort': 7777,
                        'ToPort': 7777,
                        'Protocol': 'UDP',
                        'IpRange': '0.0.0.0/0'}])
            except self.gamelift_client.exceptions.LimitExceededException as e:
                ret = False
                log_error(e)
                log_error(' * if the limit is the instance types: then try again later; try a different region; or try specifying a different instance type (e.g. use --fleet_ec2_instance_type)')
                log_error(' * if limit is fleet limit: delete the existing fleet.')
        else:
            ret = False
            log_error(f'could not find uploaded_build: {backend_config["server_package_name"]}')

        return ret

    def delete_fleet(self, backend_config):
        log_info("delete_fleet()")
        fleet_id = self._lookup_fleet_id(backend_config["fleet_name"])
        ret = True
        if fleet_id:
            try:
                log_info(f"deleting fleet {fleet_id}")
                self.gamelift_client.delete_fleet(FleetId=fleet_id)
            except ClientError as e:
                ret = False
                log_exception(e)
            except InvalidRequest as e:
                ret = False
                log_exception(e)
        return ret

    def browse_fleet(self, backend_config):
        log_info("browse_fleet()")
        url = f'https://{backend_config["region_name"]}.console.aws.amazon.com/gamelift/fleets'
        log_info(f"url {url}")
        webbrowser.open(url)
        return True

    def _lookup_user_pool_id(self, pool_name):
        response = self.cognitoidp_client.list_user_pools(MaxResults=60)
        for pool in response["UserPools"]:
            if pool["Name"] == pool_name:
                pool_id = pool["Id"]
                return pool_id
        return None

    def _lookup_user_pool_arn(self,pool_name):
        pool_id = self._lookup_user_pool_id(pool_name)
        response = self.cognitoidp_client.describe_user_pool(UserPoolId=pool_id)
        arn = response["UserPool"]["Arn"]
        return arn

    def _lookup_user_pool_client_id(self, pool_name, client_name):
        pool_id = self._lookup_user_pool_id(pool_name)
        if pool_id:
            response = self.cognitoidp_client.list_user_pool_clients(
                UserPoolId=pool_id,
                MaxResults=60)
            for client in response["UserPoolClients"]:
                if client["ClientName"] == client_name:
                    client_id = client["ClientId"]
                    return client_id
        return None

    def check_user_pool(self, backend_config):
        log_info("check_user_pool()")
        ret = True
        pool_id = self._lookup_user_pool_id(backend_config["user_pool_name"])
        if pool_id is None:
            log_info(f'not ready: no pool id found for {backend_config["user_pool_name"]}')
            ret = False
        else:
            log_info(f'found: pool_id: {pool_id} found for {backend_config["user_pool_name"]}')
            log_info(OK_STRING)
        return ret

    def create_user_pool(self, backend_config):
        log_info("create_user_pool()")

        if self._lookup_user_pool_id(backend_config["user_pool_name"]):
            log_warn("not creating - user pool already exists\n")
            return

        create_user_pool_resp = self.cognitoidp_client.create_user_pool(
            PoolName=backend_config["user_pool_name"],
            Policies={
                "PasswordPolicy": {
                    "MinimumLength": 6,
                    "RequireUppercase": False,
                    "RequireLowercase": False,
                    "RequireNumbers": False,
                    "RequireSymbols": False
                }
            },
            Schema=[{"Name": "email",
                 "AttributeDataType": "String",
                 "DeveloperOnlyAttribute": False,
                 "Mutable": True,
                 "Required": True,
                 "StringAttributeConstraints": {
                     "MinLength": "0",
                     "MaxLength": "2048"
                 }}]
        )
        user_pool_id = create_user_pool_resp["UserPool"]["Id"]

        log_info("creating cognito app client")
        # ref: https://youtu.be/EfIuC5-wdeo?t=137
        # uncheck generate client secret
        # just using ALLOW_USER_PASSWORD_AUTH.  API also wants: "ALLOW_REFRESH_TOKEN_AUTH"
        #
        # ref https://youtu.be/EfIuC5-wdeo?t=172
        # Enabled Identity Providers: Cognito User Pools
        # Callback and Signout URLs: Use AWS home page
        # implicit grant,
        # email and openid OAuth scopes
        redirect_uri = "https://aws.amazon.com"
        create_user_pool_client_resp = self.cognitoidp_client.create_user_pool_client(
            UserPoolId=user_pool_id,
            ClientName=backend_config["user_pool_login_client_name"],
            GenerateSecret=False,
            ExplicitAuthFlows=[
                "ALLOW_USER_PASSWORD_AUTH",
                "ALLOW_REFRESH_TOKEN_AUTH"],
            SupportedIdentityProviders=["COGNITO"],
            CallbackURLs=[redirect_uri],
            LogoutURLs=[redirect_uri],
            AllowedOAuthFlows=["implicit"],
            AllowedOAuthFlowsUserPoolClient=True,
            AllowedOAuthScopes=[
                "email",
                "openid"],
        )
        log_debug(f"create_user_pool_client_resp {create_user_pool_client_resp}")

        update_user_pool_resp = self.cognitoidp_client.update_user_pool(
            UserPoolId=user_pool_id,
            AutoVerifiedAttributes=["email"])
        log_debug(f"update_user_pool_resp {update_user_pool_resp}")

        log_info("creating cognito user pool domain")
        # go to App client settings, setup the callback URLs and hosted UI
        subdomain = backend_config["user_pool_subdomain_prefix"]
        create_user_pool_resp = self.cognitoidp_client.create_user_pool_domain(
            Domain=subdomain,
            UserPoolId=user_pool_id)

        log_info("users can create new accounts using the ui at:")
        login_url = f'https://{subdomain}.auth.{backend_config["region_name"]}.amazoncognito.com/'
        login_url = login_url + \
            f'login?client_id={create_user_pool_client_resp["UserPoolClient"]["ClientId"]}'
        login_url = login_url + \
            f'&response_type=Token&scope=email+openid&redirect_uri={redirect_uri}'
        log_info(login_url)

        log_info("creating test users")
        for index in range(32):
            user_name = 'user' + str(index)
            self.cognitoidp_client.admin_create_user(
                UserPoolId=user_pool_id,
                Username=user_name,
                UserAttributes=[
                    {"Name": "email", "Value": "test@test.com"}
                ],
                TemporaryPassword="test12",
                MessageAction='SUPPRESS'
            )
            self.cognitoidp_client.admin_set_user_password(
                UserPoolId=user_pool_id,
                Username=user_name,
                Password="test12",
                Permanent=True
            )

    def delete_user_pool(self, backend_config):
        log_info('delete_user_pool()')
        pool_id = self._lookup_user_pool_id(backend_config["user_pool_name"])
        if pool_id:
            response = self.cognitoidp_client.describe_user_pool(UserPoolId=pool_id)
            if "Domain" in response["UserPool"]:
                pool_domain = response["UserPool"]["Domain"]
                log_info(f"deleting user_pool domain {pool_domain}")
                response = self.cognitoidp_client.delete_user_pool_domain(
                    Domain=pool_domain, UserPoolId=pool_id)
            response = self.cognitoidp_client.delete_user_pool(UserPoolId=pool_id)

    def browse_user_pool(self, backend_config):
        log_info("browse_user_pool()")
        url = f'https://{backend_config["region_name"]}.console.aws.amazon.com/cognito/home'
        log_info(f"url {url}")
        webbrowser.open(url)
        return True

    def _lookup_lambda_function_arn(self, lambda_name):
        try:
            get_function_resp = self.lambda_client.get_function(
                FunctionName=lambda_name)
            lambda_arn = get_function_resp["Configuration"]["FunctionArn"]
            return lambda_arn
        except ClientError:
            return None

    def _lookup_role_arn(self, role_name):
        try:
            response = self.iam_client.get_role(RoleName=role_name)
            role_arn = response["Role"]["Arn"]
            return role_arn
        except ClientError:
            return None

    #
    # for details about assume_role_policy, see ref https://hands-on.cloud/working-with-aws-lambda-in-python-using-boto3/
    #
    def _create_lambda_role(
        self,
        role_name,
        assume_role_policy,
        other_policy_name,
        other_policy_json):
        '''returns role_arn of the newly created role'''
        role_arn = self._lookup_role_arn(role_name)
        if role_arn != None:
            log_warn('role already exists arn ' + role_arn)
        else:
            log_debug('role does not exist: creating')
            response = self.iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(assume_role_policy))
            role_arn = response["Role"]["Arn"]
            log_debug(response)

        response = self.iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName=other_policy_name,
            PolicyDocument=json.dumps(other_policy_json))

        return role_arn

    def _create_lambda_function_from_file(
        self,
        function_name,
        role_arn,
        filename,
        replace_old=None,
        replace_new=None):

        with open(filename, 'r') as inputfile:
            filedata = inputfile.read()

        # apply string substitutions 
        if replace_old:
            filedata = filedata.replace(replace_old, replace_new)

        # to upload, need it to be in zip format
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as tempzip:
            tempzip.writestr('handler.py', filedata)
        zipped_code = zip_buffer.getvalue()

        log_info(f"creating {function_name} lambda")
        success = False
        for create_attempt in range(10):
            try: 
                create_function_response = self.lambda_client.create_function(
                    FunctionName=function_name,
                    Runtime="python3.9",
                    Publish=True,
                    PackageType="Zip",
                    Role=role_arn,
                    Code=dict(ZipFile=zipped_code),
                    Handler="handler.lambda_handler"
                )
                success = True
                log_debug(f"create_function_response {create_function_response}")
                break
            except ClientError as e:
                log_warn(e)
                log_warn(f"create attempt {create_attempt} failed - sometimes InvalidParameterException is returned if the role is too new - sleeping and trying again")
                time.sleep(3)
        if success:
            log_info(f"success after {create_attempt+1} attempts")


    def _create_lambda_roles_and_function(self, 
            role_name, 
            other_policy_name,
            other_policy_json,
            function_name,
            filename,
            replace_old,
            replace_new):

        # setup the role: able to lambda and able to the other policy 
        role_arn = self._create_lambda_role(
            role_name,
            can_execute_lambda_policy_json,
            other_policy_name,
            other_policy_json)

        self._create_lambda_function_from_file(
            function_name,
            role_arn,
            filename,
            replace_old,
            replace_new)

    # return the path to this script
    def _get_script_path(self):
        path = os.path.dirname(os.path.realpath(__file__))
        return path

    # assume lambda files are in the same directory as this script
    def _make_lambda_local_path(self, lambda_filename):
        p = Path(self._get_script_path())
        p = p / lambda_filename
        lambda_path = str(p)
        return lambda_path


    def check_lambdas(self, backend_config):
        log_info("check_lambdas()")
        script_path = self._get_script_path()
        ret = True
        login_arn = self._lookup_lambda_function_arn(backend_config["lambda_login_function_name"])
        if login_arn is None:
            ret = False
            log_info(" lambdas not ready: missing login lambda")
        else:
            log_info(f'found login lambda {backend_config["lambda_login_function_name"]}')
            log_info(OK_STRING)

        start_session_arn = self._lookup_lambda_function_arn(backend_config["lambda_start_session_function_name"])
        if start_session_arn is None:
            ret = False
            log_info(" lambdas not ready: missing start_session lambda")
        else:
            log_info(f'found start_session lambda {backend_config["lambda_login_function_name"]}')
            log_info(OK_STRING)

        return ret


    # create the login and startsession lambdas
    def create_lambdas(self, backend_config):
        log_info("create_lambdas()")
        # need the client id to string-replace in the login function 
        cognito_app_client_id = self._lookup_user_pool_client_id(
            backend_config["user_pool_name"],
            backend_config["user_pool_login_client_name"])

        if cognito_app_client_id is None:
            log_info("app client is not setup - check your cognito status")
            return False

        # need the fleet id to string-replace in the session function
        fleet_id = self._lookup_fleet_id(backend_config["fleet_name"])
        if fleet_id is None:
            log_info("fleet id was not found - check your fleet status")
        else:
            log_debug("got fleet_id" + fleet_id)

        self._create_lambda_roles_and_function(
            backend_config["lambda_login_role_name"],
            backend_config["lambda_login_other_policy_name"],
            can_cognito_json,
            backend_config["lambda_login_function_name"],
            self._make_lambda_local_path("GameLiftUnreal-CognitoLogin.py"),
            "USER_POOL_APP_CLIENT_ID = ''",
            "USER_POOL_APP_CLIENT_ID = \"" + cognito_app_client_id + "\"")
        
        self._create_lambda_roles_and_function(
            backend_config["lambda_start_session_role_name"],
            backend_config["lambda_start_session_other_policy_name"],
            can_gamelift_session_control_policy_json,
            backend_config["lambda_start_session_function_name"],
            self._make_lambda_local_path("GameLiftUnreal-StartGameLiftSession.py"),
            'GAMELIFT_FLEET_ID = ""',
            "GAMELIFT_FLEET_ID = \"" + fleet_id + "\"")

        return True

    def _delete_lambda(self, function_name, policy_name, role_name):
        function_arn = self._lookup_lambda_function_arn(function_name)
        if function_arn: 
            self.lambda_client.delete_function(FunctionName=function_name)
        try:
            response = self.iam_client.delete_role_policy(RoleName=role_name, PolicyName=policy_name)
        except ClientError as e:
            log_warn(e)
            pass

        role_arn = self._lookup_role_arn(role_name)
        if role_arn:
            self.iam_client.delete_role(RoleName=role_name)


    def delete_lambdas(self, backend_config):
        log_info("delete_lambdas()")
        self._delete_lambda(
            backend_config["lambda_start_session_function_name"],
            backend_config["lambda_start_session_other_policy_name"],
            backend_config["lambda_start_session_role_name"])
        self._delete_lambda(
            backend_config["lambda_login_function_name"],
            backend_config["lambda_login_other_policy_name"],
            backend_config["lambda_login_role_name"])
        return True

    def browse_lambdas(self, backend_config):
        log_info("browse_lambdas()")
        url = f'https://{backend_config["region_name"]}.console.aws.amazon.com/lambda/home'
        log_info(f"url {url}")
        webbrowser.open(url)
        return True

    # create the resource for the API gateway and bind it to the corresponding lambda
    def _create_rest_resource(
        self,
        rest_api_id,
        apigateway_client, path_part, http_method,
        account_id, lambda_function_arn,
        authorizer_id):

        # get Root ID
        try:
            response = self.apigateway_client.get_resources(restApiId=rest_api_id)
            root_id = next(item['id']
                        for item in response['items'] if item['path'] == '/')
        except ClientError:
            log_exception(
                "Couldn't get the ID of the root resource of the REST API.")
            raise

        # create the resource under root
        try:
            response = self.apigateway_client.create_resource(
                restApiId=rest_api_id, parentId=root_id, pathPart=path_part)
            resource_id = response['id']
        except ClientError:
            log_exception("Couldn't create pathPart path for %s.", path_part)
            raise

        # create the method for the resource
        # ref: https://youtu.be/EfIuC5-wdeo?t=1095
        #      * shows setting the Authorizor on the method
        if authorizer_id:
            authorization_type = 'COGNITO_USER_POOLS'
        else:
            authorization_type = 'NONE'
            authorizer_id = ''
    
        try:
            self.apigateway_client.put_method(
                restApiId=rest_api_id,
                resourceId=resource_id,
                httpMethod=http_method,
                authorizationType=authorization_type,
                authorizerId=authorizer_id)
        except ClientError:
            log_exception("Couldn't create a method for the base resource.")
            raise

        # bind the method to the lambda
        lambda_uri = \
            f'arn:aws:apigateway:{self.apigateway_client.meta.region_name}:' \
            f'lambda:path/2015-03-31/functions/{lambda_function_arn}/invocations'
        log_debug(lambda_uri)  
        try:
            # NOTE: You must specify 'POST' for integrationHttpMethod or this will
            # not work.
            self.apigateway_client.put_integration(
                restApiId=rest_api_id,
                resourceId=resource_id,
                httpMethod=http_method,
                type='AWS',
                integrationHttpMethod='POST',
                uri=lambda_uri)
        except ClientError:
            log_exception(
                "Couldn't set function %s as integration destination.",
                lambda_function_arn)
            raise

        # add permission so the method is able to invoke the lambda
        source_arn = \
            f'arn:aws:execute-api:{apigateway_client.meta.region_name}:' \
            f'{account_id}:{rest_api_id}/*/*/{path_part}'
        try:
            self.lambda_client.add_permission(
                FunctionName=lambda_function_arn,
                StatementId=uuid.uuid4().hex,  # todo do I need to clean these up
                Action='lambda:InvokeFunction', Principal='apigateway.amazonaws.com',
                SourceArn=source_arn)
        except ClientError:
            log_exception(
                "Couldn't add permission to let Amazon API Gateway invoke %s.",
                lambda_function_arn)
            raise

        # fill out response details
        self.apigateway_client.put_integration_response(
            restApiId=rest_api_id,
            resourceId=resource_id,
            httpMethod=http_method,
            statusCode="200",
            selectionPattern=".*"
        )
    
        self.apigateway_client.put_method_response(
            restApiId=rest_api_id,
            resourceId=resource_id,
            httpMethod=http_method,
            statusCode="200")

    def _create_login_resource(self, backend_config, rest_api_id, authorizer_id):
        account_id = self.sts_client.get_caller_identity()["Account"]
        lambda_name = backend_config["lambda_login_function_name"]
        lambda_arn = self._lookup_lambda_function_arn(lambda_name)
        self._create_rest_resource(
            rest_api_id,
            self.apigateway_client,
            backend_config["rest_api_login_path_part"],
            'POST',
            account_id,
            lambda_arn,
            authorizer_id)

    # the gateway resource to invoke the session labmda
    def _create_start_session_resource(self, backend_config, rest_api_id, authorizer_id):
        account_id = self.sts_client.get_caller_identity()["Account"]
        lambda_name = backend_config["lambda_start_session_function_name"]
        lambda_arn = self._lookup_lambda_function_arn(lambda_name)

        self._create_rest_resource(
            rest_api_id,
            self.apigateway_client,
            backend_config["rest_api_start_session_path_part"],
            'GET',
            account_id,
            lambda_arn,
            authorizer_id)

    def _lookup_rest_api_id(self, rest_api_name):
        response = self.apigateway_client.get_rest_apis()
        rest_apis = response["items"]
        for rest_api in rest_apis:
            if rest_api_name == rest_api["name"]:
                rest_api_id = rest_api["id"]
                return rest_api_id
        return None

    def _print_helpful_rest_info(self, backend_config, rest_api_id):
        invoke_url = f'https://{rest_api_id}.execute-api.{backend_config["region_name"]}.amazonaws.com/{backend_config["rest_api_stage_name"]}'
        log_info('invoke_url:')
        log_info(invoke_url)
        log_info('(for command line testing) to login try:')
        login_curl = 'curl -X POST -d "{\\"username\\":\\"user0\\", \\"password\\":\\"test12\\"}" ' + \
            invoke_url + '/login'
        log_info(login_curl)
        log_info("")
        log_info('(for command line testing) to start a session,  use the [IdToken] from the above login')
        start_curl = 'curl -X GET -H "Authorization: Bearer [IdToken]\" ' + \
            invoke_url + '/startsession'
        log_info(start_curl)


    def check_rest_api(self, backend_config):
        log_info(f'check_rest_api()')
        log_info(f'checking for rest_api: {backend_config["rest_api_name"]}')
        ret= True
        api_id = self._lookup_rest_api_id(backend_config["rest_api_name"]);
        if api_id is None:
            log_info(f'not ready: {backend_config["rest_api_name"]} not found');
            ret = False
        else:
            log_info(f"found api_id {api_id}");
            self._print_helpful_rest_info(backend_config, api_id)
            log_info(OK_STRING);
        return ret


    # create_rest_api: create the api, authorizer and methods
    #
    # ref: https://youtu.be/EfIuC5-wdeo?t=822
    #      Amazon GameLift-UE4 Episode 6: Amazon Cognito and API Gateway
    #        * has some details on configuring lambda invocation using boto3
    #
    def create_rest_api(self, backend_config):
        log_info("create_rest_api()")
        if self._lookup_rest_api_id(backend_config["rest_api_name"]):
            log_info("not creating rest api because it already exists")
            return

        # create the rest API
        try:
            response = self.apigateway_client.create_rest_api(
                name=backend_config["rest_api_name"])
            rest_api_id = response['id']
        except ClientError:
            log_exception(
                f'Could not create REST API {backend_config["rest_api_name"]}.')
            raise

        # create the cognito authorizer
        log_info("creating cognito authorizer")
        cognito_arn = self._lookup_user_pool_arn(backend_config["user_pool_name"])

        # ref: https://youtu.be/EfIuC5-wdeo?t=1012
        create_authorizer_response = self.apigateway_client.create_authorizer(
            restApiId=rest_api_id,
            name=backend_config["rest_api_cognito_authorizer_name"],
            type='COGNITO_USER_POOLS',
            providerARNs=[cognito_arn],
            identitySource="method.request.header.Authorization"
        )
        authorizer_id = create_authorizer_response["id"]

        # create the login and start session gateway
        log_info("creating login resource")
        log_info(backend_config)
        #def _create_login_resource(self, backend_config, rest_api_id, authorizer_id):
        self._create_login_resource(backend_config, rest_api_id, None)
        log_info("creating start session resource")
        self._create_start_session_resource(backend_config, rest_api_id, authorizer_id)

        # deploy the API to the requested stage name
        log_info(f'deploying to stage backend_config["rest_api_stage_name"]')
        try:
            create_deployment_resp = self.apigateway_client.create_deployment(
                restApiId=rest_api_id,
                stageName=backend_config["rest_api_stage_name"])
            log_debug(f"create_deployment_resp {create_deployment_resp}")
        except ClientError:
            log_exception("Couldn't deploy REST API %s.", rest_api_id)
            raise

        self._print_helpful_rest_info(self, backend_config, rest_api_id)
        
        return True

    def delete_rest_api(self, backend_config):
        log_info("delete_rest_api()")
        rest_api_id = self._lookup_rest_api_id(backend_config["rest_api_name"])
        while rest_api_id:
            self.apigateway_client.delete_rest_api(restApiId=rest_api_id)
            rest_api_id = self._lookup_rest_api_id(backend_config["rest_api_name"])
        return True


    def browse_rest_api(self, backend_config):
        log_info("browse_rest_api()")
        url = f'https://{backend_config["region_name"]}.console.aws.amazon.com/apigateway'
        log_info(f"url {url}")
        webbrowser.open(url)
        return True


def process_check_commands(backend, backend_config, commands):
    while len(commands) > 0:
        command = commands.pop(0)
        if command == "packaged_build":
            backend.check_packaged_build(backend_config)
        elif command == "uploaded_build":
            backend.check_uploaded_build(backend_config)
        elif command == "fleet":
            backend.check_fleet(backend_config)
        elif command == "user_pool":
            backend.check_user_pool(backend_config)
        elif command == "lambdas":
            backend.check_lambdas(backend_config)
        elif command == "rest_api":
            backend.check_rest_api(backend_config)
        else:
            log_warn("urecognized command" + command)


def process_create_commands(backend, backend_config, commands):
    while len(commands) > 0:
        command = commands.pop(0)
        if command == "uploaded_build":
            backend.create_uploaded_build(backend_config)
        elif command == "fleet":
            backend.create_fleet(backend_config)
        elif command == "user_pool":
            backend.create_user_pool(backend_config)
        elif command == "lambdas":
            backend.create_lambdas(backend_config)
        elif command == "rest_api":
            backend.create_rest_api(backend_config)
        else:
            log_warn("urecognized command" + command)


def process_delete_commands(backend, backend_config, commands):
    while len(commands) > 0:
        command = commands.pop(0)
        if command == "uploaded_build":
            backend.delete_uploaded_build(backend_config)
        elif command == "fleet":
            backend.delete_fleet(backend_config)
        elif command == "user_pool":
            backend.delete_user_pool(backend_config)
        elif command == "lambdas":
            backend.delete_lambdas(backend_config)
        elif command == "rest_api":
            backend.delete_rest_api(backend_config)
        else:
            log_warn("unrecognized command" + command)


def process_backend_config(backend_config):
    if len(backend_config["commands"]) > 0:
        log_info(f'using AWS profile: {backend_config["profile_name"]}')
        a = AwsBackend(backend_config)

        main_command = backend_config["commands"].pop(0)
        sub_commands = backend_config["commands"]

        if len(sub_commands) > 0 and sub_commands[0] == "all":
            sub_commands = [
                "packaged_build",
                "uploaded_build",
                "fleet",
                "user_pool",
                "lambdas",
                "rest_api"]

        if main_command == "check":
            process_check_commands(a, backend_config, sub_commands)
        elif main_command == "create":
            process_create_commands(a, backend_config, sub_commands)
        elif main_command == "delete":
            process_delete_commands(a, backend_config, sub_commands)
        else:
            log_warn(f"unrecognized_command: {main_command}")


class Formatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass


# e.g.
# 
def make_backend_config_from_dict(dict):
    args = []
    for key in dict:
        param = "--" + key + "=" + dict[key]
        args.append(param)
    return make_backend_config_from_args(args)


def verify_backend_config(backend_config):
    prefix = backend_config["prefix"]
    regex = r'^[a-z0-9][a-z0-9-]{0,31}$'
    if not re.match(regex, prefix):
        raise Exception(f"Invalid fleet prefix {prefix}.  Check your project settings to ensure you are using lowercase")

# return a dictionary that still needs to be  
def make_backend_config_from_args(argv):
    '''return a backend_config'''

    example_text = '''create examples:
       python aws_backend.py create uploaded_build
       python aws_backend.py create fleet
       python aws_backend.py create user_pool
       python aws_backend.py create lambdas
       python aws_backend.py create rest_api

delete examples:
       python aws_backend.py delete uploaded_build
       python aws_backend.py delete all

override default example:
       python aws_backend.py --prefix=potato --server_package_root=E:/unreal_projects/ue5_gamelift_plugin_test/MyProject/ServerBuild/WindowsServer --fleet_launch_path=C:/game/MyProject/Binaries/Win64/MyProjectServer.exe --profile=dave --region=us-west-2
       '''

    parser = argparse.ArgumentParser(
        description='Configure AWS Services to provide login, session and server management for dedicated UE servers',
        epilog=example_text,
        formatter_class=Formatter)
    parser.add_argument('commands', nargs='*')
    parser.add_argument('--prefix', default="test1", help="prefix used below")

    parser.add_argument(
        '--project_root',
        default="E:/unreal_projects/MyProject/",
        help="path to the .uproject folder")

    parser.add_argument(
        '--server_package_name',
        default="[prefix]-build",
        help="name associated with the build (visible in the GameLift console")
    parser.add_argument(
        '--server_package_version',
        default="build0.42",
        help="a version number")
    parser.add_argument(
        '--server_package_os',
        default="WINDOWS_2016",
        help="the os to install on the EC2 instances")
    parser.add_argument(
        '--server_package_root',
        default="E:/unreal_projects/MyProject/x64 Builds/WindowsServer",
        help="path to the server package on your local machine")

    parser.add_argument(
        '--fleet_name',
        default="[prefix]-fleet",
        help="name associated with the fleet")
    parser.add_argument(
        '--fleet_launch_path',
        default="C:/game/MyProject/Binaries/Win64/MyProjectServer.exe",
        help="the EC2 path to the server.  Must start with c:/game")

    parser.add_argument(
        '--fleet_ec2_instance_type',
        default="c5.large",
        help="what kind of EC2s to allocate.  Currently c5.large, c4.large and c3.large qualify for the GameLift free tier")

    parser.add_argument(
        '--user_pool_name',
        default="[prefix]-user-pool",
        help="pool name")
    parser.add_argument(
        '--user_pool_login_client_name',
        default="[prefix]-user-pool-login-client",
        help="pool client name")
    parser.add_argument(
        '--user_pool_subdomain_prefix',
        default="[prefix]-login",
        help="name the subdomain")
 
    parser.add_argument(
        '--lambda_login_function_name',
        default="[prefix]-lambda-login-function",
        help="name of the login lamda function")
    parser.add_argument(
        '--lambda_login_role_name',
        default="[prefix]-lambda-login-role",
        help="name of the role used by the login lamda")
    parser.add_argument(
        '--lambda_login_other_policy_name',
        default="[prefix]-lambda-login-other-policy-name",
        help="name of specific policies that lets login work (i.e. cognito policies)")

    parser.add_argument(
        '--lambda_start_session_function_name',
        default="[prefix]-lambda-start-session-function",
        help="name of the start-session lambda function")
    parser.add_argument(
        '--lambda_start_session_role_name',
        default="[prefix]-lambda-start-session-role",
        help="name of the role used by the start-session lambda")
    parser.add_argument(
        '--lambda_start_session_other_policy_name',
        default="[prefix]-lambda-start-session-other-policy-name",
        help="name of specific policies that lets start-session work (i.e. gamelift policies)")

    parser.add_argument(
        '--rest_api_name',
        default="[prefix]-rest-api",
        help="name the api")
    parser.add_argument(
        '--rest_api_stage_name',
        default="[prefix]-api-test-stage",
        help="name the stage")
    parser.add_argument(
        '--rest_api_login_path_part',
        default="login",
        help="name the suffix")
    parser.add_argument(
        '--rest_api_start_session_path_part',
        default="startsession",
        help="name the suffix")
    parser.add_argument(
        '--rest_api_cognito_authorizer_name',
        default="[prefix]-cognito-authorizer",
        help="name the authorizer")

    parser.add_argument(
        '--profile_name',
        default='sean_backend',
        help="AWS credentials to use")
    parser.add_argument('--region_name',
            default='us-west-2',
            help='AWS region')

    args = parser.parse_args(argv)

    backend_config = vars(args)

    # walk through the build config and replace [prefix] with the prefix
    # these final configuration parameters are what is used as the resource
    # names during creation and deletion.
    log_debug("Backend Configuration:")
    prefix = backend_config["prefix"]
    for key, value in backend_config.items():
        if type(value) == str:
            backend_config[key] = value.replace("[prefix]", prefix)
        log_debug(f"    {key}:{backend_config[key]}")

    verify_backend_config(backend_config)

    return backend_config

# ref: https://docs.python.org/3/howto/logging-cookbook.html#logging-to-multiple-destinations 
# python docs on how to send INFO and above to console and DEBUG, INFO and above to logfile 
def setup_logger_to_both_console_and_logfile():
    logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='aws_backend.log',
                    filemode='w')
    # define a Handler which writes INFO messages or higher to the sys.stderr
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # set a format which is simpler for console use
    console_formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
    # tell the handler to use this format
    console_handler.setFormatter(console_formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console_handler)


def logging_install_handler(logging_handler):
    if aws_logger.hasHandlers():
        for handler in aws_logger.handlers:
            aws_logger.removeHandler(handler)
    aws_logger.addHandler(logging_handler)

def logging_set_level(level):
    aws_logger.setLevel(level)

def test_sending_logs():
    log_debug("a debug log")
    log_info("an info log")
    log_info("an info log with a single double quote\"")
    log_info("an info log with a single single quote'")
    log_info("an info log with a newline\nsecond line")
    log_info("an info log with a colon :")
    log_warn("a warn log")
    log_error("a error log")
    log_critical("a critical log")

    try:
        x= 1/0
    except:
        log_exception("an exception log")


def run_main(argv):
    setup_logger_to_both_console_and_logfile()
    backend_config = make_backend_config_from_args(argv)
    process_backend_config(backend_config)


if __name__ == '__main__':
    run_main(sys.argv[1:])
