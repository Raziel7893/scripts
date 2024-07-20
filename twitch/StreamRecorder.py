import datetime
import enum
import logging
import os
import subprocess
import streamlink
import requests
import sys
import shutil
import time
import json
from threading import Thread


# Python version between 3.8 and 3.11 needed with modules requests and streamlink
# Just adjust the 2 variables below.
# after it you can start it with Python StreamRecorder.py MyFirstStreamer,MySecondStreamer

streamlinkBinary = "C:\\Program Files\\Streamlink\\bin\\streamlink.exe"
ffmpgBinary = "C:\\Program Files\\Streamlink\\ffmpeg\\ffmpeg.exe"
DestinationPath = "d:\\StreamRecorder\\"
VideoLibraryPath = "d:\\Streams\\"
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
        self.refresh = 15
        self.root_path = DestinationPath

        # user configuration
        self.username = username

        self.logger = logger
        self.useApi = False

        #twitch configuration
        if (not os.environ.get('TWITCH_CLIENT_ID') or not os.environ.get('TWITCH_CLIENT_SECRET')):
            self.logger.error("Twitch api keys not set. reverting to backup")
            self.useApi = False

        if self.useApi:
            self.client_id =  os.environ.get('TWITCH_CLIENT_ID')
            self.client_secret = os.environ.get('TWITCH_CLIENT_SECRET')
            self.token_url = "https://id.twitch.tv/oauth2/token?client_id=" + self.client_id + "&client_secret=" \
                             + self.client_secret + "&grant_type=client_credentials"
            self.url = "https://api.twitch.tv/helix/streams"
            self.access_token = self.fetch_access_token()

    def fetch_access_token(self):
        if self.useApi:
            token_response = requests.post(self.token_url, timeout=15)
            token_response.raise_for_status()
            token = token_response.json()
            return token["access_token"]

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
        if self.refresh < 60:
            self.refresh = 60

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
            os.remove(recorded_filename)
        except Exception as e:
            self.logger.error(e)

    def check_user(self):
        title = None
        status = TwitchResponseStatus.ERROR
        try:
            if(self.useApi):
                headers = {"Client-ID": self.client_id, "Authorization": "Bearer " + self.access_token}
                r = requests.get(self.url + "?user_login=" + self.username, headers=headers, timeout=15)
                r.raise_for_status()
                info = r.json()
                if info is None or not info["data"]:
                    status = TwitchResponseStatus.OFFLINE
                else:
                    channels = info["data"]
                    channel = next(iter(channels), None)
                    title = channel.get("title")
                    status = TwitchResponseStatus.ONLINE
            else:
                if StreamIsOnline(self.username):
                    status = TwitchResponseStatus.ONLINE
                    title = GetTitleOfStream(self.username)
                else:
                    status = TwitchResponseStatus.OFFLINE

        except requests.exceptions.RequestException as e:
            if e.response:
                if e.response.status_code == 401:
                    status = TwitchResponseStatus.UNAUTHORIZED
                if e.response.status_code == 404:
                    status = TwitchResponseStatus.NOT_FOUND
        return status, title

    def loop_check(self, recorded_path, processed_path):
        while True:
            status, title = self.check_user()   #make threads for all streamers later
            if status == TwitchResponseStatus.NOT_FOUND:
                self.logger.error("username not found, invalid username or typo")
                Sleep(self.refresh)
            elif status == TwitchResponseStatus.ERROR:
                self.logger.error("%s unexpected error. will try again in 5 minutes",
                              datetime.datetime.now().strftime("%Hh%Mm%Ss"))
                Sleep(300)
            elif status == TwitchResponseStatus.OFFLINE:
                self.logger.info("%s currently offline, checking again in %s seconds", self.username, self.refresh)
                Sleep(self.refresh)
            elif status == TwitchResponseStatus.UNAUTHORIZED:
                self.logger.info("unauthorized, will attempt to log back in immediately")
                self.access_token = self.fetch_access_token()
            elif status == TwitchResponseStatus.ONLINE:
                self.logger.info("%s online, stream recording in session", self.username)

                filename = self.username + " - " + datetime.datetime.now() \
                    .strftime("%Y-%m-%d %Hh%Mm%Ss") + " - " + title + ".mp4"

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
def GetTitleOfStream(channelName) -> bool:
    output = subprocess.Popen([streamlinkBinary, "--json", "twitch.tv/" + channelName], stdout=subprocess.PIPE).communicate()
    data = json.loads(output[0])
    return data["metadata"]["title"]

def StreamIsOnline(channelName) -> str:
    return len(streamlink.streams(f"twitch.tv/{channelName}")) != 0

def GetAvailableStreamQuality(channelName) -> str:
    stream = None
    quality = defaultQuality
    streams = streamlink.streams(f"twitch.tv/{channelName}")
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