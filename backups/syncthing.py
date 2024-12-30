import subprocess
import logging
import os
import json
import sys
import requests

folderStats = "https://192.168.178.12:8384/rest/stats/folder"
deviceStats = "https://192.168.178.12:8384/rest/stats/device"

def main(argv):
    apiKey = "C9xDjxgPifacckQRDVDqi9vFPX9ZiuFc"
    # curl --insecure -X GET -H "X-API-Key: C9xDjxgPifacckQRDVDqi9vFPX9ZiuFc" https://192.168.178.12:8384/rest/stats/folder
    # curl --insecure -X GET -H "X-API-Key: C9xDjxgPifacckQRDVDqi9vFPX9ZiuFc" https://192.168.178.12:8384/rest/stats/device
    # dann liste aus elementen
    devices = getData(deviceStats)
    folders = getData(folderStats)

def getData(url):
    try:
        Headers = { "X-API-Key" : "C9xDjxgPifacckQRDVDqi9vFPX9ZiuFc" }
        response = requests.get(url, headers=Headers,verify=False)
        data = response.json()
        return data
        
    except Exception as e:
        logging.getLogger().error(f"gathering infos via rest api failed: {e}")
        


def setup_logger(log_file, level=logging.INFO) -> logging.Logger:
    l = logging.getLogger()
    formatter = logging.Formatter(u"%(asctime)s;%(levelname)s;%(message)s")
    fileHandler = logging.FileHandler(log_file, mode='w',encoding='utf-8')
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)

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

def sigterm_handler(_signo, _stack_frame):
    # Raises SystemExit(0):
    os._exit(0)

if __name__ == "__main__":
    main(sys.argv[1:])