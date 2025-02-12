#!/usr/bin/env python3
import os
import sys
import time
import logging
import platform
import pandas as pd
import getpass  
from app.xiq_api import XIQ
from app.xiq_logger import logger
logger = logging.getLogger('VIQ_Backup_Restore.Main')


VERSION = "v1.0"

os_ver = platform.system()
thisfile = os.path.abspath(__file__)
scriptroot = os.path.dirname(thisfile)

folder_path = f'{scriptroot}/app/backups'
log_folder_path = f'{scriptroot}/app/script_logs'

def prgood(content):
    # print(f"[\033[0;32m✓\033[0m] {content}")
    # so that people aren't confused by the [?]. stupid Windows.
    print(f"[\033[0;32mOK\033[0m] {content}")

def prbad(content):
    print(f"[\033[0;91mXX\033[0m] {content}")

def prinfo(content):
    print(f"[--] {content}")

def exitOnEnter(errCode = 0):
    input("[--] Press Enter to exit...")
    exit(errCode)

def yesNoLoop(question):
    validResponse = False
    while validResponse != True:
        response = input(f"{question} (y/n) ").lower()
        if response =='n' or response == 'no':
            response = 'n'
            validResponse = True
        elif response == 'y' or response == 'yes':
            response = 'y'
            validResponse = True
        elif response == 'q' or response == 'quit':
            print("[--]script is exiting....")
            exitOnEnter(errCode=0)
    return response

# Check if there are any files in the folder
if not os.path.exists(folder_path):
    prbad(f"{folder_path} folder does not exist!")
    exitOnEnter(errCode=1)
elif not os.path.isdir(folder_path):
    prbad(f"{folder_path} is not a folder!")
    exitOnEnter(errCode=1)

x = None

viqStates = ["\033[30;1mBackup file not created\033[0m", "\033[33;1mBackup file exists\033[0m", "\033[32mReady\033[0m"]
viqState = 0
print(viqStates[viqState])

file_list = []

def getBackupFiles():
    global file_list, viqState
    file_list = [f for f in os.listdir(folder_path) if f.endswith('.tar.gz') and os.path.isfile(os.path.join(folder_path, f))]
    if file_list:
        if len(file_list) > 1:
            prbad("There are more than 1 backup file in the backups directory. Please remove extra backup files from ../app/backups")
            exitOnEnter(errCode=1)
        viqState = 1

def clearScreen():
    if os_ver == "Windows":
        os.system("cls")
    else:
        os.system("clear")

def _create_char_spinner():
    """Creates a generator yielding a char based spinner.
    """
    while True:
        for character in '|/-\\':
            yield character

_spinner = _create_char_spinner()

def spinner(label=''):
    """Prints label with a spinner.

    When called repeatedly from inside a loop this prints
    a one line CLI spinner.
    """
    sys.stdout.write("\r\t%s %s" % (label, next(_spinner)))
    sys.stdout.flush()

def run_spinner(duration):
    """Runs the spinner for the specified duration in seconds."""
    end_time = time.time() + duration
    while time.time() < end_time:
        spinner("Processing")
        time.sleep(0.1)  # Adjust the sleep time for spinner speed

def login():
    ## Login 
    global x
    XIQ_username = input('Email: ')
    XIQ_password = getpass.getpass('Password: ')
    if XIQ_username and XIQ_password:
        x = XIQ(user_name=XIQ_username, password=XIQ_password)
    else:
        print("username or password was not entered")
        prinfo("script is exiting....")
        exitOnEnter(errCode=2)
    prgood(f"User {XIQ_username} logged in")
    time.sleep(2)

def presentMainOptions():
    getBackupFiles()
    clearScreen()
    print()
    print(f"Current state: {viqStates[viqState]}") 

    ##Prompt user for questions
    print("\n-- Please type in a number then hit return --\n")

    print("↓ Input one of these numbers!")
    
    print("0 - Cancel and Quit",)
    print("1 - Backup XIQ Instance")
    print("2 - Export XIQ instance")
    print("3 - Import XIQ instance")
                
def getInput(options):
    if type(options) == range:
        options = [*options, (options[-1] + 1)]

    while 1:
        try:
            opt = int(input(">>> "))
        except KeyboardInterrupt:
            print()
            return -1
        except EOFError:
            print()
            return -1
        except ValueError:
            opt = 0xFFFFFFFF

        if opt not in options:
            prbad(f"Invalid input, try again. Valid inputs: {str.join(', ', (str(i) for i in options))}")
            continue

        return opt

def deleteFile(f):
    try:
        os.remove(f"{folder_path}/{f}")
        prgood(f"File '{f}' has been deleted successfully.")
        time.sleep(2)
    except FileNotFoundError:
        print(f"File '{f}' not found in {folder_path}. Please confirm it is deleted and run the script again.")
        prinfo("script is exiting....")
        exitOnEnter(errCode=3)
    except Exception as e:
        print(f"Error deleting file '{f}': {e}")
        print("Please delete the file and run the script again.")
        prinfo("script is exiting....")
        exitOnEnter(errCode=4)

def ExportXIQ():
    global x
    print("\033[5;33m=== DISCLAIMER ===\033[0m") # 5;33m? The blinking is awesome but I also don't want to frighten users lol
    print()
    print("The export operation might take time to complete.")
    print("The VIQ will be suspended during the export operation.")
    print("All users will be logged out shortly after the VIQ is suspended.")
    print()
    response = yesNoLoop("Do you want to proceed?")
    if response == 'n':
        prgood("Cancelling Export...")
        prinfo("script is exiting....\n")
        exitOnEnter(errCode=0)
    elif response == 'y':
        lro_url = x.viqExport()
        if lro_url:
            prgood("Successfully started export.")
        else:
            prbad("Failed to start export.")
            exitOnEnter(errCode=5)
        while 1:
            spinner()
            run_spinner(60)
            lro_complete, lro_status = x.check_lro_status(lro_url) 
            if lro_complete:
                print()
                prgood("Successfully exported VIQ.")
                return lro_status
            if 'error' in lro_status:
                print()
                prbad(f"VIQ export failed with {lro_status}")
                exitOnEnter(errCode=6)

def ImportXIQ(filename, resendPPSK):
    global x
    print("\033[5;33m=== DISCLAIMER ===\033[0m") # 5;33m? The blinking is awesome but I also don't want to frighten users lol
    print()
    print("The import operation might take time to complete.")
    print("The VIQ will be suspended during the import operation.")
    print("All users will be logged out shortly after the VIQ is suspended.")
    print()
    response = yesNoLoop("Do you want to proceed?")
    if response == 'n':
        prgood("Cancelling Import...")
        prinfo("script is exiting....\n")
        exitOnEnter(errCode=0)
    elif response == 'y':
        lro_url = x.viqImport(filename, folder_path, resendPPSK)
        if lro_url:
            prgood("Successfully started import.")
        else:
            prbad("Failed to start import.")
            exitOnEnter(errCode=7)
        while 1:
            spinner()
            run_spinner(60)
            lro_complete, lro_status = x.check_lro_status(lro_url) 
            if lro_complete:
                print()
                prgood("Successfully imported VIQ.")
                return lro_status
            if 'error' in lro_status:
                print()
                prbad(f"VIQ import failed with {lro_status}")
                exitOnEnter(errCode=8)


def mainMenu():
    global viqState, file_list
    presentMainOptions()

    while 1:
        optSelect = getInput(range(0, 3))
        if optSelect <=  0:
            break
        # Backup VIQ
        if optSelect == 1:
            print("This will back up the VIQ. You will need to use the GUI to restore from a backup.")
            response = yesNoLoop("Would you like to backup the VIQ?")
            if response == 'n':
                prgood("Skipping backup.")
                time.sleep(2)
                continue
            clearScreen()
            print('Enter your XIQ login credentials for the account you want to Back up')
            login()
            status = x.viqBackup()
            if status == "Success":
                prgood("Successfully backed up viq")
                time.sleep(2)
                input("[--] Press Enter to exit...")
                presentMainOptions()
            else:
                prbad("Failed to backup viq")
                time.sleep(2)
                input("[--] Press Enter to exit...")
                presentMainOptions()
        # Export VIQ
        elif optSelect == 2:
            if viqState == 1:
                print(f"{viqStates[viqState]} \033[33;1mAlready\033[0m")
                time.sleep(2)
                response = yesNoLoop(f"Would you like to delete the file '{file_list[0]}'?")
                if response == 'y':
                    deleteFile(file_list[0])
                elif response == 'n':
                    print(f"Please backup files in folder and run the script again if you want to create a new backup.")
                    prinfo("script is exiting....\n")
                    exitOnEnter(errCode=0)
            clearScreen()
            print('Enter your XIQ login credentials for the account you want to Export')
            login()
            export = ExportXIQ()
            exportFile = x.downloadFile(export['export_file_name'])
            try:
                with open(f'{folder_path}/{export['export_file_name']}', 'wb') as f:
                    f.write(exportFile)
                prgood("Export download file saved.")
                viqState = 1
            except Exception as e:
                prbad(f"An error occurred downloading the file: {e}")
                break
            prgood("Successfully exported VIQ.")
            input("[--] Press Enter to exit...")
            presentMainOptions()
        # Import VIQ
        elif optSelect == 3:
            if viqState != 1:
                prbad("No Backup files found! Please create a backup first.")
                presentMainOptions()
                continue
            clearScreen()
            print('Enter your XIQ login credentials for the account you want to Import to')
            login()
            response = yesNoLoop("Would you like to resend PPSK user notifications?")  
            if response == 'y':
                resendPPSK = True
            else:
                resendPPSK = False
            # just the name of the file. The path is added separately
            i_status = ImportXIQ(file_list[0], resendPPSK)
            if 'import_status' in i_status:
                prinfo(f"The import status was {i_status['import_status']}")
                if 'log_file_name' in i_status:
                    response = yesNoLoop("Would you like to download the log file from the import?")
                    if response == 'y':
                        logFile = x.downloadFile(i_status['log_file_name'])
                        try:
                            with open(f'{log_folder_path}/{i_status['log_file_name']}', 'wb') as f:
                                f.write(logFile)
                            prgood(f"Log file saved in app/script_logs. as {i_status['log_file_name']}")
                            viqState = 1 # TODO - do i need this? 
                            break
                        except Exception as e:
                            prbad(f"An error occurred downloading the file: {e}")
                            break
            else:
                prinfo(f"The import status was {i_status['import_status']}")
                response = yesNoLoop(f"Would you like to delete {file_list[0]} from the backup folder on your machine?")
                if response == 'y':
                    deleteFile(file_list[0])
                    prgood(f"Successfully deleted file {file_list[0]}")
                    break
    prgood("Goodbye!")
    time.sleep(2)

mainMenu()