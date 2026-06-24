import os
import json
import time
import urllib.request
import urllib.error
from google import genai
from google.genai import types

class LLMClient:
    """
    A unified LLM client that prioritizes Gemini and falls back to Grok 
    if Gemini fails or rate limits.
    """
    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.grok_key = os.getenv("GROK_API_KEY")
        
        if self.gemini_key:
            self.gemini_client = genai.Client(api_key=self.gemini_key)
        else:
            self.gemini_client = None

    def analyze_lead(self, prompt: str) -> str:
        """Runs the specific prompt for LeadAnalyzer"""
        return self._generate(prompt)

    def generate_brief(self, prompt: str) -> str:
        """Runs the specific prompt for BriefGenerator"""
        return self._generate(prompt)

    def _generate(self, prompt: str) -> str:
        # Try Gemini first
        if self.gemini_client:
            for attempt in range(5):
                try:
                    response = self.gemini_client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.0
                        )
                    )
                    return response.text
                except Exception as e:
                    err_str = str(e)
                    if "429" in err_str or "503" in err_str:
                        print(f"Gemini API rate limit/unavailable (attempt {attempt+1}): waiting 15s...")
                        time.sleep(15)
                    else:
                        print(f"Gemini API failed: {e}. Falling back to Grok...")
                        break
        
        # Fallback to Grok
        if not self.grok_key:
            raise ValueError("Both Gemini and Grok failed or are missing API keys.")
            
        url = "https://api.x.ai/v1/chat/completions"
        payload = {
            "model": "grok-2-1212",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.0,
            "response_format": {"type": "json_object"}
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.grok_key}"
            },
            method="POST"
        )
        
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req) as response:
                    res_body = response.read().decode('utf-8')
                    res_json = json.loads(res_body)
                    return res_json['choices'][0]['message']['content']
            except urllib.error.HTTPError as e:
                err_msg = e.read().decode('utf-8')
                print(f"Grok API error (attempt {attempt+1}): {e.code} - {err_msg}")
                if attempt == 2:
                    raise
                time.sleep(2)
            except Exception as e:
                print(f"Grok error (attempt {attempt+1}): {e}")
                if attempt == 2:
                    raise
                time.sleep(2)
