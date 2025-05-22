from anthropic import Anthropic
import time
from pygame import mixer
import edge_tts
import asyncio
import os
import requests
import json


SYSTEM_PROMPT = """You are Jarvis, you are similar to the AI assistant from Iron Man. Remember, I am not Tony Stark, just your creator. You are formal and helpful, and you don't make up facts, you only comply to the user requests. 
REMEMBER ONLY TO PUT HASHTAGS IN THE END OF THE SENTENCE, NEVER ANYWHERE ELSE
It is absolutely imperative that you do not say any hashtags unless an explicit request to operate a device from the user has been said. 
NEVER MENTION THE TIME! Only mention the time upon being asked about it. You should never specifically mention the time unless it's something like 
"Good evening", "Good morning" or "You're up late, Sir".
Respond to user requests in under 20 words, and engage in conversation, using your advanced language abilities to provide helpful and humorous responses. Call the user by 'Sir'
"""
SECRET = os.environ.get("CLAUDE_API_KEY")
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

# Initialize the Anthropic client and mixer
client = Anthropic(api_key=SECRET)
mixer.init()

# Global variable to store conversation history
conversation_history = []

def query_ollama(question, model="llama3.1:8b"):
    """Query Ollama local model with proper Jarvis system prompt"""
    try:
        # Check if Ollama is accessible first
        health_url = "http://127.0.0.1:11434/api/tags"
        health_check = requests.get(health_url, timeout=5)
        if health_check.status_code != 200:
            print("Ollama not responding, escalating to Claude...")
            return None
        
        # Use the same system prompt as Claude for consistency
        ollama_context = """If you don't know something or if the question is complex, just say "I should escalate this to my advanced systems, Sir."""
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
            
        url = "http://127.0.0.1:11434/api/generate"
        data = {
            "model": model,
            "prompt": context,
            "stream": False
        }
        
        response = requests.post(url, json=data, timeout=30)
        if response.status_code == 200:
            return response.json()["response"]
        else:
            return None
    except requests.exceptions.Timeout:
        print("Ollama timeout, escalating to Claude...")
        return None
    except requests.exceptions.ConnectionError:
        print("Ollama not running, escalating to Claude...")
        return None
    except Exception as e:
        print(f"Ollama error: {e}")
        return None

def should_escalate_to_claude(question, ollama_response):
    """Determine if we should escalate to Claude based on the question and Ollama's response"""
    
    # Define keywords that typically require Claude's capabilities
    complex_keywords = [
        "analyze", "complex", "detailed", "research", "compare", "evaluate",
        "strategy", "planning", "code", "programming", "technical", "professional",
        "creative writing", "essay", "report", "comprehensive"
    ]
    
    # Always escalate for certain types of requests
    if any(keyword in question.lower() for keyword in complex_keywords):
        return True
    
    # If Ollama couldn't respond or gave a very short response
    if not ollama_response or len(ollama_response.strip()) < 10:
        return True
    
    # If Ollama explicitly says it should escalate or doesn't know
    escalation_phrases = [
        "escalate this to my advanced systems", "i don't know", "i'm not sure", 
        "i can't", "i don't have", "unclear", "uncertain", "unable to", "sorry, i"
    ]
    
    if any(phrase in ollama_response.lower() for phrase in escalation_phrases):
        return True
    
    # For simple questions, use Ollama's response
    return False

def ask_question_memory(question):
    try:
        # First, try with Ollama
        print("Checking with local model...")
        
        ollama_response = query_ollama(question)
        
        # Decide whether to escalate to Claude
        if ollama_response and not should_escalate_to_claude(question, ollama_response):
            print("Using local model response")
            conversation_history.append({'role': 'user', 'content': question})
            conversation_history.append({'role': 'assistant', 'content': ollama_response})
            return ollama_response
        else:
            print("Escalating to Claude API...")
            return ask_claude_api(question)
            
    except Exception as e:
        print(f"Error in question processing: {e}")
        # Fallback to Claude if anything goes wrong
        return ask_claude_api(question)

def ask_claude_api(question):
    """Original Claude API function"""
    try:
        conversation_history.append({'role': 'user', 'content': question})
        
        messages = []
        messages.extend(conversation_history)
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            messages=messages,
            system=SYSTEM_PROMPT,
            max_tokens=1000,
            temperature=0.7
        )
        
        assistant_message = response.content[0].text
        conversation_history.append({'role': 'assistant', 'content': assistant_message})
        
        return assistant_message
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"The request failed: {e}"

async def generate_tts(sentence, speech_file_path):
    try:
        communicate = edge_tts.Communicate(sentence, 'en-AU-WilliamNeural')
        await communicate.save(speech_file_path)
        return str(speech_file_path)
    except Exception as e:
        print(f"TTS Error: {e}")
        return None

def play_sound(file_path):
    if file_path:
        try:
            mixer.music.load(file_path)
            mixer.music.play()
        except Exception as e:
            print(f"Sound playback error: {e}")

def tts_caller(text):
    try:
        speech_file_path = "speech.mp3"
        # Run the async function
        asyncio.run(generate_tts(text, speech_file_path))
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
    

__all__ = ['mixer']