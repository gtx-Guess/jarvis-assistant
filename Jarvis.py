import os
import sys

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

# Redirect stdout and stderr
class DevNull:
    def write(self, msg):
        pass
    def flush(self):
        pass

stderr = sys.stderr
stdout = sys.stdout
sys.stderr = DevNull()
sys.stdout = DevNull()

# Import your modules
from RealtimeSTT import AudioToTextRecorder
import utils
import time
from utils import mixer

# Restore stdout and stderr
sys.stderr = stderr
sys.stdout = stdout


if __name__ == '__main__':
    recorder = AudioToTextRecorder(spinner=False, model="tiny.en", language="en", post_speech_silence_duration=0.5, silero_sensitivity=0.6)
    hot_words = ["jarvis", "?", "shutdown", "shut down", "right", "correct", "could I", "is it possible", "can I", "listen up",]
    skip_hot_word_check = False
    print("Jarvis Is Listening . . .")
    try:
        while True:
            current_text = recorder.text()
            print(current_text)
            if any(hot_word in current_text.lower() for hot_word in hot_words) or skip_hot_word_check:
                if current_text:
                    print("User: " + current_text)
                    recorder.stop()
                    if "shutdown" in current_text.lower() or "shut down" in current_text.lower():
                        try:
                            goodbye = "Shutting down now, Sir. Goodbye."
                            utils.tts_caller(goodbye)
                            time.sleep(1)
                        finally:
                            recorder.stop()
                            mixer.quit()
                            os._exit(0)
                    else:
                        current_text = current_text + " " + time.strftime("%Y-m-%d %H-%M-%S")
                        response = utils.ask_question_memory(current_text)
                        print(response)
                        speech = response.split('#')[0]
                        done = utils.tts_caller(speech)
                        skip_hot_word_check = True if "?" in response else False
                        recorder.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
        recorder.stop()
        mixer.quit()
        sys.stderr = stderr
        os.exit(0)