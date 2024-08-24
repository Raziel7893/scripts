# StreamRecorder

## How to use
- You need Python version between 3.8 and 3.11 
- Install streamlink for your system https://streamlink.github.io/install.html (include ffmpg at best)
- example call to execute:(use pythonw.exe to start silent without a window on windows)
  - python3.11 StreamRecorder.py -s "C:/Program Files/Streamlink/bin/streamlink.exe" -f "C:/Program Files/Streamlink/ffmpeg/ffmpeg.exe" -t "d:/StreamRecorder" -d "d:/Streams" -c dracon staiy
- if you just want to call StreamRecorder.py you can switch the comment on lines 266&267 (the args = lines) and use fixed parameters
- all parameters are optional and will use the old defaults if skipped, so you can use it also as
  - python3.11 StreamRecorder.py -c channel1 channel2 

## WebAccess
- If you want to access those comfortably i recommend Jellyfin (https://jellyfin.org/)
- Install and make the DestinationPath to a media library

## Current cmd arguments
Records multiple streams via streamlink per default a ffmpeg fix run is done while copying the stream to the destination, as ad skipping causes some audio desync

usage: StreamRecorder.py [-h] [-s [STREAMLINK]] [-f [FFMPEG]] [-t [TEMP]] [-d [DESTROOT]] [-c CHANNELS [CHANNELS ...]]

Records multiple streams via streamlink per default a ffmpeg fix run is done while copying the stream to the destination, as ad skipping causes some audio desync

options:

  -h, --help            show this help message and exit
  
  -s [STREAMLINK], --streamlink [STREAMLINK]
                        full path to your streamlink binary
						
  -f [FFMPEG], --ffmpeg [FFMPEG]
                        full path to your ffmpeg binary
						
  -t [TEMP], --temp [TEMP]
                        temp folder for streamlink to record to
						
  -d [DESTROOT], --destRoot [DESTROOT]
                        path where the stream should be copied when recording is finished
						
  -c CHANNELS [CHANNELS ...], --channels CHANNELS [CHANNELS ...]
                        channels to monitor
