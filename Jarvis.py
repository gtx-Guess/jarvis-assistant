import os
import sys
import pyautogui
import pytesseract
import time

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

class ScreenMonitor:
    def __init__(self):
        self.monitoring = False
        self.last_capture_time = 0
        self.capture_cooldown = 2  # Prevent spam captures
        
    def should_analyze_screen(self, text):
        """Determine if the user is asking for screen analysis"""
        text_lower = text.lower()
        
        # Direct screen analysis requests
        screen_triggers = [
            "analyze this code", "look at this code", "review this code", 
            "explain this code", "debug this code", "check this code",
            "what does this code do", "is this code correct", "fix this code",
            "improve this code", "optimize this code", "refactor this code",
            "look at line", "analyze line", "check line", "review line",
            "what's wrong with this", "help me with this code", "thoughts on this code"
        ]
        
        return any(trigger in text_lower for trigger in screen_triggers)
    
    def detect_request_type(self, text):
        """Detect what type of analysis the user wants"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["explain", "what does", "what is"]):
            return "explain"
        elif any(word in text_lower for word in ["debug", "fix", "wrong", "error", "bug"]):
            return "debug"
        elif any(word in text_lower for word in ["review", "check", "correct", "validate"]):
            return "review"
        elif any(word in text_lower for word in ["improve", "optimize", "better", "refactor", "suggest"]):
            return "suggest"
        else:
            return "analyze"  # Default
    
    def extract_line_numbers(self, text):
        """Extract line number ranges from text like 'lines 345-380' or 'line 50'"""
        import re
        
        # Look for patterns like "line 50", "lines 345-380", "lines 10 to 20"
        line_patterns = [
            r'lines?\s*(\d+)(?:\s*[-to]+\s*(\d+))?',  # "line 50" or "lines 345-380"
            r'from\s+line\s*(\d+)\s*to\s*line\s*(\d+)',  # "from line 10 to line 20"
        ]
        
        for pattern in line_patterns:
            match = re.search(pattern, text.lower())
            if match:
                start_line = int(match.group(1))
                end_line = int(match.group(2)) if match.group(2) else start_line
                return start_line, end_line
        
        return None, None
        
    def capture_screen(self, region=None):
        """Capture screen and extract text using OCR"""
        try:
            # Add small delay to prevent accidental captures
            current_time = time.time()
            if current_time - self.last_capture_time < self.capture_cooldown:
                print("🕐 Please wait before capturing again...")
                return None
                
            self.last_capture_time = current_time
            
            print("📸 Capturing screen...")
            
            # Take screenshot
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()
            
            # Extract text using OCR
            print("🔍 Extracting text from image...")
            text = pytesseract.image_to_string(screenshot)
            
            if not text.strip():
                print("❌ No text found in captured area")
                return None
                
            print(f"✅ Extracted {len(text)} characters")
            return text
            
        except Exception as e:
            print(f"❌ Screen capture error: {e}")
            return None
    
    def process_screen_request(self, request_type="analyze", original_text=""):
        """Process screen capture with specific request type"""
        captured_text = self.capture_screen()
        
        if not captured_text:
            response = "I couldn't capture any code from your screen, Sir."
            print(f"Jarvis: {response}")
            utils.tts_caller(response)
            return
            
        # Check for line number specifications
        start_line, end_line = self.extract_line_numbers(original_text)
        
        # Create context-aware prompt
        if start_line and end_line:
            if start_line == end_line:
                line_context = f"focusing specifically on line {start_line}"
            else:
                line_context = f"focusing specifically on lines {start_line} to {end_line}"
        else:
            line_context = ""
            
        prompts = {
            "analyze": f"Please analyze this code I'm looking at {line_context} and tell me if it makes sense or suggest improvements:\n\n{captured_text}",
            "explain": f"Please explain what this code does {line_context}:\n\n{captured_text}",
            "review": f"Please review this code {line_context} for potential bugs or issues:\n\n{captured_text}",
            "suggest": f"Please suggest improvements for this code {line_context}:\n\n{captured_text}",
            "debug": f"Help me debug this code {line_context} - what might be wrong:\n\n{captured_text}"
        }
        
        prompt = prompts.get(request_type, prompts["analyze"])
        
        # Add timestamp and send to your existing AI system
        timestamped_prompt = prompt + " " + time.strftime("%Y-%m-%d %H-%M-%S")
        
        print(f"🤖 Processing screen capture with {request_type} request...")
        response = utils.ask_question_memory(timestamped_prompt)
        
        # Split response and speech (keeping your existing format)
        speech = response.split('#')[0]
        print(f"Jarvis: {speech}")
        
        # Play TTS
        utils.tts_caller(speech)
    
    def start_monitoring(self):
        """Start the screen monitoring"""
        if self.monitoring:
            return
            
        self.monitoring = True
        print("🎯 Screen monitoring active - Natural commands available:")
        print("   'Can you analyze this code?'")
        print("   'Look at this code and explain it'") 
        print("   'Review this code for bugs'")
        print("   'What does this code do?'")
        print("   'Debug this code'")
        print("   'Look at lines 50-75'")
        print("   'Check line 42'")
        
    def stop_monitoring(self):
        """Stop screen monitoring"""
        if not self.monitoring:
            return
            
        self.monitoring = False
        print("🛑 Screen monitoring stopped")
        
        response = "Screen monitoring disabled, Sir."
        print(f"Jarvis: {response}")
        utils.tts_caller(response)


def text_input_mode():
    """Enhanced text input mode with screen monitoring"""
    hot_words = ["jarvis", "?", "shutdown", "shut down", "right", "correct", "could I", "is it possible", "can I", "listen up", "screen", "monitor", "analyze", "look at", "review", "explain", "debug"]
    skip_hot_word_check = False
    screen_monitor = ScreenMonitor()
    
    print("Jarvis Text Assistant Ready...")
    print("Type 'shutdown' or 'shut down' to exit.")
    print("Type 'screen monitor' to enable screen capture.")
    print("=" * 100)
    text_input_counter = 0
    
    try:
        while True:
            # Get text input from user
            try:
                current_text = input("You: ").strip()
            except EOFError:
                break
            
            if not current_text:
                continue
                
            print(f"User: {current_text}")
            
            # Check for hot words or if we're in skip mode
            if any(hot_word in current_text.lower() for hot_word in hot_words) or skip_hot_word_check:
                if current_text:
                    # Check for shutdown command
                    if "shutdown" in current_text.lower() or "shut down" in current_text.lower():
                        screen_monitor.stop_monitoring()
                        goodbye = "Shutting down now, Sir. Goodbye."
                        try:
                            print(f"Jarvis: {goodbye}")
                            utils.tts_caller(goodbye)
                        finally:
                            mixer.quit()
                            print("=" * 100)
                            return
                    
                    # Check for screen monitoring commands
                    elif "screen monitor" in current_text.lower():
                        if not screen_monitor.monitoring:
                            screen_monitor.start_monitoring()
                            response = "Screen monitoring enabled, Sir. I can now analyze your code when you ask."
                        else:
                            response = "Screen monitoring is already active, Sir."
                        print(f"Jarvis: {response}")
                        utils.tts_caller(response)
                        skip_hot_word_check = True
                        
                    # Natural screen analysis commands
                    elif screen_monitor.monitoring and screen_monitor.should_analyze_screen(current_text):
                        request_type = screen_monitor.detect_request_type(current_text)
                        screen_monitor.process_screen_request(request_type, current_text)
                        skip_hot_word_check = True
                        
                    elif "stop monitor" in current_text.lower() or "disable monitor" in current_text.lower():
                        screen_monitor.stop_monitoring()
                        skip_hot_word_check = True
                        
                    else:
                        # Process the regular request
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
        screen_monitor.stop_monitoring()
        mixer.quit()
        print("Goodbye!")
        print("=" * 100)


def speech_input_mode():
    """Enhanced speech input mode with screen monitoring"""
    recorder = AudioToTextRecorder(spinner=False, model="tiny.en", language="en", post_speech_silence_duration=0.5, silero_sensitivity=0.6)
    hot_words = ["jarvis", "?", "shutdown", "shut down", "right", "correct", "could I", "is it possible", "can I", "listen up", "screen", "monitor", "analyze", "look at", "review", "explain", "debug"]
    skip_hot_word_check = False
    screen_monitor = ScreenMonitor()
    
    print("Jarvis Is Listening . . .")
    print("Say 'screen monitor' to enable screen capture.")
    
    try:
        while True:
            current_text = recorder.text()
            print(current_text)
            if any(hot_word in current_text.lower() for hot_word in hot_words) or skip_hot_word_check:
                if current_text:
                    print("User: " + current_text)
                    recorder.stop()
                    
                    if "shutdown" in current_text.lower() or "shut down" in current_text.lower():
                        screen_monitor.stop_monitoring()
                        goodbye = "Shutting down now, Sir. Goodbye."
                        try:
                            utils.tts_caller(goodbye)
                        finally:
                            recorder.stop()
                            mixer.quit()
                            print("=" * 100)
                            os._exit(0)
                    
                    # Screen monitoring commands
                    elif "screen monitor" in current_text.lower():
                        if not screen_monitor.monitoring:
                            screen_monitor.start_monitoring()
                            response = "Screen monitoring enabled, Sir. I can now analyze your code when you ask."
                        else:
                            response = "Screen monitoring is already active, Sir."
                        utils.tts_caller(response)
                        skip_hot_word_check = True
                        recorder.start()
                        
                    # Natural screen analysis commands
                    elif screen_monitor.monitoring and screen_monitor.should_analyze_screen(current_text):
                        request_type = screen_monitor.detect_request_type(current_text)
                        screen_monitor.process_screen_request(request_type, current_text)
                        skip_hot_word_check = True
                        recorder.start()
                        
                    elif "stop monitor" in current_text.lower() or "disable monitor" in current_text.lower():
                        screen_monitor.stop_monitoring()
                        skip_hot_word_check = True
                        recorder.start()
                        
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
        screen_monitor.stop_monitoring()
        recorder.stop()
        mixer.quit()
        sys.stderr = stderr
        os.exit(0)


if __name__ == '__main__':
    # debug_model_access()
    if STT_AVAILABLE:
        print("RealtimeSTT detected - Using speech input mode")
        speech_input_mode()
    else:
        print("RealtimeSTT not available - Using text input mode")
        text_input_mode()