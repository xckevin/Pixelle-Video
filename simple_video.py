#!/usr/bin/env python3
"""Simple video generation with local image"""

import asyncio
import sys
sys.path.insert(0, '/Users/liukai/Pixelle-Video')

from pixelle_video.service import PixelleVideoCore
import time


async def generate_simple_video():
    """Generate video with pre-downloaded image"""
    print("\n🎬 Generating Dance Video")
    print("=" * 50)
    
    core = PixelleVideoCore(config_path="/Users/liukai/Pixelle-Video/config.yaml")
    await core.initialize()
    
    # Use existing image from earlier test
    existing_image = "/Users/liukai/Pixelle-Video/output/images/gemini_1774325693990.png"
    
    script = """优雅的现代舞蹈是情感与技巧的完美结合。
它让观众感受到舞者内心深处的故事。
通过舞蹈，我们可以探索无限可能的自我。"""
    
    try:
        print("\n📝 Generating audio...")
        audio = await core.tts("优雅的现代舞蹈，展现艺术与美的完美融合")
        print(f"✅ Audio: {audio}")
        
        # Use existing image
        print(f"\n🖼️ Using existing image: {existing_image}")
        
        # Create simple video with ffmpeg
        import subprocess
        output = "/tmp/openclaw/dance_final.mp4"
        
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", existing_image,
            "-i", audio,
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
            output
        ]
        
        print("\n🎬 Creating video...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"\n✅ Video created: {output}")
            return output
        else:
            print(f"❌ FFmpeg error: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        await core.cleanup()


if __name__ == "__main__":
    asyncio.run(generate_simple_video())
