#!/usr/bin/env python3
"""
Pixelle-Video CLI - Command Line Interface for Video Generation

Usage:
    python cli.py generate "如何养成早起的好习惯" --output video.mp4
    python cli.py generate "如何养成早起的好习惯" --n-scenes 3 --workflow gemini
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from pixelle_video.service import PixelleVideoCore
from pixelle_video.prompts.topic_narration import STYLE_DESCRIPTIONS


async def generate_video(
    text: str,
    output: str = "output.mp4",
    n_scenes: int = 5,
    workflow: str = "gemini",
    template: str = "1080x1920/image_default.html",
    title: str = None,
    mode: str = "generate",
    prompt_prefix: str = "",
    bgm: str = None,
    signature: str = None,
    voice: str = None,
    tts_speed: float = None,
    style: str = "douyin-knowledge",
):
    """
    Generate video from topic or script

    Args:
        text: Topic or script text
        output: Output video path
        n_scenes: Number of scenes
        workflow: Image generation workflow (gemini, runninghub/image_flux.json, etc.)
        template: Video template
        title: Video title (auto-generated if not provided)
        mode: "generate" (LLM generates script) or "fixed" (use text as-is)
        prompt_prefix: Image prompt prefix
        bgm: Background music path
        signature: Watermark/signature text shown in template (pass "" to remove)
        voice: TTS voice ID (e.g. zh-CN-XiaoxiaoNeural, YunxiNeural, YunjianNeural)
        tts_speed: TTS speech speed multiplier (e.g. 1.0, 1.2)
        style: Platform style key (e.g. 'douyin-knowledge', 'wechat-knowledge')
    """
    print(f"\n🎬 Pixelle-Video CLI")
    print(f"=" * 50)
    print(f"Text: {text[:50]}...")
    print(f"Output: {output}")
    print(f"Scenes: {n_scenes}")
    print(f"Workflow: {workflow}")
    print(f"Template: {template}")
    if signature is not None:
        print(f"Signature: {repr(signature)}")
    print(f"=" * 50 + "\n")
    
    # Initialize core
    core = PixelleVideoCore(config_path="config.yaml")
    await core.initialize()
    
    print("✅ Initialized")
    
    # Progress callback
    def progress_callback(event):
        step_names = {
            "setup": "🚀 Setting up",
            "generating_narrations": "📝 Generating script",
            "generating_title": "📌 Generating title",
            "generating_image_prompts": "🎨 Generating image prompts",
            "producing_frames": "🎬 Producing frames",
            "post_production": "🎞️ Post-production",
        }
        step_name = step_names.get(event.event_type, event.event_type)
        print(f"  {step_name}: {event.progress * 100:.0f}%")
    
    # Build template_params if signature is specified
    template_params = None
    if signature is not None:
        template_params = {"signature": signature}

    try:
        # Generate video
        result = await core.generate_video(
            text=text,
            pipeline="standard",
            mode=mode,
            n_scenes=n_scenes,
            title=title,
            frame_template=template,
            media_workflow=workflow,
            prompt_prefix=prompt_prefix if prompt_prefix else None,
            output_path=output,
            progress_callback=progress_callback,
            template_params=template_params,
            voice_id=voice,
            tts_speed=tts_speed,
            content_style=style,
        )

        print(f"\n✅ Video generated: {result.video_path}")
        print(f"   Duration: {result.duration:.1f}s")
        print(f"   Frames: {getattr(result, 'frame_count', 'N/A')}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        await core.cleanup()


def main():
    parser = argparse.ArgumentParser(
        description="Pixelle-Video CLI - Generate videos from command line"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate a video")
    gen_parser.add_argument(
        "text",
        help="Topic or script text (e.g., '如何养成早起的好习惯')"
    )
    gen_parser.add_argument(
        "-o", "--output",
        default="output.mp4",
        help="Output video path (default: output.mp4)"
    )
    gen_parser.add_argument(
        "-n", "--n-scenes",
        type=int,
        default=5,
        help="Number of scenes (default: 5)"
    )
    gen_parser.add_argument(
        "-w", "--workflow",
        default="gemini",
        help="Image workflow: gemini, runninghub/image_flux.json, etc. (default: gemini)"
    )
    gen_parser.add_argument(
        "-t", "--template",
        default="1080x1920/image_default.html",
        help="Video template (default: 1080x1920/image_default.html)"
    )
    gen_parser.add_argument(
        "--title",
        help="Video title (auto-generated if not provided)"
    )
    gen_parser.add_argument(
        "--mode",
        choices=["generate", "fixed"],
        default="generate",
        help="generate: LLM creates script from topic; fixed: use text as-is"
    )
    gen_parser.add_argument(
        "--prompt-prefix",
        default="",
        help="Image prompt prefix for style control"
    )
    gen_parser.add_argument(
        "--bgm",
        help="Background music path"
    )
    gen_parser.add_argument(
        "--signature",
        default=None,
        help='Watermark/signature text shown in bottom-right of template. '
             'Pass empty string to remove: --signature ""'
    )
    gen_parser.add_argument(
        "--voice",
        default=None,
        help='TTS voice ID. Options: zh-CN-XiaoxiaoNeural (女暖), '
             'zh-CN-YunxiNeural (男磁), zh-CN-YunjianNeural (男力)'
    )
    gen_parser.add_argument(
        "--tts-speed",
        type=float,
        dest="tts_speed",
        default=None,
        help="TTS speech speed multiplier (e.g. 1.0 normal, 1.2 faster)"
    )
    gen_parser.add_argument(
        "--style",
        choices=list(STYLE_DESCRIPTIONS.keys()),
        default="douyin-knowledge",
        help="Platform narration style (default: douyin-knowledge)"
    )
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Test services")
    test_parser.add_argument(
        "--service",
        choices=["llm", "tts", "image", "all"],
        default="all",
        help="Service to test"
    )
    
    args = parser.parse_args()
    
    if args.command == "generate":
        asyncio.run(generate_video(
            text=args.text,
            output=args.output,
            n_scenes=args.n_scenes,
            workflow=args.workflow,
            template=args.template,
            title=args.title,
            mode=args.mode,
            prompt_prefix=args.prompt_prefix,
            bgm=args.bgm,
            signature=args.signature,
            voice=args.voice,
            tts_speed=args.tts_speed,
            style=args.style,
        ))
    elif args.command == "test":
        asyncio.run(test_services(args.service))
    else:
        parser.print_help()


async def test_services(service: str):
    """Test available services"""
    print(f"\n🧪 Testing Services")
    print(f"=" * 50)
    
    core = PixelleVideoCore(config_path="config.yaml")
    await core.initialize()
    
    if service in ["llm", "all"]:
        print("\n📝 Testing LLM...")
        try:
            result = await core.llm("Hello, how are you?")
            print(f"   ✅ LLM: {result[:100]}...")
        except Exception as e:
            print(f"   ❌ LLM: {e}")
    
    if service in ["tts", "all"]:
        print("\n🎤 Testing TTS...")
        try:
            result = await core.tts("你好，这是一个测试")
            print(f"   ✅ TTS: {result}")
        except Exception as e:
            print(f"   ❌ TTS: {e}")
    
    if service in ["image", "all"]:
        print("\n🎨 Testing Image (Gemini)...")
        try:
            result = await core.media(
                prompt="a cute cat",
                workflow="gemini"
            )
            print(f"   ✅ Image: {result.url}")
        except Exception as e:
            print(f"   ❌ Image: {e}")
    
    await core.cleanup()
    print("\n" + "=" * 50)


if __name__ == "__main__":
    main()
