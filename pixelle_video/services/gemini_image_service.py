# Copyright (C) 2025 AIDC-AI
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Gemini Image Generation Service (via LiteLLM Proxy)

Generate images using Google Gemini API through LiteLLM proxy.
"""

import base64
import httpx
from typing import Optional
from loguru import logger
from pathlib import Path

from pixelle_video.models.media import MediaResult


class GeminiImageService:
    """
    Gemini Image Generation Service (via LiteLLM Proxy)
    
    Uses Google's Gemini API through LiteLLM proxy for image generation.
    
    Usage:
        service = GeminiImageService(config)
        result = await service.generate("a cat in space")
        print(result.url)  # Local file path
    """
    
    def __init__(self, config: dict):
        """
        Initialize Gemini Image service
        
        Args:
            config: Full application config dict
        """
        self._config = config
        self._output_dir: str = "output/images"
    
    def _get_config(self) -> tuple[Optional[str], Optional[str]]:
        """Get LiteLLM host and API key from config"""
        gemini_config = self._config.get("gemini", {})
        
        # Support both direct config and LiteLLM proxy config
        litellm_host = gemini_config.get("litellm_host") or gemini_config.get("base_url")
        api_key = gemini_config.get("api_key") or gemini_config.get("litellm_api_key")
        
        return litellm_host, api_key
    
    async def generate(
        self,
        prompt: str,
        width: Optional[int] = 1024,
        height: Optional[int] = 1024,
        negative_prompt: Optional[str] = None,
        seed: Optional[int] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> MediaResult:
        """
        Generate image using Gemini (via LiteLLM proxy)
        
        Args:
            prompt: Image generation prompt
            width: Image width
            height: Image height
            negative_prompt: Negative prompt (not used)
            seed: Random seed (not used)
            model: Model name (default: gemini-3.1-flash-image-preview)
            **kwargs: Additional parameters
        
        Returns:
            MediaResult with local file path
        """
        litellm_host, api_key = self._get_config()
        
        if not litellm_host or not api_key:
            raise ValueError(
                "Gemini LiteLLM proxy not configured. "
                "Add 'gemini.litellm_host' and 'gemini.api_key' to config.yaml"
            )
        
        # Remove trailing slash from host
        litellm_host = litellm_host.rstrip("/")
        
        # Default model for image generation
        model_name = model or "gemini-3.1-flash-image-preview"
        
        # Build request URL and payload
        url = f"{litellm_host}/v1beta/models/{model_name}:generateContent"
        
        # Determine aspect ratio
        aspect_ratio = self._get_aspect_ratio(width, height)
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "responseModalities": ["IMAGE"],
                "imageConfig": {}
            }
        }
        
        # Add aspect ratio if specified
        if aspect_ratio and aspect_ratio != "Auto":
            payload["generationConfig"]["imageConfig"]["aspectRatio"] = aspect_ratio
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": api_key
        }
        
        logger.info(f"🎨 Generating image with Gemini (via LiteLLM): {prompt[:50]}...")
        logger.debug(f"Request URL: {url}")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code != 200:
                error_msg = response.text
                logger.error(f"Gemini API error: {response.status_code} - {error_msg}")
                raise Exception(f"Gemini API error: {error_msg}")
            
            result = response.json()
        
        # Extract image from response
        try:
            candidates = result.get("candidates", [])
            if not candidates:
                raise Exception(f"No candidates in response: {result}")
            
            parts = candidates[0].get("content", {}).get("parts", [])
            
            image_base64 = None
            for part in parts:
                if "inlineData" in part:
                    image_base64 = part["inlineData"].get("data")
                    break
            
            if not image_base64:
                raise Exception(f"No image in response: {result}")
            
        except Exception as e:
            logger.error(f"Failed to parse response: {e}")
            raise
        
        # Save to local file
        output_dir = Path(self._output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        import time
        filename = f"gemini_{int(time.time() * 1000)}.png"
        output_path = output_dir / filename
        
        image_bytes = base64.b64decode(image_base64)
        output_path.write_bytes(image_bytes)
        
        logger.info(f"✅ Image saved to: {output_path}")
        
        return MediaResult(
            media_type="image",
            url=str(output_path.absolute())
        )
    
    def _get_aspect_ratio(self, width: int, height: int) -> str:
        """
        Determine aspect ratio string for Gemini
        
        Args:
            width: Image width
            height: Image height
        
        Returns:
            Aspect ratio string
        """
        if width is None or height is None:
            return "Auto"
        
        ratio = width / height
        
        if 0.99 <= ratio <= 1.01:
            return "1:1"
        elif 1.7 <= ratio <= 1.8:
            return "16:9"
        elif 0.55 <= ratio <= 0.6:
            return "9:16"
        elif 1.3 <= ratio <= 1.4:
            return "4:3"
        elif 0.7 <= ratio <= 0.8:
            return "3:4"
        else:
            return "Auto"
    
    @property
    def available(self) -> bool:
        """Check if Gemini is configured"""
        litellm_host, api_key = self._get_config()
        return bool(litellm_host and api_key)
    
    def __repr__(self) -> str:
        return f"<GeminiImageService available={self.available}>"
