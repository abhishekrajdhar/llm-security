import json
import asyncio
import httpx
from typing import Dict, Any, List, Optional
import time

from utils.logger import setup_logger
from utils.config import get_config

logger = setup_logger(__name__)
config = get_config()

class ModelClient:
    """Client for querying LLMs via APIs (supports OpenAI-compatible and custom endpoints)."""
    
    def __init__(self, endpoint: str, api_key: str, model_name: str, format_type: str = "openai"):
        self.endpoint = endpoint
        self.api_key = api_key
        self.model_name = model_name
        self.format_type = format_type.lower()
        self.headers = self._build_headers()

    def _build_headers(self) -> Dict[str, str]:
        if self.format_type == "gemini":
            # Gemini typically uses the key in the URL, but we'll accept it via header if supported,
            # or it's handled during request URL formatting. 
            # We'll set standard JSON headers.
            return {"Content-Type": "application/json"}
            
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        return headers

    def _build_payload(self, prompt: str, temperature: float, max_tokens: int) -> Dict[str, Any]:
        if self.format_type == "openai":
            return {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
        elif self.format_type == "gemini":
            return {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens
                }
            }
        else:
            # Fallback for generic custom endpoints
            return {
                "model": self.model_name,
                "prompt": prompt,
                "temperature": temperature,
                "max_tokens": max_tokens
            }

    def _parse_response(self, response_data: Dict[str, Any]) -> str:
        """Extract the model response text depending on the API format."""
        try:
            if self.format_type == "openai":
                return response_data.get("choices", [])[0].get("message", {}).get("content", "")
            elif self.format_type == "gemini":
                # Standard format for gemini outputs: candidates[0].content.parts[0].text
                return response_data.get("candidates", [])[0].get("content", {}).get("parts", [])[0].get("text", "")
            else:
                # Custom endpoints might return unstructured generation text or response
                if "choices" in response_data and isinstance(response_data["choices"], list):
                     return response_data["choices"][0].get("text", "")
                return response_data.get("response", response_data.get("generated_text", str(response_data)))
        except (KeyError, IndexError) as e:
            logger.error(f"Failed to parse response format. Error: {e}")
            return f"Error parsing response: {str(e)}"

    async def generate_response(self, prompt: str, temperature: float = config.default_temperature, 
                                max_tokens: int = config.default_max_tokens) -> Dict[str, Any]:
        """Send asynchronous request to the model's API."""
        payload = self._build_payload(prompt, temperature, max_tokens)
        
        start_time = time.time()
        retries = config.max_retries
        
        for attempt in range(retries):
            try:
                # Gemini generally expects the API key as a query param if not using Google ADC
                request_url = self.endpoint
                if self.format_type == "gemini" and self.api_key:
                     separator = "&" if "?" in request_url else "?"
                     request_url = f"{request_url}{separator}key={self.api_key}"

                async with httpx.AsyncClient(timeout=config.timeout_seconds) as client:
                    response = await client.post(
                        request_url, 
                        headers=self.headers, 
                        json=payload
                    )
                    
                    # Raise for 4xx/5xx errors
                    response.raise_for_status()
                    
                    data = response.json()
                    content = self._parse_response(data)
                    latency = time.time() - start_time
                    
                    return {
                        "prompt": prompt,
                        "response": content,
                        "latency_seconds": latency,
                        "status": "success",
                        "error": None
                    }
                    
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                logger.warning(f"Request failed (Attempt {attempt+1}/{retries}): {e}")
                if attempt == retries - 1:
                    latency = time.time() - start_time
                    logger.error(f"Failed to get response after {retries} retries for prompt: '{prompt[:30]}...'")
                    return {
                        "prompt": prompt,
                        "response": "",
                        "latency_seconds": latency,
                        "status": "error",
                        "error": str(e)
                    }
                await asyncio.sleep(2 ** attempt) # Exponential backoff
        
        return {
            "prompt": prompt,
            "response": "",
            "latency_seconds": time.time() - start_time,
            "status": "error",
            "error": "Max retries exceeded"
        }

    async def generate_batch_responses(self, prompts: List[str], temperature: float = config.default_temperature, 
                                       max_tokens: int = config.default_max_tokens, batch_size: int = 5) -> List[Dict[str, Any]]:
        """Process multiple prompts concurrently in batches."""
        results = []
        for i in range(0, len(prompts), batch_size):
            batch = prompts[i:i+batch_size]
            tasks = [self.generate_response(p, temperature, max_tokens) for p in batch]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
            await asyncio.sleep(1) # Slight pause to prevent heavy rate limits
        return results
