#!/usr/bin/env python3
import argparse
import shutil
import os
import filecmp
from datetime import datetime
from pathlib import Path
from typing import List
import arrow
import sys
try:
    import tkinter
    from tkinter import messagebox
except ImportError:
    pass

tmpFolder = "/BackupTemp/"
backupFolder = "/Backup/"


def CheckDiskUsage(path: str):
    base = path
    if '\\' in base:
        base = base.split('\\')[0]
    if '/' in base:
        base = base.split('/')[0]
    total, used, free = shutil.disk_usage(base)
    if used/total > 0.95:
        print(
            f"Disk is nearly full({int((used/total)*100)}). please check or adjust backup limits!")
        # try creating a window to notify user
        try:
            rootWindow = tkinter.Tk()
            rootWindow.withdraw()
            messagebox.showwarning(
                "Disk is nearly full", f"Disk is nearly full({int((used/total)*100)}). please check or adjust backup limits!")
        except Exception:
            pass


def make_archive(destPath: str, src: str):
    now = datetime.now()
    dt_string = now.strftime("%Y_%m_%d_%H_%M_%S")
    if Path(src).is_dir():
        shutil.make_archive(destPath+"/"+dt_string, 'zip', src)
    else:
        shutil.make_archive(destPath+"/"+dt_string, 'zip',
                            Path(src).parent, Path(src).name)


def checkFileDate(files: List[Path], daysToKeep: int):
    oldesDate = arrow.now().shift(days=-int(daysToKeep))
    for f in files:
        if f.is_file():
            item_time = arrow.get(f.stat().st_mtime)
            if item_time < oldesDate:
                os.remove(f)


def checkFileCount(files: List[Path], versionsToKeep: int):
    maxFiles = int(versionsToKeep)
    if len(files) > maxFiles:
        for i in range(0, len(files)-maxFiles):
            oldestFile = files[i]
            if oldestFile.is_file():
                os.remove(oldestFile)


def deleteTmp(path: str):
    if Path(path).is_file():
        os.remove(path)
    elif Path(path).is_dir():
        shutil.rmtree(path)
    else:
        print(f"{path} does not exist, seems to be the first backup-call")


def createArchive(base: str, backupName: str):
    tmpPath = base+tmpFolder+backupName
    backupPath = base+backupFolder+backupName
    make_archive(backupPath, tmpPath)


def compareEqual(filePath: str, tmpPath: str, shallow: bool):
    if Path(filePath).is_dir():
        files = Path(filePath).glob('*')
        for f in files:
            curPath = Path(f)
            curTmpPath = tmpPath+"/"+curPath.name

            if not Path(curTmpPath).exists():
                # new file added
                return False
            if curPath.is_dir():
                # solve directorys recursivly, maybe add a exit if it recurses to much?
                if compareEqual(curPath, curTmpPath, shallow):
                    # folder is equal, continue to check
                    continue
                else:
                    return False

            if filecmp.cmp(curPath, curTmpPath, shallow=shallow):
                # file equal, continue to check
                continue

            # not equal, return
            return False
        return True
    if filecmp.cmp(filePath, tmpPath, shallow=shallow):
        return True
    return False


def copyToTemp(filePath: str, tmpPath: str):
    deleteTmp(tmpPath)
    os.makedirs(Path(tmpPath).parent, exist_ok=True)
    if Path(filePath).is_file():
        shutil.copy(filePath, tmpPath)
    else:
        shutil.copytree(filePath, tmpPath)


def IsNullOrDefault(val: int) -> bool:
    if val == None:
        return True
    if val == 0:
        return True
    return False


def checkVersionLimit(backupPath: str, versionsToKeep: int, daysToKeep: int):
    scanPath = backupPath
    if Path(scanPath).is_file():
        scanPath = Path(scanPath).parent
    if not IsNullOrDefault(daysToKeep) and not IsNullOrDefault(versionsToKeep):
        print(
            f"Both variants of versioning controll was used. appling both,daysToKeep:{daysToKeep}, versionsToKeep:{versionsToKeep}")
    elif IsNullOrDefault(daysToKeep) and IsNullOrDefault(versionsToKeep):
        print("No deletion dueto missing parameters. It is highly recommended to either include versionCount(-c) or deleteOlder(-o)")

    files = sorted(Path(scanPath).glob('*'), key=os.path.getmtime)

    if not IsNullOrDefault(daysToKeep):
        checkFileDate(files, daysToKeep)
    if not IsNullOrDefault(versionsToKeep):
        checkFileCount(files, versionsToKeep)

# base: Root where the Backup structure is placed
# filePath: file or folder you want to backup
# backupName: Path after base+backupFolder(and BackupTemp) where you want to store the backup. Will create backups like  base+backupFolder/backupName/date.zip
#   most time it should be the last part of the backup filePath. do not end it with slashes
#   example:    -f C:/Users/Games/.chatty/settings backupName=.chatty/settings
# versionsToKeep: deletes the oldest files if there are over x archives
# shallowCheck: type of comparison to use. True checks only metadata if the file was changed. false should use bytewise comparison, check #https://docs.python.org/3/library/filecmp.html
# daysToKeep: deletes files after x days


def backup(base: str, filePath: str, backupName: str, versionsToKeep: int = 0, shallowCheck: bool = True, daysToKeep: int = 0):
    tmpPath = base+tmpFolder+backupName
    backupPath = base+backupFolder+backupName+"/"
    CheckDiskUsage(base)

    if Path(tmpPath).exists():
        # https://docs.python.org/3/library/filecmp.html
        # for files: only save copies if there was a change
        # TODO: for dirs there could be an iteration happen
        if compareEqual(filePath, tmpPath, shallowCheck):
            print(f"State: No changes found in {filePath}")
            return
        else:
            print(f"State: Found changes in {filePath}, creating archive")
            createArchive(base, backupName)
        # delete tmp files to recreate without issue

    copyToTemp(filePath, tmpPath)
    checkVersionLimit(backupPath, versionsToKeep, daysToKeep)


def main() -> int:
    parser = argparse.ArgumentParser(usage="Prepare both paths at the top of the script (use forward slashes to be sure), then use it like: \nbackupFiles.py -p x -n y [-c=i] [-o=j] or \npython backupFiles.py -p x -n y [-c=i] [-o=j] \nIt's highly recommended to use either -c or -o.",
                                     description=f"The Script copys the data to the TempFolder(base/{tmpFolder}/name) on the first call. On consecutive calls, if the data has changed, it creates archives of this file(in base/{backupFolder}/name) then exchanges the copy in TempFolder")
    parser.add_argument(
        "--filePath", '-p', help="file or folder that you want to backup", required=True)
    parser.add_argument(
        "--base", '-b', help="BasePath Of the Backups. base/Backup and base/BackupTemp will be created", required=True)
    parser.add_argument(
        "--name", '-n', help="Name of the Backup, used as sub-path in the backup folders", required=True)
    parser.add_argument("--versionCount", '-c',
                        help="number of versions to keep", required=False, type=int)
    parser.add_argument("--deleteOlderThan", '-o',
                        help="keep everything newer than o days", required=False, type=int)
    parser.add_argument("--shallowCompareType", '-s',
                        help="How should files be checked. If set to False, it should do byte-wise compares", required=False, default=True)
    args = parser.parse_args()

    backup(filePath=args.filePath, backupName=args.name, shallowCheck=args.shallowCompareType,
           versionsToKeep=args.versionCount, daysToKeep=args.deleteOlderThan)


if __name__ == '__main__':
    sys.exit(main())
