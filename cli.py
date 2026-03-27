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
from pixelle_video.prompts.image_generation import IMAGE_STYLE_PRESETS, get_style_prompt_prefix


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
    image_style: str = None,
    transition: str = None,
    transition_duration: float = 0.3,
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
        image_style: Image visual style key (e.g. 'flat_design', 'anime')
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

    # Resolve prompt_prefix: image_style overrides explicit prompt_prefix
    effective_prompt_prefix = prompt_prefix
    if image_style:
        effective_prompt_prefix = get_style_prompt_prefix(image_style)

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
            prompt_prefix=effective_prompt_prefix if effective_prompt_prefix else None,
            output_path=output,
            progress_callback=progress_callback,
            template_params=template_params,
            voice_id=voice,
            tts_speed=tts_speed,
            content_style=style,
            transition=transition,
            transition_duration=transition_duration,
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


async def batch_generate(
    topics_file: str,
    output_dir: str = "batch_output",
    n_scenes: int = 5,
    workflow: str = "gemini",
    template: str = "1080x1920/image_default.html",
    style: str = "douyin-knowledge",
    image_style: str = None,
    voice: str = None,
    tts_speed: float = None,
    signature: str = None,
    transition: str = None,
    transition_duration: float = 0.3,
    delay: float = 2.0,
):
    """
    Batch generate videos from a topics file

    Each non-empty, non-comment line in the file is treated as a topic.
    Lines starting with '#' are skipped.

    Args:
        topics_file: Path to file with one topic per line
        output_dir: Directory to save generated videos
        n_scenes: Number of scenes per video
        workflow: Image generation workflow
        template: Video template
        style: Platform narration style
        image_style: Image visual style
        voice: TTS voice ID
        tts_speed: TTS speech speed
        signature: Watermark text
        delay: Seconds to wait between videos (default: 2.0)
    """
    import time

    topics_path = Path(topics_file)
    if not topics_path.exists():
        print(f"❌ Topics file not found: {topics_file}")
        return

    # Read topics
    topics = []
    with open(topics_path, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                topics.append(stripped)

    if not topics:
        print("❌ No topics found in file.")
        return

    # Create output directory
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n📋 Batch Generate: {len(topics)} topics → {output_dir}")
    print(f"=" * 60)

    success = 0
    failed = []

    for idx, topic in enumerate(topics, 1):
        safe_name = topic[:30].replace("/", "_").replace("\\", "_").replace(" ", "_")
        filename = f"{idx:02d}_{safe_name}.mp4"
        output_path = str(out_dir / filename)

        print(f"\n[{idx}/{len(topics)}] 🎬 {topic}")
        print(f"  → {output_path}")

        try:
            result = await generate_video(
                text=topic,
                output=output_path,
                n_scenes=n_scenes,
                workflow=workflow,
                template=template,
                style=style,
                image_style=image_style,
                voice=voice,
                tts_speed=tts_speed,
                signature=signature,
                transition=transition,
                transition_duration=transition_duration,
            )
            if result:
                success += 1
                print(f"  ✅ Done: {output_path}")
            else:
                failed.append((idx, topic))
                print(f"  ❌ Failed (no result)")
        except Exception as e:
            failed.append((idx, topic))
            print(f"  ❌ Error: {e}")

        if idx < len(topics):
            print(f"  ⏳ Waiting {delay}s before next video...")
            await asyncio.sleep(delay)

    print(f"\n{'=' * 60}")
    print(f"✅ Batch complete: {success}/{len(topics)} succeeded")
    if failed:
        print(f"❌ Failed topics:")
        for i, t in failed:
            print(f"   [{i:02d}] {t}")


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
    gen_parser.add_argument(
        "--image-style",
        choices=list(IMAGE_STYLE_PRESETS.keys()),
        dest="image_style",
        default=None,
        help="Image visual style preset (e.g. flat_design, anime, realistic)"
    )
    gen_parser.add_argument(
        "--transition",
        choices=["fade", "wipeleft", "wiperight", "slideleft", "dissolve"],
        default=None,
        help="Frame transition effect between scenes"
    )
    gen_parser.add_argument(
        "--transition-duration",
        type=float,
        dest="transition_duration",
        default=0.3,
        help="Transition duration in seconds (default: 0.3)"
    )
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Test services")
    test_parser.add_argument(
        "--service",
        choices=["llm", "tts", "image", "all"],
        default="all",
        help="Service to test"
    )

    # Batch command
    batch_parser = subparsers.add_parser("batch", help="Batch generate videos from a topics file")
    batch_parser.add_argument("topics_file", help="Path to topics file (one topic per line, # for comments)")
    batch_parser.add_argument("-o", "--output-dir", default="batch_output", dest="output_dir",
                              help="Output directory (default: batch_output)")
    batch_parser.add_argument("-n", "--n-scenes", type=int, default=5, dest="n_scenes",
                              help="Number of scenes per video (default: 5)")
    batch_parser.add_argument("-w", "--workflow", default="gemini",
                              help="Image workflow (default: gemini)")
    batch_parser.add_argument("-t", "--template", default="1080x1920/image_default.html",
                              help="Video template")
    batch_parser.add_argument("--style", choices=list(STYLE_DESCRIPTIONS.keys()),
                              default="douyin-knowledge", help="Platform narration style")
    batch_parser.add_argument("--image-style", choices=list(IMAGE_STYLE_PRESETS.keys()),
                              dest="image_style", default=None, help="Image visual style preset")
    batch_parser.add_argument("--voice", default=None,
                              help="TTS voice ID (e.g. zh-CN-XiaoxiaoNeural)")
    batch_parser.add_argument("--tts-speed", type=float, dest="tts_speed", default=None,
                              help="TTS speech speed multiplier")
    batch_parser.add_argument("--signature", default=None, help="Watermark/signature text")
    batch_parser.add_argument("--transition", default=None,
                              choices=['fade', 'wipeleft', 'wiperight', 'slideleft', 'dissolve'],
                              help="Frame transition effect (default: None)")
    batch_parser.add_argument("--transition-duration", type=float, default=0.3, dest="transition_duration",
                              help="Transition duration in seconds (default: 0.3)")
    batch_parser.add_argument("--delay", type=float, default=2.0,
                              help="Seconds to wait between videos (default: 2.0)")
    
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
            image_style=args.image_style,
            transition=args.transition,
            transition_duration=args.transition_duration,
        ))
    elif args.command == "test":
        asyncio.run(test_services(args.service))
    elif args.command == "batch":
        asyncio.run(batch_generate(
            topics_file=args.topics_file,
            output_dir=args.output_dir,
            n_scenes=args.n_scenes,
            workflow=args.workflow,
            template=args.template,
            style=args.style,
            image_style=args.image_style,
            voice=args.voice,
            tts_speed=args.tts_speed,
            signature=args.signature,
            transition=args.transition,
            transition_duration=args.transition_duration,
            delay=args.delay,
        ))
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
