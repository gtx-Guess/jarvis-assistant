import sys
import time
from utils.class_models.ScreenMonitor import ScreenMonitor
import utils.utils as utils

# Try to import RealtimeSTT
try:
    from RealtimeSTT import AudioToTextRecorder
    STT_AVAILABLE = True
except ImportError:
    STT_AVAILABLE = False

class JarvisApp:
    def __init__(self):
        self.screen_monitor = ScreenMonitor()
        self.text_input_counter = 0
        self.recorder = None
        self.hot_words = ["jarvis", "?", "shutdown", "shut down", "right", "correct", 
                         "could I", "is it possible", "can I", "listen up", "screen", 
                         "monitor", "analyze", "look at", "review", "explain", "debug"]
        self.skip_hot_word_check = False
        
        # Store original streams for restoration
        self.original_stderr = sys.stderr
        self.original_stdout = sys.stdout
        self.conversation_history = []
    
    def clear_history(self):
        self.conversation_history.clear()
        utils.tts_caller("Conversation history has been cleared")
        
    def cleanup_and_exit(self):
        """Graceful shutdown with proper cleanup order"""
        print("\nShutting down...")
        utils.tts_caller("Shutting down services")
        # Stop screen monitoring
        if self.screen_monitor:
            try:
                self.screen_monitor.stop_monitoring()
            except Exception as e:
                print(f"⚠️ Screen monitor cleanup failed: {e}")
        
        # Stop audio recorder
        if self.recorder:
            try:
                print("Stopping audio recorder...")
                self.recorder.stop()
                time.sleep(0.5)
                print("✅ Audio recorder stopped")
                utils.tts_caller("Audio recorder stopped")
            except Exception as e:
                print(f"⚠️ Audio recorder cleanup failed: {e}")
        
        # Announce mixer shutdown BEFORE actually stopping it
        try:
            utils.tts_caller("Audio mixer shutting down")
            time.sleep(1)  # Give TTS time to finish
            utils.mixer.quit()
            print("✅ Audio mixer stopped")
        except Exception as e:
            print(f"⚠️ Audio mixer cleanup failed: {e}")
        
        # Restore output streams (no TTS after mixer is gone)
        try:
            sys.stderr = self.original_stderr
            sys.stdout = self.original_stdout
            print("✅ Output streams restored")
        except Exception as e:
            print(f"⚠️ Stream restoration failed: {e}")
        
        print("=" * 100)
        print("Shutdown complete.")
        sys.exit(0)
    
    def text_input_mode(self):
        """Text input mode with screen monitoring"""
        print("Jarvis Text Assistant Ready...")
        print("Type 'shutdown' or 'shut down' to exit.")
        print("Type 'screen monitor' to enable screen capture.")
        print("=" * 100)
        
        try:
            while True:
                try:
                    current_text = input("You: ").strip()
                except EOFError:
                    break
                
                if not current_text:
                    continue
                    
                print(f"User: {current_text}")
                
                # Check for shutdown
                if "shutdown" in current_text.lower() or "shut down" in current_text.lower():
                    self.cleanup_and_exit()
                if any(hot_word in current_text.lower() for hot_word in self.hot_words) or self.skip_hot_word_check:
                    if current_text:
                        # Check for screen monitoring commands
                        if utils.start_screen_monitor(current_text):
                            if not self.screen_monitor.monitoring:
                                self.screen_monitor.start_monitoring()
                                utils.tts_caller("Go ahead and give me a command")
                            else:
                                response = "Screen monitoring is already active, Sir."
                                print(f"Jarvis: {response}")
                                utils.tts_caller(response)
                            self.skip_hot_word_check = True
                            
                        # Natural screen analysis commands
                        elif self.screen_monitor.monitoring and self.screen_monitor.should_analyze_screen(current_text):
                            request_type = self.screen_monitor.detect_request_type(current_text)
                            self.screen_monitor.process_screen_request(self.conversation_history, request_type, current_text)
                            self.skip_hot_word_check = True
                            
                        elif utils.stop_screen_monitor(current_text):
                            self.screen_monitor.stop_monitoring()
                            self.skip_hot_word_check = True
                            
                        else:
                            # Process the regular request
                            current_text = current_text + " " + time.strftime("%Y-%m-%d %H-%M-%S")
                            response = utils.ask_question_memory(current_text, self.conversation_history)
                            
                            # Split response and speech
                            speech = response.split('#')[0]
                            print(f"Jarvis: {speech}")
                            
                            # Play TTS
                            utils.tts_caller(speech)
                            
                            # Check if we should skip hot word check next time
                            self.skip_hot_word_check = True if "?" in response else False
                else:
                    self.text_input_counter += 1
                    if self.text_input_counter == 10:
                        print("Jarvis: I'm listening for a hot word to activate...")
                
        except KeyboardInterrupt:
            self.cleanup_and_exit()
    
    def speech_input_mode(self):
        """Speech input mode with screen monitoring"""
        if not STT_AVAILABLE:
            print("Speech to text not available, falling back to text mode")
            return self.text_input_mode()
            
        self.recorder = AudioToTextRecorder(
            spinner=False, 
            model="tiny.en", 
            language="en", 
            post_speech_silence_duration=0.5, 
            silero_sensitivity=0.6
        )
        
        print("Jarvis Is Listening . . .")
        print("Say 'screen monitor' to enable screen capture.")
        
        try:
            while True:
                current_text = self.recorder.text()
                print(current_text)
                if "shutdown" in current_text.lower() or "shut down" in current_text.lower():
                    self.cleanup_and_exit()
                if any(hot_word in current_text.lower() for hot_word in self.hot_words) or self.skip_hot_word_check:
                    if current_text:
                        print("User: " + current_text)
                        self.recorder.stop()
                        
                        if "shutdown" in current_text.lower() or "shut down" in current_text.lower():
                            self.cleanup_and_exit()
                        
                        # Screen monitoring commands
                        elif utils.start_screen_monitor(current_text):
                            if not self.screen_monitor.monitoring:
                                self.screen_monitor.start_monitoring()
                                utils.tts_caller("Go ahead and give me a command")
                            else:
                                response = "Screen monitoring is already active, Sir."
                                utils.tts_caller(response)
                            self.skip_hot_word_check = True
                            self.recorder.start()
                            
                        # Natural screen analysis commands
                        elif self.screen_monitor.monitoring and self.screen_monitor.should_analyze_screen(current_text):
                            request_type = self.screen_monitor.detect_request_type(current_text)
                            self.screen_monitor.process_screen_request(self.conversation_history, request_type, current_text)
                            self.skip_hot_word_check = True
                            self.recorder.start()
                            
                        elif utils.stop_screen_monitor(current_text):
                            self.screen_monitor.stop_monitoring()
                            self.skip_hot_word_check = True
                            self.recorder.start()
                            
                        else:
                            current_text = current_text + " " + time.strftime("%Y-%m-%d %H-%M-%S")
                            response = utils.ask_question_memory(current_text, self.conversation_history)
                            print(response)
                            speech = response.split('#')[0]
                            utils.tts_caller(speech)
                            self.skip_hot_word_check = True if "?" in response else False
                            self.recorder.start()
                
        except KeyboardInterrupt:
            self.cleanup_and_exit()
    
    def run(self):
        """Main entry point"""
        if STT_AVAILABLE:
            print("RealtimeSTT detected - Using speech input mode")
            self.speech_input_mode()
        else:
            print("RealtimeSTT not available - Using text input mode")
            self.text_input_mode()

if __name__ == '__main__':
    app = JarvisApp()
    app.run()