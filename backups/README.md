# Backups
Scripts to backup various files 

## backupFiles.py
The Script copys the data to the TempFolder(base/BackupTemp/name) on the first call. On consecutive calls, if the data has changed, it creates archives of this file(in base/{Backup}/name) then exchanges the copy in TempFolder

On default backupFiles.py only makes copies if there is a difference to the last version and avoids unnecessary copies (comparison could be changed between metadata only(shallowCheck=True, default) and bytewise compare(shallowCheck=False))

### Help:
Usage: Prepare both paths at the top of the script (use forward slashes to be sure), then use it like:

Default:
- backupFiles.py -b baseDir -p Path -n name [-c=i] [-o=j] or
- python backupFiles.py -b baseDir -p Path -n name [-c=i] [-o=j]

Silent execution:
- pythonw backupFiles.py -b baseDir -p Path -n name [-c=i] [-o=j]

It's highly recommended to use either -c or -o.
The name must be unique as the script uses that to sort and identify the backups.
The name can contain subfolders to sort your backups into groups

## gameserver-backup.py
This script basically utilises backupFiles to backup various files without cluttering the TaskSceduler with a call each.
For my usecase it is a backup for a gameserver manager and i wanted to avoid to backup any binaries dueto storage space. 

Make sure both scripts (gameserver-backup.py and backupFiles.py) are in the same folder
Then just exchange basePath and the files to backup in the middle.

Then you can run the script via any timesceduler you want. The script should be platform independent, so cron should be possible too. But i did not test that yet, so please let me know, if there is any issue or improvement to be done.

### Windows TaskSceduler
You can setup the script via Windows TaskSceduler with following settings: 

Notes: 
- My Server runs with a user constantly logged in (because of programs that need a user-session), so my scedule runs under "Run only when user is logged on".
    - It should work in "Run whether the user is logged on or not" Mode, but it is not tested.
- only use **Absolute paths** in Tasks
- the more granular you call the backupscript, the best the avoid dupplications work
    - If one file in the source folder changes, the whole folder will be backuped.

Trigger: 
- On Login / on start / on a timestamp
- Repeat every x minutes/hours

Action:
- Executable Path\To\Your\Python\PythonXXX\pythonw.exe
- Arguments Path\To\Scripts\gameserver-backup.py
- Execute IN Path\To\Scripts
  
Conditions':
- Make sure nothing is checked here
