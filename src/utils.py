import os
import logging
from typing import Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def generate_text(self, prompt: str, system_prompt: str = "") -> str:
        pass

class GroqLLMProvider(BaseLLMProvider):
    """Groq API provider (recommended - free and fast)"""
    
    def __init__(self):
        try:
            from groq import Groq
            
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in environment variables")
            
            self.client = Groq(api_key=api_key)
            self.model = "mixtral-8x7b-32768"
            logger.info("Groq LLM provider initialized")
        except ImportError:
            raise ImportError("groq package not installed. Run: pip install groq")
        except Exception as e:
            logger.error(f"Error initializing Groq: {e}")
            raise
    
    def generate_text(self, prompt: str, system_prompt: str = "") -> str:
        """Generate text using Groq API"""
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                messages=messages,
                model=self.model,
                temperature=0.7,
                max_tokens=1024,
                top_p=1,
                stream=False,
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating text with Groq: {e}")
            raise

class HuggingFaceLLMProvider(BaseLLMProvider):
    """HuggingFace Inference API provider"""
    
    def __init__(self):
        try:
            from huggingface_hub import InferenceClient
            
            api_key = os.getenv("HUGGINGFACE_API_KEY")
            if not api_key:
                raise ValueError("HUGGINGFACE_API_KEY not found in environment variables")
            
            self.client = InferenceClient(
                model="mistralai/Mistral-7B-Instruct-v0.1",
                token=api_key
            )
            logger.info("HuggingFace LLM provider initialized")
        except ImportError:
            raise ImportError("huggingface-hub package not installed")
        except Exception as e:
            logger.error(f"Error initializing HuggingFace: {e}")
            raise
    
    def generate_text(self, prompt: str, system_prompt: str = "") -> str:
        """Generate text using HuggingFace API"""
        try:
            full_prompt = f"{system_prompt}\n{prompt}" if system_prompt else prompt
            
            response = self.client.text_generation(
                full_prompt,
                max_new_tokens=1024,
                temperature=0.7,
                top_p=0.95,
            )
            
            return response
        except Exception as e:
            logger.error(f"Error generating text with HuggingFace: {e}")
            raise

class OllamaLLMProvider(BaseLLMProvider):
    """Local Ollama provider (requires local Ollama instance)"""
    
    def __init__(self, model: str = "mistral"):
        try:
            import requests
            
            self.base_url = "http://localhost:11434"
            self.model = model
            
            # Test connection
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                raise ConnectionError("Cannot connect to Ollama. Make sure Ollama is running.")
            
            logger.info(f"Ollama provider initialized with model: {model}")
        except ImportError:
            raise ImportError("requests package not installed")
        except Exception as e:
            logger.error(f"Error initializing Ollama: {e}")
            raise
    
    def generate_text(self, prompt: str, system_prompt: str = "") -> str:
        """Generate text using local Ollama"""
        try:
            import requests
            
            full_prompt = f"{system_prompt}\n{prompt}" if system_prompt else prompt
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                },
                timeout=300
            )
            
            if response.status_code == 200:
                return response.json()['response']
            else:
                raise Exception(f"Ollama error: {response.text}")
        except Exception as e:
            logger.error(f"Error generating text with Ollama: {e}")
            raise

def create_llm_provider(provider_name: str) -> BaseLLMProvider:
    """Factory function to create appropriate LLM provider"""
    
    provider_name = provider_name.lower().strip()
    
    if provider_name in ["groq", "groq-api"]:
        return GroqLLMProvider()
    elif provider_name in ["huggingface", "hf"]:
        return HuggingFaceLLMProvider()
    elif provider_name in ["ollama", "local"]:
        return OllamaLLMProvider()
    else:
        raise ValueError(f"Unknown provider: {provider_name}")