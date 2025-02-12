import logging
import os
import inspect
from socketserver import BaseRequestHandler
import sys
import json
import time
from xmlrpc.client import APPLICATION_ERROR
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
from pprint import pprint as pp
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir) 
from requests.exceptions import HTTPError, ReadTimeout
from app.xiq_logger import logger

logger = logging.getLogger('VIQ_Backup_Restore.xiq_connector')

PATH = current_dir

class APICallFailedException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class XIQ:
    def __init__(self, user_name=None, password=None, token=None):
        self.URL = "https://api.extremecloudiq.com"
        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}
        self.totalretries = 5
        if token:
            self.headers["Authorization"] = "Bearer " + token
        else:
            try:
                self.__getAccessToken(user_name, password)
            except ValueError as e:
                raise ValueError(e)
            except HTTPError as e:
               raise ValueError(e)
            except:
                log_msg = "Unknown Error: Failed to generate token for XIQ"
                logger.error(log_msg)
                raise ValueError(log_msg)
    #API CALLS
    def __get_api_call(self, url, downloadFile = False):
        try:
            response = requests.get(url, headers= self.headers)
        except HTTPError as http_err:
            logger.error(f'HTTP error occurred: {http_err} - on API {url}')
            raise APICallFailedException(f'HTTP error occurred: {http_err}') 
        if response is None:
            log_msg = "ERROR: No response received from XIQ!"
            logger.error(log_msg)
            raise APICallFailedException(log_msg)
        if response.status_code != 200:
            log_msg = f"Error - HTTP Status Code: {str(response.status_code)}"
            logger.error(f"{log_msg}")
            try:
                data = response.json()
            except json.JSONDecodeError:
                logger.warning(f"\t\t{response.text}")
            else:
                if 'error_message' in data:
                    logger.warning(f"\t\t{data['error_message']}")
                else:
                    logger.warning(f"\n\n{data}")
            raise APICallFailedException(log_msg) 
        if downloadFile:
            return response.content
        try:
            data = response.json()
        except json.JSONDecodeError:
            logger.error(f"Unable to parse json data - {url} - HTTP Status Code: {str(response.status_code)}")
            raise APICallFailedException("Unable to parse the data from json, script cannot proceed")
        return data

    def __put_api_call(self, url, payload):
        try:
            response = requests.put(url, headers= self.headers, data=payload)
        except HTTPError as http_err:
            logger.error(f'HTTP error occurred: {http_err} - on API {url}')
            raise APICallFailedException(f'HTTP error occurred: {http_err}') 
        if response is None:
            log_msg = "ERROR: No response received from XIQ!"
            logger.error(log_msg)
            raise APICallFailedException(log_msg)
        if response.status_code != 200:
            log_msg = f"Error - HTTP Status Code: {str(response.status_code)}"
            logger.error(f"{log_msg}")
            try:
                data = response.json()
            except json.JSONDecodeError:
                logger.warning(f"\t\t{response.text}")
            else:
                if 'error_message' in data:
                    logger.warning(f"\t\t{data['error_message']}")
                else:
                    logger.warning(f"{data}")
            raise APICallFailedException(log_msg) 
        try:
            data = response.json()
        except json.JSONDecodeError:
            logger.error(f"Unable to parse json data - {url} - HTTP Status Code: {str(response.status_code)}")
            raise APICallFailedException("Unable to parse the data from json, script cannot proceed")
        return data
    
    def __post_api_call(self, url, payload):
        try:
            response = requests.post(url, headers= self.headers, data=payload)
        except HTTPError as http_err:
            raise APICallFailedException(f'HTTP error occurred: {http_err} - on API {url}') 
        if response is None:
            log_msg = "ERROR: No response received from XIQ!"
            raise APICallFailedException(log_msg)
        if response.status_code == 202:
            return response.status_code
        elif response.status_code != 200 and response.status_code != 201:
            log_msg = f"Error - HTTP Status Code: {str(response.status_code)}"
            try:
                data = response.json()
            except json.JSONDecodeError:
                logger.warning(f"\t\t{response.text}")
            else:
                if 'error_message' in data:
                    log_msg.append(f"\t\t{data['error_message']}")
            raise APICallFailedException(log_msg)
        if response.text:
            try:
                data = response.json()
            except json.JSONDecodeError:
                raise APICallFailedException(f"Unable to parse the data from json - {url}, script cannot proceed - HTTP Status Code: {str(response.status_code)}")
            return data
        else:
            return response.status_code

    def __delete_api_call(self, url):
        try:
            response = requests.delete(url, headers= self.headers)
        except HTTPError as http_err:
            logger.error(f'HTTP error occurred: {http_err} - on API {url}')
            raise ValueError(f'HTTP error occurred: {http_err}') 
        if response is None:
            log_msg = "ERROR: No response received from XIQ!"
            logger.error(log_msg)
            raise APICallFailedException(log_msg)
        if response.status_code == 202:
            return response.status_code
        elif response.status_code != 200 and response.status_code != 201:
            log_msg = f"Error - HTTP Status Code: {str(response.status_code)}"
            logger.error(f"{log_msg}")
            try:
                data = response.json()
            except json.JSONDecodeError:
                logger.warning(f"\t\t{response.text}")
            else:
                if 'error_message' in data:
                    logger.warning(f"\t\t{data['error_message']}")
                    raise APICallFailedException(data['error_message'])
            raise APICallFailedException(log_msg)
        if response.text:
            try:
                data = response.json()
            except json.JSONDecodeError:
                logger.error(f"Unable to parse json data - {url} - HTTP Status Code: {str(response.status_code)}")
                raise APICallFailedException("Unable to parse the data from json, script cannot proceed")
            return data
        else:
            return response.status_code

    ## Long Run Operations
    def __post_lro_call(self,url,payload={},files={}):
        headers = self.headers
        if files:
            payload = MultipartEncoder(fields=files)
            headers["Content-Type"] = payload.content_type
            #payload = json.dumps({"importFile":None})
        #print(payload)
        #print(files)
        try:
            response = requests.post(url, headers=headers, data=payload)
        except HTTPError as http_err:
            raise APICallFailedException(f'HTTP error occurred: {http_err} - on API {url}')
        except ReadTimeout as timout_err:
            raise APICallFailedException(f'HTTP error occurred: {timout_err} - on API {url}')
        except Exception as err:
            raise APICallFailedException(f'Other error occurred: {err}: on API {url}')
        else:
            if response is None:
                log_msg = "ERROR: No response received from XIQ!"
                raise APICallFailedException(log_msg)
            if response.status_code != 202:
                raise  APICallFailedException(f"Error retrieving response from XIQ. - HTTP Status Code: {str(response.status_code)}")
            data = response.headers
            # return the URL needed to check the status and collect data for the LRO
            return data['Location']
                
    # XIQ Token
    def __getAccessToken(self, user_name, password):
        info = "get XIQ token"
        success = 0
        url = self.URL + "/login"
        payload = json.dumps({"username": user_name, "password": password})
        try:
            data = self.__post_api_call(url=url,payload=payload)
        except APICallFailedException as e:
            print(f"API to {info} failed with {e}")
            print('script is exiting...')
            raise SystemExit
        except:
            print(f"API to {info} failed with unknown API error")
        else:
            success = 1
        if success != 1:
            print("failed to get XIQ token. Cannot continue to import")
            print("exiting script...")
            raise SystemExit
        
        if "access_token" in data:
            #print("Logged in and Got access token: " + data["access_token"])
            self.headers["Authorization"] = "Bearer " + data["access_token"]
            return 0

        else:
            log_msg = "Unknown Error: Unable to gain access token for XIQ"
            logger.warning(log_msg)
            raise ValueError(log_msg)

    ## EXTERNAL FUNCTION

    # EXTERNAL ACCOUNTS
    def __getVIQInfo(self):
        info="get current VIQ name"
        url = f"{self.URL}/account/home"
        try:
            data = self.__get_api_call(url=url)
        except HTTPError as http_err:
            logger.error(f'HTTP error occurred: {http_err} - on API {url}')
            raise APICallFailedException(f'HTTP error occurred: {http_err}') 
        except:
            print(f"Failed to {info}")
            return None      
        else:
            self.viqName = data['name']
            self.viqID = data['id']        

    #ACCOUNT SWITCH
    def selectManagedAccount(self):
        self.__getVIQInfo()
        info="gather accessible external XIQ accounts"
        url = f"{self.URL}/account/external"
        try:
            data = self.__get_api_call(url=url)
        except HTTPError as http_err:
            logger.error(f'HTTP error occurred: {http_err} - on API {url}')
            raise APICallFailedException(f'HTTP error occurred: {http_err}') 
        except:
            print(f"Failed to {info}")
            return None, None  
        else:
            return(data, self.viqName)


    def switchAccount(self, viqID, viqName):
        info=f"switch to external account {viqName}"
        url = f"{self.URL}/account/:switch?id={viqID}"
        payload = ''
        try:
            data = self.__post_api_call(url=url, payload=payload)
        except HTTPError as http_err:
            logger.error(f'HTTP error occurred: {http_err} - on API {url}')
            raise APICallFailedException(f'HTTP error occurred: {http_err}') 
        except:
            print(f"failed to get XIQ token to {info}. Cannot continue to import")
            print("exiting script...")
            raise SystemExit
        if "access_token" in data:
            #print("Logged in and Got access token: " + data["access_token"])
            self.headers["Authorization"] = "Bearer " + data["access_token"]
            self.__getVIQInfo()
            if viqName != self.viqName:
                logger.error(f"Failed to switch external accounts. Script attempted to switch to {viqName} but is still in {self.viqName}")
                print("Failed to switch to external account!!")
                print("Script is exiting...")
                raise SystemExit
            return None

        else:
            log_msg = "Unknown Error: Unable to gain access token for XIQ"
            logger.warning(log_msg)
            raise APICallFailedException(log_msg) 
        
    # LRO Functions       
    def check_lro_status(self,url):
        try:
            rawData = self.__get_api_call(url)
        except APICallFailedException as e:
            logger.error(f"failed to get LRO with {e}")
            return None, None
        except:
            logger.error(f"Failed to get LRO with unknown error")
            return None, None
        if rawData['done'] == True:
            return rawData['done'], rawData['response']
        else:
            if rawData['metadata']['status'] != "RUNNING":
                logger.error(f"long-running operation status is {rawData['metadata']['status']}")
                logger.error(f"Error msg: {rawData}")
                if 'error' in rawData:
                    return False, rawData['error']
                else:
                    return False, {"error_message": "Unknown error"}
            else:
                return False, rawData['metadata']['status']
            
    # VIQ Backup
    def viqBackup(self):
        url = f"{self.URL}/account/viq/:backup"
        try:
            response = self.__post_api_call(url,payload=None)
        except APICallFailedException as err:
            logger.error(err)
            return 'Failed'
        else:
            if response != 200:
                logger.error(f"VIQ Backup failed. - {response}")
                return 'Failed'
            else:
                return 'Success'
            
    # VIQ Export
    def viqExport(self):
        url = f"{self.URL}/account/viq/export"
        try:
            lro_url = self.__post_lro_call(url=url)
        except APICallFailedException as err:
            logger.error(err)
            return None
        return lro_url
            
    # VIQ Download export file
    def downloadFile(self, filename):
        url = f"{self.URL}/account/viq/download?reportName={filename}"
        try:
            downloadFile = self.__get_api_call(url,downloadFile=True)
        except APICallFailedException as err:
            logger.error(f"Failed to download file with {err}")
            return None
        return downloadFile

    # VIQ Import 
    def viqImport(self, filename, filepath, resendPPSK=False):
        url = f"{self.URL}/account/viq/import"
        if resendPPSK:
            url = f"{url}?resendUserNotifications=true"
        payload = {}
        # Check if the file exists
        if os.path.exists(f"{filepath}/{filename}"):
            # Prepare the files parameter for the API call
            files = {'importFile': (filename, open(f"{filepath}/{filename}", 'rb'), 'text/plain')}
            try:
                lro_url = self.__post_lro_call(url,files = files)
            except APICallFailedException as err:
                logger.error(err)
                return None
            return lro_url
        else:
            logger.error(f"File {filename} was not found in folder with script.")
            return None
