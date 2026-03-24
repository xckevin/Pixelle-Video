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
LiteLLM Video Generation Service

Generate videos using LiteLLM proxy (supports Runway, Pika, etc.)
"""

import asyncio
import time
from typing import Optional
from pathlib import Path

import httpx
from loguru import logger

from pixelle_video.models.media import MediaResult


class LiteLLMVideoService:
    """
    LiteLLM Video Generation Service
    
    Uses LiteLLM proxy for video generation (Runway, Pika, etc.)
    
    API Flow:
    1. POST /videos - Start video generation
    2. GET /v1/videos/{id} - Poll status
    3. GET /v1/videos/{id}/content - Download video
    
    Usage:
        service = LiteLLMVideoService(config)
        result = await service.generate("a cat running")
        print(result.url)  # Local file path
    """
    
    # Polling settings
    POLL_INTERVAL = 5  # seconds
    MAX_POLL_TIME = 600  # 10 minutes max
    
    def __init__(self, config: dict):
        """
        Initialize LiteLLM Video service
        
        Args:
            config: Full application config dict
        """
        self._config = config
        self._output_dir: str = "output/videos"
    
    def _get_config(self) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Get LiteLLM host, API key, and model from config"""
        video_config = self._config.get("video", {})
        
        litellm_host = video_config.get("litellm_host")
        api_key = video_config.get("api_key")
        model = video_config.get("model", "runway-gen3-turbo")
        
        logger.debug(f"Video config: litellm_host={litellm_host}, model={model}")
        
        return litellm_host, api_key, model
    
    async def generate(
        self,
        prompt: str,
        duration: Optional[float] = 8.0,
        width: Optional[int] = None,
        height: Optional[int] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> MediaResult:
        """
        Generate video using LiteLLM proxy
        
        Args:
            prompt: Video generation prompt
            duration: Video duration in seconds (default: 8)
            width: Video width (not all models support)
            height: Video height (not all models support)
            model: Model name (default: from config)
            **kwargs: Additional parameters
        
        Returns:
            MediaResult with local file path
        """
        litellm_host, api_key, default_model = self._get_config()
        
        if not litellm_host or not api_key:
            raise ValueError(
                "LiteLLM Video not configured. "
                "Add 'video.litellm_host' and 'video.api_key' to config.yaml"
            )
        
        # Remove trailing slash from host
        litellm_host = litellm_host.rstrip("/")
        
        # Get model from config or parameter
        model_name = model or default_model
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        logger.info(f"🎬 Generating video with LiteLLM: {prompt[:50]}...")
        logger.debug(f"Model: {model_name}, Duration: {duration}s")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Step 1: Start video generation
            generate_url = f"{litellm_host}/videos"
            
            payload = {
                "model": model_name,
                "prompt": prompt,
                "seconds": str(int(duration))
            }
            
            logger.debug(f"POST {generate_url}")
            response = await client.post(generate_url, json=payload, headers=headers)
            
            if response.status_code not in [200, 201]:
                error_msg = response.text
                logger.error(f"Video generation failed: {response.status_code} - {error_msg}")
                raise Exception(f"Video generation failed: {error_msg}")
            
            result = response.json()
            video_id = result.get("id") or result.get("video_id") or result.get("data", {}).get("id")
            
            if not video_id:
                logger.error(f"No video_id in response: {result}")
                raise Exception(f"No video_id in response: {result}")
            
            logger.info(f"📹 Video generation started: {video_id}")
            
            # Step 2: Poll status
            status_url = f"{litellm_host}/v1/videos/{video_id}"
            start_time = time.time()
            
            while True:
                elapsed = time.time() - start_time
                if elapsed > self.MAX_POLL_TIME:
                    raise Exception(f"Video generation timed out after {self.MAX_POLL_TIME}s")
                
                status_response = await client.get(status_url, headers=headers)
                
                if status_response.status_code != 200:
                    logger.warning(f"Status check failed: {status_response.status_code}")
                    await asyncio.sleep(self.POLL_INTERVAL)
                    continue
                
                status_data = status_response.json()
                status = status_data.get("status") or status_data.get("state", "").lower()
                
                logger.debug(f"Video status: {status} (elapsed: {elapsed:.0f}s)")
                
                if status in ["completed", "complete", "succeeded", "success"]:
                    break
                elif status in ["failed", "error"]:
                    error = status_data.get("error") or status_data.get("message", "Unknown error")
                    raise Exception(f"Video generation failed: {error}")
                
                await asyncio.sleep(self.POLL_INTERVAL)
            
            logger.info(f"✅ Video generation completed: {video_id}")
            
            # Step 3: Download video
            download_url = f"{litellm_host}/v1/videos/{video_id}/content"
            
            # Get video info for duration
            video_duration = status_data.get("duration") or status_data.get("seconds") or duration
            
            # Download video
            output_dir = Path(self._output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Use short filename (video_id can be very long)
            import hashlib
            short_id = hashlib.md5(video_id.encode()).hexdigest()[:12]
            output_path = output_dir / f"video_{short_id}.mp4"
            
            logger.info(f"⬇️ Downloading video from {download_url}")
            
            download_response = await client.get(download_url, headers=headers, follow_redirects=True)
            
            if download_response.status_code != 200:
                raise Exception(f"Failed to download video: {download_response.status_code}")
            
            output_path.write_bytes(download_response.content)
            
            logger.info(f"✅ Video saved to: {output_path}")
            
            return MediaResult(
                media_type="video",
                url=str(output_path.absolute()),
                duration=float(video_duration) if video_duration else None
            )
    
    @property
    def available(self) -> bool:
        """Check if LiteLLM Video is configured"""
        litellm_host, api_key, _ = self._get_config()
        return bool(litellm_host and api_key)
    
    def __repr__(self) -> str:
        return f"<LiteLLMVideoService available={self.available}>"
