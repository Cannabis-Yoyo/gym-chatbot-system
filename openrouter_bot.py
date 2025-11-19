import requests
import json
from config import Config

# Alias for backward compatibility
GeminiBot = None

class OpenRouterBot:
    def __init__(self):
        self.api_key = Config.OPENROUTER_API_KEY
        self.model = Config.MODEL_NAME
        self.temperature = Config.TEMPERATURE
        self.max_tokens = Config.MAX_TOKENS
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
    
    def get_response(self, prompt, context=""):
        try:
            full_prompt = f"{context}\n\n{prompt}" if context else prompt
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000",  # Optional
                "X-Title": "Gym Chatbot System"  # Optional
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'choices' in data and len(data['choices']) > 0:
                    message = data['choices'][0].get('message', {})
                    content = message.get('content', '')
                    
                    if content:
                        return content.strip()
                    else:
                        return "I received an empty response. Please try again."
                else:
                    return "I couldn't generate a response. Please try rephrasing your question."
            
            elif response.status_code == 429:
                return "Rate limit exceeded. Please wait a moment and try again."
            
            elif response.status_code == 401:
                return "Authentication error. Please check your API key."
            
            elif response.status_code == 402:
                return "Insufficient credits. Please check your OpenRouter account."
            
            else:
                error_msg = f"API request failed with status {response.status_code}"
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_msg += f": {error_data['error'].get('message', 'Unknown error')}"
                except:
                    pass
                return error_msg
                
        except requests.exceptions.Timeout:
            return "Request timed out. Please try again."
        
        except requests.exceptions.ConnectionError:
            return "Connection error. Please check your internet connection."
        
        except Exception as e:
            error_msg = str(e).lower()
            
            if 'timeout' in error_msg:
                return "Request timed out. Please try again."
            elif 'connection' in error_msg:
                return "Connection error. Please check your internet connection."
            else:
                print(f"Error details: {str(e)}")
                return "I encountered an error. Please try again with a simpler question."