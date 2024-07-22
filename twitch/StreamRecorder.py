import datetime
import enum
import logging
import os
import subprocess
import sys
import shutil
import time
import json
import glob
from pathlib import Path
from threading import Thread


# Python version between 3.8 and 3.11 needed with modules requests and streamlink
# Just adjust the 2 variables below.
# after it you can start it with Python StreamRecorder.py MyFirstStreamer,MySecondStreamer

streamlinkBinary = "C:\\Program Files\\Streamlink\\bin\\streamlink.exe"
ffmpgBinary = "C:\\Program Files\\Streamlink\\ffmpeg\\ffmpeg.exe"
DestinationPath = "e:\\StreamRecorder\\"
VideoLibraryPath = "e:\\Streams\\"
DefaultChannels = ["dracon"]

class TwitchResponseStatus(enum.Enum):
    ONLINE = 0
    OFFLINE = 1
    NOT_FOUND = 2
    UNAUTHORIZED = 3
    ERROR = 4

defaultQuality = "720p"

class TwitchRecorder:
    def __init__(self, username = "", logger = logging.getLogger()):
        # global configuration
        self.disable_ffmpeg = False
        self.refresh = 60
        self.root_path = DestinationPath
        self.postOfflineLog = True
        # user configuration
        self.username = username

        self.logger = logger

    def run(self):
        # path to recorded stream
        recorded_path = os.path.join(self.root_path, "recorded", self.username)
        # path to finished video, errors removed
        processed_path = os.path.join(self.root_path, "processed", self.username)

        # create directory for recordedPath and processedPath if not exist
        if os.path.isdir(recorded_path) is False:
            os.makedirs(recorded_path)
        if os.path.isdir(processed_path) is False:
            os.makedirs(processed_path)

        # make sure the interval to check user availability is not less than 60 seconds
        if self.refresh < 30:
            self.refresh = 30

        # fix videos from previous recording session
        try:
            video_list = [f for f in os.listdir(recorded_path) if os.path.isfile(os.path.join(recorded_path, f))]
            if len(video_list) > 0:
                self.logger.info("processing previously recorded files")
            for f in video_list:
                recorded_filename = os.path.join(recorded_path, f)
                processed_filename = os.path.join(processed_path, f)
                self.process_recorded_file(recorded_filename, processed_filename)
        except Exception as e:
            self.logger.error(e)

        self.logger.info("checking for %s every %s seconds, recording ",
                     self.username, self.refresh)
        self.loop_check(recorded_path, processed_path)

    def process_recorded_file(self, recorded_filename, processed_filename):
        if self.disable_ffmpeg:
            self.logger.info("moving: %s", recorded_filename)
            shutil.move(recorded_filename, processed_filename)
        else:
            self.logger.info("fixing %s", recorded_filename)
            self.ffmpeg_copy_and_fix_errors(recorded_filename, processed_filename)

    def ffmpeg_copy_and_fix_errors(self, recorded_filename, processed_filename):
        try:
            subprocess.call(
                [ffmpgBinary, "-err_detect", "ignore_err", "-i", recorded_filename, "-c", "copy",
                 processed_filename], shell=True)
            if os.path.exists(processed_filename): 
                os.remove(recorded_filename)
        except Exception as e:
            self.logger.error(e)

    def check_user(self):
        title = None
        status = TwitchResponseStatus.ERROR
        try:
            if StreamIsOnline(self.username):
                status = TwitchResponseStatus.ONLINE
                title = GetTitleOfStream(self.username)
            else:
                status = TwitchResponseStatus.OFFLINE

        except Exception as e:
            status = TwitchResponseStatus.OFFLINE
        return status, title

    def getPartString(self) -> int:
        part = ""
        destPath = os.path.join(VideoLibraryPath, self.username)
        files = list(Path(destPath).glob(f'*{datetime.datetime.now().strftime("%Y-%m-%d")}*'))
        if files and len(files) != 0:
            part = f" part {len(files)+1}"
        return part

    def loop_check(self, recorded_path, processed_path):
        while True:
            status, title = self.check_user()  
            if status == TwitchResponseStatus.OFFLINE:
                if self.postOfflineLog:
                    self.logger.info("%s currently offline, checking again in %s seconds. This log will not reapear to allow HDDs to spin down ", self.username, self.refresh)
                    self.postOfflineLog = False 
                Sleep(self.refresh)
            elif status == TwitchResponseStatus.ONLINE:
                self.postOfflineLog = True
                self.logger.info("%s online, stream recording in session", self.username)

                filename = self.username + " - " + datetime.datetime.now() \
                    .strftime("%Y-%m-%d") + self.getPartString() +" - " + title + ".mp4"

                # clean filename from unnecessary characters
                filename = "".join(x for x in filename if x.isalnum() or x in [" ", "-", "_", "."])

                recorded_filename = os.path.join(recorded_path, filename)
                processed_filename = os.path.join(VideoLibraryPath, self.username, filename)

                # start streamlink process
                if not os.path.isfile(streamlinkBinary):
                    logging.CRITICAL("Streamlink not set")
                    
                subprocess.call(
                    [streamlinkBinary, "--twitch-disable-ads", "--twitch-low-latency", "--logfile", "f{DestinationPath}{self.username}_streamlink.log", "twitch.tv/" + self.username, GetAvailableStreamQuality(self.username), "-o", recorded_filename], shell=True)
                
                self.logger.info("recording stream is done, processing video file")
                
                if not os.path.exists(os.path.join(VideoLibraryPath, self.username)):
                    os.makedirs(os.path.join(VideoLibraryPath, self.username))
                if os.path.exists(recorded_filename) is True:
                    self.process_recorded_file(recorded_filename, processed_filename)
                else:
                    self.logger.info("skip fixing, file not found")
                    
                self.logger.info("recording stream is done, processing video file")
                if os.path.exists(processed_filename) is False: #ffmpg failed, copy without fix
                    shutil.move(recorded_filename, processed_filename)

                self.logger.info("processing is done, going back to checking...")
                Sleep(self.refresh)


def main(argv):
    recorderThreads = {}
    recorders = {}
    channelNames = DefaultChannels

    if not os.path.exists(VideoLibraryPath):
        os.makedirs(VideoLibraryPath)
    if not os.path.exists(DestinationPath):
        os.makedirs(DestinationPath)
    
    if(len(argv)>=1):
        channelNames = argv[0].split(",")
    print(f"channels to monitor: {' '.join(channelNames)}")
    
    for channelName in channelNames:
        recorder = TwitchRecorder(channelName, setup_logger(channelName,f"{DestinationPath}{channelName}twitch-recorder.log"))
        recorders[channelName] = recorder
        recorderThreads[channelName] = createThread(recorder)
    while True:
        Sleep(30)
        for channelName in channelNames:
            if not recorderThreads[channelName].is_alive:
                #recreate thread if it failed
                recorderThreads[channelName] = createThread(recorders[channelName])

def createThread(recorder : TwitchRecorder) -> Thread:
    thread = Thread(target = recorder.run)
    thread.daemon = True
    thread.start()
    return thread

def setup_logger(logger_name, log_file, level=logging.INFO) -> logging.Logger:
    l = logging.getLogger(logger_name)
    l.info(f"create sublogger for {logger_name}")
    formatter = logging.Formatter('%(message)s')
    fileHandler = logging.FileHandler(log_file, mode='w')
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)

    l.setLevel(level)
    l.addHandler(fileHandler)
    l.addHandler(streamHandler)
    return l

#goes through the available streams and find the nearest to defaultQuality
def GetStreamData(channelName):
    output = subprocess.Popen([streamlinkBinary, "--json", "twitch.tv/" + channelName], stdout=subprocess.PIPE, shell= True).communicate()
    return json.loads(output[0])

def GetTitleOfStream(channelName) -> str:
    return GetStreamData(channelName)["metadata"]["title"]

def StreamIsOnline(channelName) -> bool:
    return len(GetStreamData(channelName)["streams"]) != 0

def GetAvailableStreamQuality(channelName) -> str:
    stream = None
    quality = defaultQuality
    streams = GetStreamData(channelName)["streams"]
    if len(streams) < 1:
        return 
    if quality in streams:
        return quality
    if stream:
        keys = list(streams.keys())
        for key in keys:
            targetRes = int(defaultQuality.replace("p"))
            curRes = int(keys.replace("p"))
            #get the highst resolution under 720p in case the streamer uses some weird resolutions
            if not curRes or curRes == -1:
                continue
            if(targetRes < curRes):
                quality = key
            else:
                continue
        return key
    else:
        #fallback
        return "best" 

def ParseInt(value):
  if value is None:
      return -1
  try:
      return int(value)
  except:
      return -1

def Sleep(duration):    
    try:
        time.sleep(duration)
    except KeyboardInterrupt:
        os._exit(1)
        

if __name__ == "__main__":
    main(sys.argv[1:])