# StreamRecorder

## How to use
- You need Python version between 3.8 and 3.11 
  - with modules requests streamlink
- Install streamlink for your system https://streamlink.github.io/install.html (include ffmpg at best)
- Just adjust the global variables at the top to your needs (Line 18+)
- Add your Twitch client ID and Secret to your Environment Variables (user if the script runs as user, system var if not)
  - as TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET (see below for howto)
- After that you can start it with Python StreamRecorder.py 
  - you can add a list of channels to overwrite the channels defined in Global variables of the script
  - Python StreamRecorder.py MyStreamer1,Mystreamer2,Mystreamer2

## Getting the ID and Secret:
- Go to https://dev.twitch.tv/console and log in
- click on Application => Register your Application
- Add a name, choose a category, add http://localhost:3000/ as Oauth URL 
- Note the ClientId and Secret (you get it by clicking new Secret)

