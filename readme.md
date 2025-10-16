# XIQ VIQ Backup / Restore
### xiq_backup_restore.py

|  _The software is provided as-is and [Extreme Networks](http://www.extremenetworks.com/) has no obligation to provide maintenance, support, updates, enhancements, or modifications. Any support provided by [Extreme Networks](http://www.extremenetworks.com/) is at its sole discretion._

_Issues and/or bug fixes may be reported on in the Issues for this repository._  |

## Purpose
This script preforms 3 different functions. When ran the user will be presented with options to select which function should be preformed. 
1) The backup the configuration for the VIQ - Which can be restored if needed from the GUI
> Note: Currently there is no API available to restore a backup
2) The script can Export a VIQ and download the file. The file is downloaded into the ../app/backups folder included with the script.
3) The script can Import a downloaded VIQ. 
> Note: it works best if the VIQ is reset. There currently is no API call to reset a VIQ, this would need to be done in the GUI.

## Information
The script will check if an Exported file exists in the ../app/backups folder. If a file exists and the option to Export is selected the user will be given an option to delete the file. If the file is not deleted the script will end and the user can then backup the file into a different location.
If the Import function is selected, once the Import is completed, the user will be presented with an option to download the log file, wether the Import is successful or not. If downloaded the log will be downloaded to the ../app/script_logs folder.

Once the user chooses a selections, the user will be presented with login information for the VIQ they would like to backup, export, or import.

## Needed Files
The script uses other files. If these files are missing the script will not function. 
In the same folder as the script, there should be an ../app/ folder. This folder will contain the /backups/ folder, the /script_logs/ folder and 2 additional scripts, xiq_api.py and xiq_logger.py

## Running the script
open the terminal to the location of the script and run this command.
```
python xiq_backup_restore.py
```
### Optional Flags
There is an optional flag that can be added to the script when running.
```
--external
```
This flag will enable you to execute this script on an XIQ account where you are an external user. After logging in with your XIQ credentials, the script will give you a numeric option of each of the XIQ instances you have access to. Choose the one you would like to use.

You can add the flag when running the script.
```
python xiq_backup_restore.py --external
```

## Requirements
There are additional modules that need to be installed in order for this script to function. They are listed in the requirements.txt file and can be installed with the 'pip install -r requirements.txt' if pip is used.