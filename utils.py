from anthropic import Anthropic
import time
from pygame import mixer
import edge_tts
import asyncio
import os

SECRET = os.environ.get("CLAUDE_API_KEY")
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

# Initialize the Anthropic client and mixer
client = Anthropic(api_key=SECRET)  # Replace with your API key
mixer.init()

# Global variable to store conversation history
conversation_history = []

def ask_question_memory(question):
    try:
        system_message = """
                            You are Jarvis, you are similiar to the AI assistant from Iron Man. Remember, I am not Tony Stark, just your creator. You are formal and helpful, and you don't make up facts, you only comply to the user requests. 
                            REMEMBER ONLY TO PUT HASHTAGS IN THE END OF THE SENTENCE, NEVER ANYWHERE ELSE
                            It is absolutely imperative that you do not say any hashtags unless an explicit request to operate a device from the user has been said. 
                            NEVER MENTION THE TIME! Only mention the time upon being asked about it. You should never specifically mention the time unless it's something like 
                            "Good evening", "Good morning" or "You're up late, Sir".
                            Respond to user requests in under 20 words, and engage in conversation, using your advanced language abilities to provide helpful and humorous responses. Call the user by 'Sir'
                        """

        conversation_history.append({'role': 'user', 'content': question})
        
        messages = []
        messages.extend(conversation_history)
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            messages=messages,
            system=system_message,
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