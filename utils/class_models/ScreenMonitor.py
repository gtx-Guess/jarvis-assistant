import time
import pyautogui
import pytesseract
from utils import utils

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

        jarvis_response = "You can ask me to analyze, explain, debug, or review any code on your screen. You can also specify line numbers if needed."
        utils.tts_caller(jarvis_response)
        
    def stop_monitoring(self):
        """Stop screen monitoring"""
        if not self.monitoring:
            return
            
        self.monitoring = False
        print("✅ Screen monitor stopped")
        
        response = "Screen monitoring disabled, Sir."
        print(f"Jarvis: {response}")
        utils.tts_caller(response)