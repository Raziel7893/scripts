# StreamRecorder

## How to use
- You need Python version between 3.8 and 3.11 
- Install streamlink for your system https://streamlink.github.io/install.html (include ffmpg at best)
- Just adjust the global variables at the top to your needs (Line 18+)
- After that you can start it with Python StreamRecorder.py 
  - you can add a list of channels to overwrite the channels defined in Global variables of the script
  - Python StreamRecorder.py MyStreamer1,Mystreamer2,Mystreamer2

## WebAccess
- If you want to access those comfortably i recommend Jellyfin (https://jellyfin.org/)
- Install and make the DestinationPath to a media library

## Credits
- Base Script used as base:
  - https://github.com/ancalentari/twitch-stream-recorder/blob/master/twitch-recorder.py
