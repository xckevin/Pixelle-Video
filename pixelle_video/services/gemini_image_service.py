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
        
        # Debug: log all config keys
        logger.debug(f"Gemini config keys: {list(gemini_config.keys())}")
        logger.debug(f"Full gemini config: {gemini_config}")
        
        # Support both direct config and LiteLLM proxy config
        litellm_host = gemini_config.get("litellm_host") or gemini_config.get("base_url")
        api_key = gemini_config.get("api_key") or gemini_config.get("litellm_api_key")
        
        # Debug log
        logger.debug(f"Gemini resolved: litellm_host={litellm_host}, api_key={'*' * 8 if api_key else None}")
        
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
        Generate image using Gemini (via LiteLLM proxy - OpenAI compatible)
        
        Args:
            prompt: Image generation prompt
            width: Image width
            height: Image height
            negative_prompt: Negative prompt (not used)
            seed: Random seed (not used)
            model: Model name (default: from config)
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
        
        # Get model from config or parameter
        gemini_config = self._config.get("gemini", {})
        model_name = model or gemini_config.get("image_model", "gemini-3-pro-image-preview")
        
        # Use OpenAI-compatible endpoint
        url = f"{litellm_host}/v1/chat/completions"
        
        payload = {
            "model": model_name,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        logger.info(f"🎨 Generating image with Gemini (via LiteLLM): {prompt[:50]}...")
        logger.debug(f"Request URL: {url}, Model: {model_name}")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code != 200:
                error_msg = response.text
                logger.error(f"Gemini API error: {response.status_code} - {error_msg}")
                raise Exception(f"Gemini API error: {error_msg}")
            
            result = response.json()
        
        # Extract image from OpenAI-format response
        try:
            choices = result.get("choices", [])
            if not choices:
                raise Exception(f"No choices in response: {result}")
            
            message = choices[0].get("message", {})
            content = message.get("content")
            parts = message.get("parts", [])
            images = message.get("images", [])  # LiteLLM returns images here
            
            # Debug: log response structure
            logger.debug(f"Content type: {type(content)}, parts: {len(parts) if parts else 0}, images: {len(images) if images else 0}")
            
            # Handle different response formats
            image_base64 = None
            
            # Format 1: images array (LiteLLM specific format)
            if images and isinstance(images, list) and len(images) > 0:
                img = images[0]
                logger.debug(f"First image type: {type(img)}, keys: {img.keys() if isinstance(img, dict) else 'N/A'}")
                if isinstance(img, dict):
                    # Format: {"image_url": {"url": "data:image/png;base64,..."}, "type": "image_url"}
                    if "image_url" in img:
                        img_url = img["image_url"]
                        if isinstance(img_url, dict) and "url" in img_url:
                            url = img_url["url"]
                            if isinstance(url, str) and url.startswith("data:"):
                                image_base64 = url.split(",", 1)[1]
                                logger.info(f"✅ Extracted base64 from image_url.url, length: {len(image_base64)}")
                        elif isinstance(img_url, str):
                            # Direct URL string
                            if img_url.startswith("data:"):
                                image_base64 = img_url.split(",", 1)[1]
                                logger.info(f"✅ Extracted base64 from image_url string, length: {len(image_base64)}")
                    elif "data" in img:
                        image_base64 = img["data"]
                        logger.debug("Found base64 in image dict 'data' field")
                elif isinstance(img, str):
                    if img.startswith("data:"):
                        image_base64 = img.split(",", 1)[1]
                        logger.debug("Extracted base64 from data URL")
                    else:
                        image_base64 = img
                        logger.debug(f"Using image string as base64 (length: {len(img)})")
            
            # If we found it, skip other checks
            if image_base64:
                logger.info(f"✅ Image extracted successfully, length: {len(image_base64)}")
            
            # Format 2: content is directly a base64 string
            if not image_base64 and isinstance(content, str) and len(content) > 1000:
                image_base64 = content
                logger.debug("Found base64 image directly in content string")
            
            # Format 3: parts array
            elif parts and isinstance(parts, list):
                for part in parts:
                    if isinstance(part, dict) and "data" in part:
                        image_base64 = part["data"]
                        logger.debug("Found base64 image in parts array")
                        break
            
            # Format 4: content is a dict
            elif isinstance(content, dict):
                if "image_url" in content:
                    image_url = content["image_url"]
                    if isinstance(image_url, str) and image_url.startswith("data:"):
                        image_base64 = image_url.split(",", 1)[1]
                elif "url" in content:
                    image_url = content["url"]
                    if isinstance(image_url, str) and image_url.startswith("data:"):
                        image_base64 = image_url.split(",", 1)[1]
            
            # Format 5: content is a list of parts
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict):
                        if "image" in part:
                            image_base64 = part["image"]
                            break
                        elif "data" in part:
                            image_base64 = part["data"]
                            break
            
            if not image_base64:
                # Log the response structure for debugging
                logger.error(f"Could not extract image from response.")
                logger.error(f"Message keys: {message.keys()}")
                raise Exception(f"No image found in response")
            
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
