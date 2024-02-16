# Backups
Scripts to backup various files 

## backupFiles.py
The Script copys the data to the TempFolder(base/BackupTemp/name) on the first call. On consecutive calls, if the data has changed, it creates archives of this file(in base/{Backup}/name) then exchanges the copy in TempFolder
On default backupFiles.py only makes copies if there is a difference to the last version and avoids unnecessary copies (comparison could be changed between metadata(shallowCheck=True, default) only and bytewise compare(shallowCheck=False))

### Help:
Usage: Prepare both paths at the top of the script (use forward slashes to be sure), then use it like:
Default:
    backupFiles.py -b baseDir -p Path -n name [-c=i] [-o=j] or
    python backupFiles.py -b baseDir -p Path -n name [-c=i] [-o=j]
Silent execution:
    pythonw backupFiles.py -b baseDir -p Path -n name [-c=i] [-o=j]     
It's highly recommended to use either -c or -o.
The name must be unique as the script uses that to sort and identify the backups.
The name can contain subfolders to sort your backups into groups

## gameserver-backup.py
Make sure both scripts (gameserver-backup.py and backupFiles.py) are in the same folder
Then just exchange basePath and the files to backup in the middle.

Then you can run it with the WindowsTaskSceduler with following settings: 
Notes: 
- My Server runs with a user constantly logged in (because of programs that need a user-session), so my scedule runs under "Run only when user is logged on".
    - It should work in "Run whether the user is logged on or not" Mode, but it is not tested.
- only use **Absolute paths** in Tasks
Trigger: 
- On Login / on start / on a timestamp
- Repeat every x minutes/hours
Action:
- Executable Path\To\Your\Python\PythonXXX\pythonw.exe
- Arguments Path\To\Scripts\gameserver-backup.py
- Execute IN Path\To\Scripts
Conditions':
- Make sure nothing is checked here
