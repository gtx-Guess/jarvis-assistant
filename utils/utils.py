from anthropic import Anthropic
from openai import OpenAI
from dotenv import load_dotenv
import time
from pygame import mixer
import edge_tts
import asyncio
import os
import requests
import json

load_dotenv()

def load_escalation_keywords():
    try:
        with open('utils/escalation_keywords.json', 'r') as f:
            keywords_dict = json.load(f)
            
            # Flatten all categories into one list at load time
            all_keywords = []
            for category in keywords_dict.values():
                all_keywords.extend(category)
                
            return keywords_dict, all_keywords
            
    except FileNotFoundError:
        print("⚠️ escalation_keywords.json not found, using basic fallback")
        fallback = {
            "programming": ["code", "python", "javascript"],
            "complex_analysis": ["analyze", "research"]
        }
        all_keywords = ["code", "python", "javascript", "analyze", "research"]
        return fallback, all_keywords

# Load once at startup
ESCALATION_KEYWORDS, ALL_ESCALATION_KEYWORDS = load_escalation_keywords()

def should_escalate_immediately(question):
    """Fast keyword check using pre-built list"""
    question_lower = question.lower()
    return any(keyword in question_lower for keyword in ALL_ESCALATION_KEYWORDS)

# Environment variable configuration
USE_OPENAI_ENV = os.environ.get("USE_OPENAI", "true").lower()
USE_OPENAI = USE_OPENAI_ENV in ["true", "1", "yes", "on"]

# Audio configuration with smart detection
ENABLE_AUDIO = os.environ.get("ENABLE_AUDIO", "auto").lower()
AUDIO_AVAILABLE = False

# Try to import RealtimeSTT only if audio is enabled and available
if ENABLE_AUDIO in ["true", "auto"]:
    try:
        from RealtimeSTT import AudioToTextRecorder
        AUDIO_AVAILABLE = True
        print("🎤 Audio input available")
    except ImportError:
        AUDIO_AVAILABLE = False
        if ENABLE_AUDIO == "true":
            print("⚠️ Audio input not available (RealtimeSTT not installed)")
        else:
            print("📝 Text-only mode (audio dependencies not found)")
    except Exception as e:
        AUDIO_AVAILABLE = False
        if ENABLE_AUDIO == "true":
            print(f"⚠️ Audio input failed to initialize: {e}")

SYSTEM_PROMPT = """You are Jarvis, you are similar to the AI assistant from Iron Man. Remember, I am not Tony Stark, just your creator. 
You are formal and helpful, and you don't make up facts, you only comply to the user requests. 
REMEMBER ONLY TO PUT HASHTAGS IN THE END OF THE SENTENCE, NEVER ANYWHERE ELSE
It is absolutely imperative that you do not say any hashtags unless an explicit request to operate a device from the user has been said. 
NEVER MENTION THE TIME! Only mention the time upon being asked about it. 
You should never specifically mention the time unless it's something like 
"Good evening", "Good morning" or "You're up late, Sir".
Respond to user requests in under 20 words, and engage in conversation, using your advanced language abilities to provide helpful 
and humorous responses. Call the user by 'Sir'
"""

# API Keys and Configuration
CLAUDE_SECRET = os.environ.get("CLAUDE_API_KEY")
OPENAI_SECRET = os.environ.get("OPENAI_API_KEY")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

# Initialize the appropriate client
if USE_OPENAI:
    client = OpenAI(api_key=OPENAI_SECRET)
    MODEL_NAME = "gpt-4o"
    print(f"Using OpenAI with model: {MODEL_NAME}")
else:
    client = Anthropic(api_key=CLAUDE_SECRET)
    MODEL_NAME = "claude-sonnet-4-20250514"
    print(f"Using Anthropic with model: {MODEL_NAME}")

# Safe mixer initialization
try:
    mixer.init()
    AUDIO_OUTPUT_AVAILABLE = True
    print("🔊 Audio output initialized")
except Exception as e:
    AUDIO_OUTPUT_AVAILABLE = False
    print(f"🔇 Audio output not available: {e}")
    print("📝 TTS will be disabled - text responses only")

def get_input_mode():
    """Determine if we should use audio or text input"""
    if not AUDIO_AVAILABLE:
        return "text"
    
    if ENABLE_AUDIO == "false":
        return "text"
    
    if ENABLE_AUDIO in ["true", "auto"]:
        # Check if we're actually in an environment that supports audio
        try:
            # Simple test - try to initialize audio recorder
            recorder = AudioToTextRecorder(spinner=False, model="tiny.en", language="en")
            recorder.stop()  # Clean up immediately
            print("🎤 Audio hardware detected - voice input available")
            return "audio"
        except Exception as e:
            print(f"🔇 Audio hardware not available: {e}")
            print("📝 Falling back to text input mode")
            return "text"
    
    return "text"

def query_ollama(question, conversation_history, model=None):
    """Query Ollama local model with proper Jarvis system prompt"""
    if model is None:
        model = OLLAMA_MODEL
        
    start_time = time.time()
    
    try:
        # Check if Ollama is accessible first
        health_url = f"{OLLAMA_BASE_URL}/api/tags"
        health_check = requests.get(health_url, timeout=5)
        if health_check.status_code != 200:
            elapsed = time.time() - start_time
            provider = "OpenAI" if USE_OPENAI else "Claude"
            print(f"❌ Ollama not responding after {elapsed:.2f}s, escalating to {provider}...")
            return None
        
        # Use the same system prompt as Claude for consistency
        ollama_context = """If you don't know something or if the question is complex, just say "I should escalate this to my advanced systems, Sir." You are allowed to mention which model is being ran in ollama. For example, qwen2.5:7b or llama3.2 but only when asked."""
        # Build conversation context
        context = SYSTEM_PROMPT + ollama_context + "\n\n"
        
        # Add recent conversation history (last 4 messages to keep it manageable)
        recent_history = conversation_history[-4:] if len(conversation_history) > 4 else conversation_history
        
        for msg in recent_history:
            if msg['role'] == 'user':
                context += f"User: {msg['content']}\n"
            else:
                context += f"Jarvis: {msg['content']}\n"
        
        # Add current question
        context += f"User: {question}\nJarvis:"
        
        # Time the actual inference
        inference_start = time.time()
        url = f"{OLLAMA_BASE_URL}/api/generate"
        data = {
            "model": model,
            "prompt": context,
            "stream": False
        }
        
        response = requests.post(url, json=data, timeout=30)
        inference_end = time.time()
        
        if response.status_code == 200:
            total_time = time.time() - start_time
            inference_time = inference_end - inference_start
            overhead_time = total_time - inference_time
            
            # Log timing information
            print(f"🤖 Ollama Timing:")
            print(f"   Total time: {total_time:.2f}s")
            print(f"   Inference time: {inference_time:.2f}s") 
            print(f"   Overhead time: {overhead_time:.2f}s")
            print(f"   Model: {model}")
            print(f"   Location: Remote ({OLLAMA_BASE_URL})")
            
            return response.json()["response"]
        else:
            elapsed = time.time() - start_time
            print(f"❌ Ollama failed after {elapsed:.2f}s (Status: {response.status_code})")
            return None
            
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        provider = "OpenAI" if USE_OPENAI else "Claude"
        print(f"⏰ Ollama timeout after {elapsed:.2f}s, escalating to {provider}...")
        return None
    except requests.exceptions.ConnectionError:
        elapsed = time.time() - start_time
        provider = "OpenAI" if USE_OPENAI else "Claude"
        print(f"🔌 Ollama connection failed after {elapsed:.2f}s, escalating to {provider}...")
        return None
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"💥 Ollama error after {elapsed:.2f}s: {e}")
        return None

def should_escalate_to_cloud(question, ollama_response=None):
    
    # If no ollama response yet, don't escalate based on question alone
    if ollama_response is None:
        return False
        
    # Escalate if ollama explicitly says to escalate
    escalation_phrases = ["escalate this to my advanced systems", "i don't know"]
    if any(phrase in ollama_response.lower() for phrase in escalation_phrases):
        return True
        
    # Escalate if response seems incomplete/unhelpful
    if len(ollama_response.strip()) < 5 or "i can't" in ollama_response.lower():
        return True
        
    return False

def ask_question_memory(question, conversation_history):
    total_start_time = time.time()
    
    try:
        skip_llama = False
        if should_escalate_immediately(question): 
            skip_llama = True
            print(f"🔥 API hot word detected, skipping local model")
        else:
            print("Checking with local model...")
            ollama_response = query_ollama(question, conversation_history)
        
        if not skip_llama and ollama_response and not should_escalate_to_cloud(question, ollama_response):
            total_time = time.time() - total_start_time
            print(f"✅ Using local model response (Total: {total_time:.2f}s)")
            conversation_history.append({'role': 'user', 'content': question})
            conversation_history.append({'role': 'assistant', 'content': ollama_response})
            return ollama_response
        else:
            provider = "OpenAI" if USE_OPENAI else "Claude"
            print(f"📡 Escalating to {provider} API...")
            cloud_response = ask_cloud_api(question, conversation_history)
            total_time = time.time() - total_start_time
            print(f"🌐 Total query time (including escalation): {total_time:.2f}s")
            return cloud_response
            
    except Exception as e:
        total_time = time.time() - total_start_time
        print(f"💥 Error in question processing after {total_time:.2f}s: {e}")
        # Fallback to cloud API if anything goes wrong
        return ask_cloud_api(question, conversation_history)

def ask_openai_api(question, conversation_history):
    """OpenAI API function with timing"""
    start_time = time.time()
    
    try:
        conversation_history.append({'role': 'user', 'content': question})
        
        # OpenAI format includes system message in messages array
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        messages.extend(conversation_history)
        
        # Time the actual API call
        api_start = time.time()
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
        api_end = time.time()
        
        total_time = time.time() - start_time
        api_time = api_end - api_start
        overhead_time = total_time - api_time
        
        # Log timing information
        print(f"🌐 OpenAI Timing:")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   API call time: {api_time:.2f}s")
        print(f"   Overhead time: {overhead_time:.2f}s")
        print(f"   Model: {MODEL_NAME}")
        print(f"   Location: Cloud")
        
        assistant_message = response.choices[0].message.content
        conversation_history.append({'role': 'assistant', 'content': assistant_message})
        
        return assistant_message
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ OpenAI API error after {elapsed:.2f}s: {e}")
        return f"The OpenAI request failed: {e}"

def ask_claude_api(question, conversation_history):
    """Anthropic Claude API function with timing"""
    start_time = time.time()
    
    try:
        conversation_history.append({'role': 'user', 'content': question})
        
        messages = []
        messages.extend(conversation_history)
        
        # Time the actual API call
        api_start = time.time()
        response = client.messages.create(
            model=MODEL_NAME,
            messages=messages,
            system=SYSTEM_PROMPT,
            max_tokens=1000,
            temperature=0.7
        )
        api_end = time.time()
        
        total_time = time.time() - start_time
        api_time = api_end - api_start
        overhead_time = total_time - api_time
        
        # Log timing information
        print(f"🌐 Claude Timing:")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   API call time: {api_time:.2f}s")
        print(f"   Overhead time: {overhead_time:.2f}s")
        print(f"   Model: {MODEL_NAME}")
        print(f"   Location: Cloud")
        
        assistant_message = response.content[0].text
        conversation_history.append({'role': 'assistant', 'content': assistant_message})
        
        return assistant_message
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Claude API error after {elapsed:.2f}s: {e}")
        return f"The Claude request failed: {e}"

def ask_cloud_api(question, conversation_history):
    """Router function that calls the appropriate API based on USE_OPENAI flag"""
    if USE_OPENAI:
        return ask_openai_api(question, conversation_history)
    else:
        return ask_claude_api(question, conversation_history)

async def generate_tts(sentence, speech_file_path):
    try:
        communicate = edge_tts.Communicate(sentence, 'en-AU-WilliamNeural')
        await communicate.save(speech_file_path)
        return str(speech_file_path)
    except Exception as e:
        print(f"TTS Error: {e}")
        return None

def play_sound(file_path):
    if not AUDIO_OUTPUT_AVAILABLE:
        print("🔇 Audio playback skipped (no audio hardware)")
        return
        
    if file_path:
        try:
            mixer.music.load(file_path)
            mixer.music.play()
        except Exception as e:
            print(f"Sound playback error: {e}")

def tts_caller(text: str):
    if not AUDIO_OUTPUT_AVAILABLE:
        print(f"🔇 TTS skipped: {text}")
        return "skipped"
        
    try:
        speech_file_path = "speech.mp3"
        cleaned_string = clean_up_tts_string(text)
        asyncio.run(generate_tts(cleaned_string, speech_file_path))
        if os.path.exists(speech_file_path):
            play_sound(speech_file_path)
            while mixer.music.get_busy():
                time.sleep(1)
            mixer.music.unload()
            os.remove(speech_file_path)
        return "done"
    except Exception as e:
        print(f"TTS processing error: {e}")
        return "error"

def clean_up_tts_string(text: str):
    text = text.replace("**", "")
    text = text.replace("*", "")
    text = text.replace("`", "")
    text = text.replace("##", "")
    text = text.replace("#", "") 
    return text

def debug_model_access():
    """Test what models you can actually access with timing"""
    if USE_OPENAI:
        print("Testing OpenAI models...")
        models_to_test = ["gpt-4o", "gpt-4", "gpt-3.5-turbo"]
        
        for model in models_to_test:
            start_time = time.time()
            try:
                test_client = OpenAI(api_key=OPENAI_SECRET)
                response = test_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": "What's your training cutoff date?"}],
                    max_tokens=50
                )
                elapsed = time.time() - start_time
                print(f"✅ {model}: {response.choices[0].message.content[:100]}... ({elapsed:.2f}s)")
            except Exception as e:
                elapsed = time.time() - start_time
                print(f"❌ {model}: {str(e)} ({elapsed:.2f}s)")
    else:
        print("Testing Anthropic models...")
        models_to_test = [
            "claude-sonnet-4-20250514",
            "claude-3-5-sonnet-20241022", 
            "claude-3-5-sonnet-20240620"
        ]
        
        for model in models_to_test:
            start_time = time.time()
            try:
                test_client = Anthropic(api_key=CLAUDE_SECRET)
                response = test_client.messages.create(
                    model=model,
                    messages=[{"role": "user", "content": "What's your training cutoff date?"}],
                    max_tokens=50
                )
                elapsed = time.time() - start_time
                print(f"✅ {model}: {response.content[0].text[:100]}... ({elapsed:.2f}s)")
            except Exception as e:
                elapsed = time.time() - start_time
                print(f"❌ {model}: {str(e)} ({elapsed:.2f}s)")


def start_screen_monitor(text: str):
    '''
        Checkes current_text to see if the user asked for screen monitoring to start
    '''
    start_monitoring = [
        # Direct commands
        "start monitoring",
        "start watching",
        "start screen monitor",
        "turn on monitoring",
        "turn on screen monitor",
        "screen monitor on",
        "enable monitoring",
        "enable screen monitor",
        "activate monitoring",
        "activate screen monitor",
        
        # More casual phrases
        "watch the screen",
        "monitor the screen",
        "keep an eye on the screen",
        "start screen recording",
        "begin monitoring",
        "begin watching",
        "start tracking",
        "track the screen",
        "observe the screen",
        "surveillance on",
        
        # Natural speech patterns
        "can you monitor",
        "please monitor",
        "start to monitor",
        "begin to watch",
        "keep watch",
        "watch my screen",
        "monitor my screen",
        "track my screen",
        "record my screen",
        "capture my screen",
        
        # Jarvis-style commands
        "jarvis monitor",
        "jarvis watch",
        "jarvis start monitoring",
        "jarvis screen on",
        "monitor mode on",
        "watching mode",
        "surveillance mode",
        
        # Alternative phrasings
        "switch on monitoring",
        "fire up monitoring",
        "boot up screen monitor",
        "initialize monitoring",
        "commence monitoring",
        "engage monitoring"
    ]
    
    if any(key_word in text.lower() for key_word in start_monitoring):
        return True
    return False

def stop_screen_monitor(text: str):
    '''
        Checkes current_text to see if the user asked for screen monitoring to stop
    '''
    stop_monitoring = [
        # Direct commands
        "stop monitoring",
        "stop watching",
        "stop screen monitor",
        "turn off monitoring",
        "turn off screen monitor",
        "screen monitor off",
        "disable monitoring",
        "disable screen monitor",
        "deactivate monitoring",
        "deactivate screen monitor",
        
        # More casual phrases
        "stop watching the screen",
        "stop monitoring the screen",
        "end monitoring",
        "end watching",
        "stop screen recording",
        "stop tracking",
        "stop tracking the screen",
        "stop observing",
        "surveillance off",
        "quit monitoring",
        
        # Natural speech patterns
        "stop monitoring please",
        "please stop monitoring",
        "can you stop monitoring",
        "stop watching my screen",
        "stop monitoring my screen",
        "stop tracking my screen",
        "stop recording my screen",
        "stop capturing my screen",
        
        # Jarvis-style commands
        "jarvis stop monitoring",
        "jarvis stop watching",
        "jarvis screen off",
        "monitor mode off",
        "watching mode off",
        "surveillance mode off",
        "jarvis disable monitoring",
        
        # Alternative phrasings
        "switch off monitoring",
        "shut down monitoring",
        "shut off screen monitor",
        "terminate monitoring",
        "cease monitoring",
        "halt monitoring",
        "kill monitoring",
        "cancel monitoring",
        "exit monitoring",
        "close monitoring"
    ]
    
    if any(key_word in text.lower() for key_word in stop_monitoring):
        return True
    return False

__all__ = ['mixer']