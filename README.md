Different ways of running this when on mac vs windows.

WINDOWS
For windows we have audio and microphone support, for that there is an override file in the windows dir Run the docker command like so:
Running it (1 terminal): "docker-compose -f docker-compose.yml -f windows/docker-compose"


MAC
If working on mac, using docker jarvis will NOT have access to audio output so docker will reflect that. Running Jarvis locally he will have audio output
On mac you wont have access to a mic at all - macOS just wont allow it.
Running it (2 terminals):
1st terminal "docker compse up"
2nd terminal window "docker attach jarvis-app"

The second terminal app is how you can interact with Jarvis through text input