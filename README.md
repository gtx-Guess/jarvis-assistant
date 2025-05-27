This is a personal assistant project.

REQUIRED: python 3.12
ALL python requirements - you may need to install some brew/winget libraries
-tesseract
-portaudio

The idea is that you would have ollama running in docker (this has a docker file for that) as an interference/router layer. Then if ollama needs to it escalate it will route the request to the proper ai model.
ChatGPT for reasoning and general info
Claude for code and software development

Different ways of running this when on mac vs windows.

Windows and MAC run similarly but youll have to install the respective list of libraries manually
