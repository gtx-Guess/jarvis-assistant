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

# Try to import RealtimeSTT - if it fails, we'll use text input
try:
    from RealtimeSTT import AudioToTextRecorder
    STT_AVAILABLE = True
except ImportError:
    STT_AVAILABLE = False

import utils.utils as utils
import time
from utils.utils import mixer, debug_model_access

# Restore stdout and stderr
sys.stderr = stderr
sys.stdout = stdout


def text_input_mode():
    """Handle text-based input when STT is not available"""
    hot_words = ["jarvis", "?", "shutdown", "shut down", "right", "correct", "could I", "is it possible", "can I", "listen up"]
    skip_hot_word_check = False
    
    print("Jarvis Text Assistant Ready...")
    print("Type 'shutdown' or 'shut down' to exit.")
    print("=" * 100)
    text_input_counter = 0
    try:
        while True:
            # Get text input from user
            try:
                current_text = input("You: ").strip()
            except EOFError:
                # Handle Ctrl+D
                break
            
            if not current_text:
                continue
                
            print(f"User: {current_text}")
            
            # Check for hot words or if we're in skip mode
            if any(hot_word in current_text.lower() for hot_word in hot_words) or skip_hot_word_check:
                if current_text:
                    # Check for shutdown command
                    if "shutdown" in current_text.lower() or "shut down" in current_text.lower():
                        goodbye = "Shutting down now, Sir. Goodbye."
                        try:
                            print(f"Jarvis: {goodbye}")
                            utils.tts_caller(goodbye)
                        finally:
                            mixer.quit()
                            print("=" * 100)
                            return
                    else:
                        # Process the request
                        current_text = current_text + " " + time.strftime("%Y-%m-%d %H-%M-%S")
                        response = utils.ask_question_memory(current_text)
                        
                        # Split response and speech
                        speech = response.split('#')[0]
                        print(f"Jarvis: {speech}")
                        
                        # Play TTS
                        utils.tts_caller(speech)
                        
                        # Check if we should skip hot word check next time
                        skip_hot_word_check = True if "?" in response else False
            else:
                text_input_counter += 1
                if text_input_counter == 10:
                    print("Jarvis: I'm listening for a hot word to activate...")
                
    except KeyboardInterrupt:
        print("\nShutting down...")
        mixer.quit()
        print("Goodbye!")
        print("=" * 100)


def speech_input_mode():
    """Handle speech-to-text input when STT is available"""
    recorder = AudioToTextRecorder(spinner=False, model="tiny.en", language="en", post_speech_silence_duration=0.5, silero_sensitivity=0.6)
    hot_words = ["jarvis", "?", "shutdown", "shut down", "right", "correct", "could I", "is it possible", "can I", "listen up"]
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
                        goodbye = "Shutting down now, Sir. Goodbye."
                        try:
                            utils.tts_caller(goodbye)
                        finally:
                            recorder.stop()
                            mixer.quit()
                            print("=" * 100)
                            os._exit(0)
                    else:
                        current_text = current_text + " " + time.strftime("%Y-%m-%d %H-%M-%S")
                        response = utils.ask_question_memory(current_text)
                        print(response)
                        speech = response.split('#')[0]
                        done = utils.tts_caller(speech)
                        skip_hot_word_check = True if "?" in response else False
                        recorder.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
        print("=" * 100)
        recorder.stop()
        mixer.quit()
        sys.stderr = stderr
        os.exit(0)


if __name__ == '__main__':
    speech = False
    # debug_model_access()
    if STT_AVAILABLE and speech:
        print("RealtimeSTT detected - Using speech input mode")
        speech_input_mode()
    else:
        print("RealtimeSTT not available - Using text input mode")
        text_input_mode()