import sys
try:
    import backupFiles
except ImportError:
    raise ImportError('BackupFiles needs to be in the same folder or in an importable path!')

basePath = "E:/"

#this file needs to be in the same folder as backupFiles.py

def main() -> int:
	print("Start Gameserver Backup")
    #just exchange the folders or files to be backuped and choose a variant to delete.  if you want a maximum number of files exchange the daysToKeep with versionsToKeep
    #versionsToKeep = number of versions to keep
    #daysToKeep = deletes everything older than x days
	backupFiles.backup(basePath, filePath="C:/Data/Servers/WinGSM/configs", backupName="WinGSM/configs", shallowCheck=True, daysToKeep=14)
	backupFiles.backup(basePath, filePath="C:/Data/Servers/WinGSM/plugins", backupName="WinGSM/plugins", shallowCheck=True, daysToKeep=14)
	backupFiles.backup(basePath, filePath="C:/Data/Servers/WinGSM/servers/1/configs", backupName="Enshrouded/configs", shallowCheck=True, daysToKeep=14)
	backupFiles.backup(basePath, filePath="C:/Data/Servers/WinGSM/servers/1/serverfiles/savegame", backupName="Enshrouded/serverfiles/savegame", shallowCheck=True, daysToKeep=14)
	backupFiles.backup(basePath, filePath="C:/Data/Servers/WinGSM/servers/2/configs", backupName="ProjectZomboid/configs", shallowCheck=True, daysToKeep=14)
	backupFiles.backup(basePath, filePath="C:/Data/Servers/WinGSM/servers/2/Zomboid", backupName="ProjectZomboid/Zomboid", shallowCheck=True, daysToKeep=14)
	backupFiles.backup(basePath, filePath="C:/Data/Servers/WinGSM/servers/3/configs", backupName="Smalland/configs", shallowCheck=True, daysToKeep=14)
	backupFiles.backup(basePath, filePath="C:/Data/Servers/WinGSM/servers/3/serverfiles/SMALLAND/Saved/SaveGames", backupName="Smalland/Smalland/Saved/SaveGames", shallowCheck=True, daysToKeep=14)
	backupFiles.backup(basePath, filePath="C:/Data/Servers/WinGSM/servers/3/serverfiles/SMALLAND/Saved/Config/WindowsServer", backupName="Smalland/Smalland/Saved/Config/WindowsServer", shallowCheck=True, daysToKeep=14)

if __name__ == '__main__':
    sys.exit(main())