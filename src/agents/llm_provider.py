import os
import requests

import requests
import os
from google import genai


class LLMProvider:
    def __init__(self, provider=None):
        self.default_provider = provider or os.getenv("LLM_PROVIDER", "openrouter")

    def get_config(self, provider=None):
        provider = provider or self.default_provider
        # Special handling for local Ollama
        if provider == "ollama":
            api_key = "ollama"  # Not used, but required for interface
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1/chat/completions")
            model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        else:
            api_key = os.getenv(f"{provider.upper()}_API_KEY")
            base_url = os.getenv(f"{provider.upper()}_BASE_URL")
            model = os.getenv(f"{provider.upper()}_MODEL")
        return provider, api_key, base_url, model

    def chat(self, messages, temperature=0.2, max_tokens=512, provider=None):
        """
        Provider-agnostic chat interface. Supports Gemini, Groq, OpenRouter. Others raise NotImplementedError.
        messages: list of dicts with 'role' and 'content'.
        """
        provider, api_key, base_url, model = self.get_config(provider)
        if provider == "gemini":
            prompt = "\n".join([m["content"] for m in messages if m["role"] in ("system", "user")])
            try:
                from google import genai
                client = genai.Client()
                response = client.models.generate_content(
                    model=model,
                    contents=prompt
                )
                return response.text
            except Exception as e:
                return f"[Gemini summary error: {e}]"
        elif provider == "groq":
            url = base_url or "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            try:
                resp = requests.post(url, headers=headers, json=data, timeout=60)
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]
            except Exception as e:
                return f"[Groq summary error: {e}]"
        elif provider == "openrouter" or provider == "ollama":
            url = base_url or ("http://localhost:11434/v1/chat/completions" if provider == "ollama" else "https://openrouter.ai/api/v1/chat/completions")
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            try:
                resp = requests.post(url, headers=headers, json=data, timeout=60)
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]
            except Exception as e:
                return f"[{provider.capitalize()} summary error: {e}]"
        elif provider == "langsmith":
            raise NotImplementedError("LangSmith chat integration not implemented.")
        elif provider == "azure":
            raise NotImplementedError("Azure chat integration not implemented.")
        else:
            raise NotImplementedError(f"Provider {provider} not supported for chat().")

    def summarize(self, section_text, provider=None, max_tokens=256):
        messages = [
            {"role": "system", "content": "You are a helpful assistant that summarizes document sections for navigation."},
            {"role": "user", "content": f"Summarize the following section in 2-3 sentences for a navigation tree:\n{section_text}"}
        ]
        return self.chat(messages, temperature=0.2, max_tokens=max_tokens, provider=provider)
