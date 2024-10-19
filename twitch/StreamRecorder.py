import datetime
import enum
import logging
import os
import subprocess
import sys
import shutil
import time
import json
import signal
from pathlib import Path
from threading import Thread
import argparse


# Python version between 3.8 and 3.11 needed with modules requests and streamlink
# Just adjust the 2 variables below.
# after it you can start it with Python StreamRecorder.py MyFirstStreamer,MySecondStreamer

#streamlinkBinary = "/home/alex/.local/bin/streamlink"
#ffmpegBinary = "/usr/bin/ffmpeg"
streamlinkBinary = "C:\\Program Files\\Streamlink\\bin\\streamlink.exe"
ffmpegBinary = "C:\\Program Files\\Streamlink\\ffmpeg\\ffmpeg.exe"
RecorderTemp = "g:/StreamRecorder"
DestinationPath = "G:/Streams"

class TwitchResponseStatus(enum.Enum):
    ONLINE = 0
    OFFLINE = 1
    NOT_FOUND = 2
    UNAUTHORIZED = 3
    ERROR = 4

defaultQuality = "720p"

class TwitchRecorder:
    def __init__(self, username = "", logger = logging.getLogger(), ffmpeg = ffmpegBinary, streamlink=streamlinkBinary, root_path=RecorderTemp, videoLib=DestinationPath):
        # global configuration
        self.disable_ffmpeg = False
        self.refresh = 60
        self.root_path = root_path

        self.log_dir = os.path.join(root_path, "logs")
        self.postOfflineLog = True
        self.ffmpeg = ffmpeg
        self.streamLink = streamlink
        self.videoLib=videoLib
        # user configuration
        self.username = username
        self.apiReturn = {}
        self.logger = logger

    def run(self):
        # path to recorded stream
        recorded_path = os.path.join(self.root_path, "recorded", self.username)
        # path to finished video, errors removed
        processed_path = os.path.join(self.videoLib, self.username)

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
            args = None
            if os.name == 'nt':
                args = [self.ffmpeg, "-err_detect","ignore_err", "-n", "-i", recorded_filename, "-c", "copy", processed_filename]
                self.logger.info(f"Start ffmpeg with args:{' '.join(args)}")
            else:
                args = f"{self.ffmpeg} -err_detect ignore_err -n -i \"{recorded_filename}\" -c copy \"{processed_filename}\""
                self.logger.info(f"starting ffmpeg with args (could take a few minutes without output):{args}")
            logData = subprocess.Popen(args, stderr=subprocess.PIPE, shell=True).communicate()
            if os.path.exists(processed_filename):
                self.logger.info("ended ffmpeg successfully")
                os.remove(recorded_filename)
            else: 
                self.logger.error(f"Ended ffmpeg with error: {logData}")
        except Exception as e:
            self.logger.error(f"Exception on ffmpeg call: {e}")

    def check_user(self):
        title = None
        status = TwitchResponseStatus.ERROR
        quality = defaultQuality
        try:
            data = self.getStreamData()
            if data and self.streamIsOnline(data):
                status = TwitchResponseStatus.ONLINE
                title = self.getTitleOfStream(data)
                quality = self.getAvailableStreamQuality(data)
            elif not data:
                self.logger.error(f"no data gathered")
            else:
                status = TwitchResponseStatus.OFFLINE

        except Exception as e:
            status = TwitchResponseStatus.OFFLINE
        return status, title, quality

    def getStreamData(self):
        args = None
        if os.name == 'nt':
            args = [self.streamLink, "--json", f"twitch.tv/{self.username}"]
        else:
            args = f"\"{self.streamLink}\" --json twitch.tv/{self.username}"
        data = None
        try:
            output = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()
            data = json.loads(output[0])
        except Exception as e:
            self.logger.error(f"gathering infos via streamlink failed: {e}")
        return data

    def getTitleOfStream(self, data) -> str:
        return data["metadata"]["title"]

    def streamIsOnline(self, data) -> bool:
        return len(data["streams"]) != 0

    def getAvailableStreamQuality(self, data) -> str:
        stream = None
        quality = defaultQuality
        streams = data["streams"]
        if len(streams) < 1:
            return 
        if quality in streams: 
            return quality
        if streams:
            keys = []
            
            for key in list(streams.keys()):
                if not "p" in key: 
                    continue
                if defaultQuality.split("p", 1)[0] == key.split("p", 1)[0]:
                    return key
                try:
                    keys.append(int(key.split("p", 1)[0]))
                    #.split("p", 1)[0] finds even stuff like p60 for 60fps
                except Exception as e:
                    pass
                
            keys.sort(reverse=True)
            for curRes in keys:
                targetRes = int(defaultQuality.split("p", 1)[0])
                #get the highst resolution under target in case the streamer uses some weird resolutions
                if(targetRes > curRes): 
                    return curRes
                else:
                    continue

        return "720p,480p,best"

    def getPartString(self):
        part = ""
        destPath = os.path.join(self.videoLib, self.username)
        files = list(Path(destPath).glob(f'*{datetime.datetime.now().strftime("%Y-%m-%d")}*'))
        if files and len(files) != 0:
            part = f" part {len(files)+1}"
        else:
            destPath = os.path.join(self.root_path, "recorded" , self.username)
            files = list(Path(destPath).glob(f'*{datetime.datetime.now().strftime("%Y-%m-%d")}*'))        
            if files and len(files) != 0:
                part = f" part {len(files)+1}"

        return part

    def loop_check(self, recorded_path, processed_path):
        while True:
            try:
                self.apiReturn = {}
                status, title, quality = self.check_user()  
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
                    processed_filename = os.path.join(processed_path, filename)

                    # start streamlink process
                    if not os.path.isfile(self.streamLink):
                        self.logger.CRITICAL("Streamlink not set")
                    args = None
                    if os.name == 'nt':
                        args = [self.streamLink, "--twitch-disable-ads", "--twitch-low-latency", 
                                "--logfile", os.path.join(self.log_dir,f'{self.username}_{datetime.datetime.now().strftime("%Y-%m-%d")}_streamlink.log'), 
                                f"twitch.tv/{self.username }", quality, "-o", recorded_filename]
                        self.logger.info(f"Start StreamLink with args:{subprocess.list2cmdline(args)}")
                    else:
                        args = f"{self.streamLink} --twitch-disable-ads --twitch-low-latency " + f"--logfile \"{os.path.join(self.log_dir,f'{self.username}_streamlink.log')}\" twitch.tv/{self.username} {quality} -o \"{recorded_filename}\"" 
                        self.logger.info(f"Start StreamLink with args:{args}")
                    
                    retData = subprocess.Popen(args, stdout=subprocess.PIPE, shell=True).communicate()
                    
                    if os.path.exists(recorded_filename):
                        self.logger.info("recording stream is done, processing video file")
                    else:
                        self.logger.error(f"recording stream failed: {retData}")

                    if not os.path.exists(os.path.join(self.videoLib, self.username)):
                        os.makedirs(os.path.join(self.videoLib, self.username))
                    if os.path.exists(recorded_filename) is True:
                        self.process_recorded_file(recorded_filename, processed_filename)
                    else:
                        self.logger.info("skip fixing, file not found")
                        
                    self.logger.info("recording stream is done, processing video file")
                    if os.path.exists(recorded_filename) and os.path.exists(processed_filename) is False : #ffmpg failed, copy without fix
                        shutil.move(recorded_filename, processed_filename)

                    self.logger.info("processing is done, going back to checking...")
                    Sleep(self.refresh)
                    
            except Exception as ex:
                self.logger.critical(ex)


def main(argv):
    recorderThreads = {}
    recorders = {}

    #cmd params
    parser = argparse.ArgumentParser(description='Records multiple streams via streamlink'+
                                     '\nper default a ffmpeg fix run is done while copying the stream to the destination, as ad skipping causes some audio desync')
    parser.add_argument('-s','--streamlink', type=str, nargs='?', default=streamlinkBinary,
                        help='full path to your streamlink binary')
    parser.add_argument('-f','--ffmpeg', type=str, nargs='?', default=ffmpegBinary,
                        help='full path to your ffmpeg binary')
    parser.add_argument('-t','--temp', type=str, nargs='?',default=RecorderTemp,
                        help='temp folder for streamlink to record to')
    parser.add_argument('-d','--destRoot', type=str, nargs='?', default=DestinationPath,
                        help='path where the stream should be copied when recording is finished')
    parser.add_argument('-c','--channels', nargs='+', default=[],
                        help='channels to monitor')
    
    args = parser.parse_args()
    #args = parser.parse_args(["-s", "C:/Program Files/Streamlink/bin/streamlink.exe", "-f", "C:/Program Files/Streamlink/ffmpeg/ffmpeg.exe", "-t", "d:/StreamRecorder", "-d", "d:/Streams", "-c", "staiy", "vincentg", "dlz_jimmy"])

    if not args.channels:
        print(f"No channels chosen")
        exit()
    channelNames = args.channels

    logDir = os.path.join(args.temp, "logs")

    if not os.path.exists(args.temp):
        os.makedirs(args.temp)
    if not os.path.exists(logDir):
        os.makedirs(logDir)
    if not os.path.exists(args.destRoot):
        os.makedirs(args.destRoot)
    
    print(f"channels to monitor: {', '.join(channelNames)}")
    
    signal.signal(signal.SIGTERM, sigterm_handler)

    for channelName in channelNames:
        recorder = TwitchRecorder(channelName, setup_logger(channelName,os.path.join(logDir,f"{channelName}_twitch-recorder_{datetime.datetime.now().strftime("%Y-%m-%d")}.log")),args.ffmpeg, args.streamlink, args.temp,args.destRoot)
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
    formatter = logging.Formatter(u"%(asctime)s;%(levelname)s;%(message)s")
    fileHandler = logging.FileHandler(log_file, mode='a',encoding='utf-8')
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)
    l.info(f"create sublogger for {logger_name}")

    l.setLevel(level)
    l.addHandler(fileHandler)
    l.addHandler(streamHandler)
    return l

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

def sigterm_handler(_signo, _stack_frame):
    # Raises SystemExit(0):
    os._exit(0)

if __name__ == "__main__":
    main(sys.argv[1:])
