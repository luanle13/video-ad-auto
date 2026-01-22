#!/usr/bin/env python3
"""
Test script for Script Generation and Image Generation flow.

This script tests the agent pipeline for kitchen product video ads:
1. ProductAnalyzer (mock or real)
2. ScriptGenerator
3. ImageGenerator

Outputs are saved to:
- ./test_output/script_TIMESTAMP.json (script data)
- ./test_output/opening_frame_TIMESTAMP.png (opening image for Video 1)
- ./test_output/bridge_frame_TIMESTAMP.png (bridge image for Video 1→2 connection)

Usage:
    # First, set up environment
    cd backend
    source .venv/bin/activate
    pip install -r requirements.txt
    
    # Set required environment variables in .env file
    AZURE_OPENAI_API_KEY=your-azure-key
    AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/openai/v1/
    AZURE_GPT_DEPLOYMENT_NAME=gpt-4.1
    
    # Run the test
    python test_agents_flow.py
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded .env file")
except ImportError:
    print("⚠️  python-dotenv not installed, using system environment variables")
    print("   Install with: pip install python-dotenv")

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Create output directory
OUTPUT_DIR = Path(__file__).parent / "test_output"
OUTPUT_DIR.mkdir(exist_ok=True)
print(f"📁 Output directory: {OUTPUT_DIR}")


def check_environment():
    """Check required environment variables."""
    print("=" * 60)
    print("🔍 Checking Environment")
    print("=" * 60)
    
    azure_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    
    if not azure_key:
        print("❌ AZURE_OPENAI_API_KEY not set")
        print("   Set it in .env file")
        return False
    else:
        print(f"✅ AZURE_OPENAI_API_KEY set ({azure_key[:10]}...)")
    
    if not azure_endpoint:
        print("❌ AZURE_OPENAI_ENDPOINT not set")
        print("   Set it in .env file")
        print("   Example: https://your-resource.openai.azure.com/openai/v1/")
        return False
    else:
        print(f"✅ AZURE_OPENAI_ENDPOINT set")
        print(f"   Endpoint: {azure_endpoint}")
    
    print(f"\n📝 Will use Azure OpenAI for:")
    print(f"   - GPT-4o (script generation)")
    print(f"   - FLUX-1.1-pro (image generation)")
    
    return True


def create_mock_product_data():
    """Create mock product analysis data for testing."""
    return {
        "key_features": [
            "1800W powerful motor",
            "6 stainless steel blades",
            "64oz BPA-free pitcher",
            "10 speed settings with pulse",
            "Self-cleaning function"
        ],
        "unique_selling_points": [
            "Crushes ice in seconds",
            "Whisper-quiet operation",
            "Dishwasher-safe parts"
        ],
        "target_audience": "Health-conscious home cooks and smoothie enthusiasts aged 25-45",
        "visual_elements": [
            "Sleek brushed stainless steel finish",
            "LED control panel",
            "Clear pitcher with measurement markings",
            "Compact countertop footprint"
        ],
        "product_category": "kitchen appliances",
        "price_positioning": "mid-range",
        "suggested_hooks": [
            "Watch ice disappear in 3 seconds",
            "The smoothie maker that won't wake the baby",
            "From frozen to silky smooth instantly"
        ]
    }


def create_mock_market_data():
    """Create mock market insight data for testing."""
    return {
        "content_angles": [
            "Morning routine transformation",
            "Healthy lifestyle made easy",
            "Kitchen upgrade essentials"
        ],
        "trending_formats": [
            "Before/after transformation",
            "POV cooking content",
            "Satisfying process videos"
        ],
        "platform_tips": {
            "TikTok": "Use trending sounds, quick cuts",
            "Instagram": "Focus on aesthetic, lifestyle shots"
        },
        "suggested_music_style": "upbeat electronic, energetic"
    }


def test_script_generator():
    """Test the ScriptGeneratorAgent."""
    print("\n" + "=" * 60)
    print("📝 Testing Script Generator")
    print("=" * 60)
    
    from src.agents.script_generator import ScriptGeneratorAgent, ScriptGeneratorInput
    
    # Create input with mock data
    product_data = create_mock_product_data()
    market_data = create_mock_market_data()
    
    script_input = ScriptGeneratorInput(
        job_id="test-job-001",
        user_id="test-user-001",
        product_title="ProBlend 3000 High-Performance Blender",
        key_features=product_data["key_features"],
        unique_selling_points=product_data["unique_selling_points"],
        target_audience=product_data["target_audience"],
        visual_elements=product_data["visual_elements"],
        price="$149.99",
        price_positioning=product_data["price_positioning"],
        suggested_hooks=product_data["suggested_hooks"],
        content_angles=market_data["content_angles"],
        trending_formats=market_data["trending_formats"],
        platform_tips=market_data["platform_tips"],
        suggested_music_style=market_data["suggested_music_style"],
        target_duration=18,  # 18 seconds
        tone="energetic",
    )
    
    print(f"\n📦 Product: {script_input.product_title}")
    print(f"⏱️  Target Duration: {script_input.target_duration}s")
    print(f"🎯 Tone: {script_input.tone}")
    
    # Run the agent
    print("\n🤖 Running ScriptGeneratorAgent...")
    agent = ScriptGeneratorAgent()
    
    try:
        result = agent.run(script_input)
        
        if result.success:
            print("\n✅ Script Generated Successfully!")
            print("-" * 40)
            print(f"\n🎬 HOOK (first 3s):\n{result.hook}")
            print(f"\n📊 SCENES ({result.scene_count} total, ~{result.estimated_duration_seconds}s):")
            
            for scene in result.scenes:
                print(f"\n  Scene {scene['scene_number']} ({scene['duration_seconds']}s):")
                print(f"    Visual: {scene['visual_description'][:100]}...")
                if scene.get('text_overlay'):
                    print(f"    Text: \"{scene['text_overlay']}\"")
                if scene.get('motion_description'):
                    print(f"    Motion: {scene['motion_description'][:80]}...")
            
            print(f"\n📢 CALL TO ACTION:\n{result.call_to_action}")
            print(f"\n🖼️  Opening Frame Description:\n{result.opening_frame_description[:200]}...")
            print(f"\n🖼️  Closing Frame Description:\n{result.closing_frame_description[:200]}...")
            print(f"\n#️⃣  Hashtags: {', '.join(result.suggested_hashtags[:5])}")
            print(f"\n🎵 Music Mood: {result.suggested_music_mood}")
            print(f"\n🎬 Motion Style: {result.motion_style}")
            
            # Save script to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            script_file = OUTPUT_DIR / f"script_{timestamp}.json"
            
            script_data = {
                "product": script_input.product_title,
                "target_duration": script_input.target_duration,
                "tone": script_input.tone,
                "hook": result.hook,
                "scenes": result.scenes,
                "call_to_action": result.call_to_action,
                "opening_frame_description": result.opening_frame_description,
                "closing_frame_description": result.closing_frame_description,
                "suggested_hashtags": result.suggested_hashtags,
                "suggested_music_mood": result.suggested_music_mood,
                "motion_style": result.motion_style,
                "full_visual_description": result.full_visual_description,
                "scene_count": result.scene_count,
                "estimated_duration_seconds": result.estimated_duration_seconds,
                "generated_at": timestamp,
            }
            
            with open(script_file, "w") as f:
                json.dump(script_data, f, indent=2)
            
            print(f"\n💾 Script saved to: {script_file.name}")
            
            return result
        else:
            print(f"\n❌ Script generation failed: {result.error}")
            return None
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_image_generator(script_result=None):
    """Test the ImageGeneratorAgent."""
    print("\n" + "=" * 60)
    print("🖼️  Testing Image Generator")
    print("=" * 60)
    
    # Check if Azure is configured
    azure_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    
    from src.agents.image_generator import ImageGeneratorAgent, ImageGeneratorInput
    
    # Create input
    product_data = create_mock_product_data()
    
    image_input = ImageGeneratorInput(
        job_id="test-job-001",
        user_id="test-user-001",
        product_title="ProBlend 3000 High-Performance Blender",
        product_description="A powerful 1800W blender with 6 stainless steel blades, perfect for smoothies, soups, and frozen drinks. Features 10 speed settings and a self-cleaning function.",
        product_category="kitchen appliances",
        visual_elements=product_data["visual_elements"],
        key_features=product_data["key_features"],
        price_positioning=product_data["price_positioning"],
        hook=script_result.hook if script_result else "Watch ice disappear in seconds",
        call_to_action=script_result.call_to_action if script_result else "Shop Now - Free Shipping",
        full_visual_description=script_result.full_visual_description if script_result else "",
        scenes=script_result.scenes if script_result else [],
        target_duration=script_result.estimated_duration_seconds if script_result else 15,
        style_preference="modern",
        color_scheme="silver and black with white accents",
    )
    
    print(f"\n📦 Product: {image_input.product_title}")
    print(f"🎨 Style: {image_input.style_preference}")
    print(f"🎨 Colors: {image_input.color_scheme}")
    print(f"⏱️  Target Duration: {image_input.target_duration}s (split into 2 videos)")
    
    # Run the agent (prompt generation)
    print("\n🤖 Running ImageGeneratorAgent (generating split video prompts)...")
    agent = ImageGeneratorAgent()
    
    try:
        result = agent.run(image_input)
        
        if result.success:
            print("\n✅ Split Video Prompts Generated Successfully!")
            print("-" * 40)
            
            print(f"\n🖼️  OPENING FRAME PROMPT (Start of Video 1):\n{result.opening_frame_prompt}")
            print(f"\n🖼️  BRIDGE FRAME PROMPT (End of Video 1 / Start of Video 2):\n{result.bridge_frame_prompt}")
            print(f"\n🔗 BRIDGE SCENE DESCRIPTION:\n{result.bridge_scene_description}")
            print(f"\n🎬 FIRST HALF VIDEO PROMPT:\n{result.first_half_prompt}")
            print(f"\n🎬 SECOND HALF VIDEO PROMPT:\n{result.second_half_prompt}")
            print(f"\n🎨 STYLE DESCRIPTION:\n{result.style_description}")
            print(f"\n📝 VISUAL CONTINUITY NOTES:\n{result.visual_continuity_notes}")
            print(f"\n🎬 MOTION SUGGESTIONS:")
            for i, suggestion in enumerate(result.motion_suggestions, 1):
                print(f"   {i}. {suggestion}")
            
            # Automatically generate images if Azure is configured
            if azure_key and azure_endpoint:
                print("\n" + "-" * 40)
                print("🎨 Generating images with Azure FLUX-1.1-pro...")
                
                try:
                    from src.workers.clients.azure_image import AzureImageClient
                    
                    client = AzureImageClient(
                        api_key=azure_key,
                        endpoint=azure_endpoint,
                        deployment_name="FLUX-1.1-pro",
                    )
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
                    # Generate opening frame
                    print("\n   📸 Generating opening frame (start of Video 1)...")
                    opening_result = client.generate_image(
                        prompt=result.opening_frame_prompt,
                        size="1440x1024",
                    )
                    
                    if opening_result.image_bytes:
                        opening_file = OUTPUT_DIR / f"opening_frame_{timestamp}.png"
                        with open(opening_file, "wb") as f:
                            f.write(opening_result.image_bytes)
                        print(f"   ✅ Opening frame saved: {opening_file.name}")
                    
                    # Generate bridge frame
                    print("   📸 Generating bridge frame (end of Video 1 / start point for Video 2)...")
                    bridge_result = client.generate_image(
                        prompt=result.bridge_frame_prompt,
                        size="1440x1024",
                    )
                    
                    if bridge_result.image_bytes:
                        bridge_file = OUTPUT_DIR / f"bridge_frame_{timestamp}.png"
                        with open(bridge_file, "wb") as f:
                            f.write(bridge_result.image_bytes)
                        print(f"   ✅ Bridge frame saved: {bridge_file.name}")
                    
                    print("\n✅ Images generated and saved to test_output/")
                    
                except Exception as e:
                    print(f"\n❌ Image generation failed: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("\n⚠️  Azure OpenAI not configured. Skipping image generation.")
                print("   Set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT to generate images.")
            
            return result
        else:
            print(f"\n❌ Image prompt generation failed: {result.error}")
            return None
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_full_flow():
    """Test the complete flow: Script → Image prompts → Split video generation prompts."""
    print("\n" + "=" * 60)
    print("🚀 FULL AGENT FLOW TEST")
    print("   Kitchen Product Video Ad Generation (Split Video)")
    print("=" * 60)
    
    # Step 1: Generate script
    script_result = test_script_generator()
    
    if script_result:
        # Step 2: Generate image prompts based on script
        image_result = test_image_generator(script_result)
        
        if image_result:
            print("\n" + "=" * 60)
            print("✅ FULL FLOW TEST COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            
            # Calculate split
            total_duration = script_result.estimated_duration_seconds
            half_duration = total_duration // 2
            
            print("\n📋 Summary:")
            print(f"   - Script: {script_result.scene_count} scenes, ~{total_duration}s total")
            print(f"   - Split into 2 videos: ~{half_duration}s each")
            print(f"   - First half scenes: {len(image_result.first_half_scenes)}")
            print(f"   - Second half scenes: {len(image_result.second_half_scenes)}")
            print(f"   - Opening frame prompt: {len(image_result.opening_frame_prompt)} chars")
            print(f"   - Bridge frame prompt: {len(image_result.bridge_frame_prompt)} chars")
            
            # Step 3: Generate split video generation prompt
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Build comprehensive split video generation data
            video_prompt_data = {
                "product": "ProBlend 3000 High-Performance Blender",
                "total_duration": total_duration,
                "split_strategy": {
                    "video_1_duration": half_duration,
                    "video_2_duration": total_duration - half_duration,
                    "combine_method": "Veo3 extend feature",
                },
                
                # First half (Video 1)
                "video_1": {
                    "start_image": f"opening_frame_{timestamp}.png",
                    "end_image": f"bridge_frame_{timestamp}.png",
                    "duration_seconds": half_duration,
                    "prompt": image_result.first_half_prompt,
                    "scenes": [
                        {
                            "scene_number": scene.get("scene_number"),
                            "duration": scene.get("duration_seconds", scene.get("duration", 3)),
                            "visual": scene.get("visual_description", scene.get("visual", "")),
                            "text_overlay": scene.get("text_overlay", ""),
                            "motion": scene.get("motion_description", scene.get("motion", "")),
                        }
                        for scene in image_result.first_half_scenes
                    ],
                },
                
                # Second half (Video 2) - extends from bridge frame
                "video_2": {
                    "start_image": f"bridge_frame_{timestamp}.png",
                    "duration_seconds": total_duration - half_duration,
                    "prompt": image_result.second_half_prompt,
                    "extend_from": "video_1",
                    "scenes": [
                        {
                            "scene_number": scene.get("scene_number"),
                            "duration": scene.get("duration_seconds", scene.get("duration", 3)),
                            "visual": scene.get("visual_description", scene.get("visual", "")),
                            "text_overlay": scene.get("text_overlay", ""),
                            "motion": scene.get("motion_description", scene.get("motion", "")),
                        }
                        for scene in image_result.second_half_scenes
                    ],
                },
                
                "bridge_scene": {
                    "description": image_result.bridge_scene_description,
                    "image": f"bridge_frame_{timestamp}.png",
                    "purpose": "End of video 1 / Starting point for video 2 extend",
                },
                
                "style_description": image_result.style_description,
                "visual_continuity_notes": image_result.visual_continuity_notes,
                "motion_suggestions": image_result.motion_suggestions,
                "negative_prompt": "human faces, people, portraits, blurry, distorted, low quality, watermark, text",
                
                "veo3_config": {
                    "aspect_ratio": "16:9",
                    "extend_mode": True,
                },
                
                "generated_at": timestamp,
            }
            
            # Save video generation prompt (JSON)
            video_prompt_file = OUTPUT_DIR / f"video_prompt_{timestamp}.json"
            with open(video_prompt_file, "w") as f:
                json.dump(video_prompt_data, f, indent=2)
            
            print(f"\n💾 Video generation prompt saved to: {video_prompt_file.name}")
            
            # Save plain text prompts for easy copy-paste
            video_prompt_txt_file = OUTPUT_DIR / f"video_prompt_{timestamp}.txt"
            with open(video_prompt_txt_file, "w") as f:
                f.write("=" * 70 + "\n")
                f.write("SPLIT VIDEO GENERATION - VEO3 / PIAPI\n")
                f.write("=" * 70 + "\n\n")
                
                f.write("STRATEGY: Generate 2 videos and combine with extend feature\n")
                f.write(f"Total Duration: {total_duration}s = Video 1 ({half_duration}s) + Video 2 ({total_duration - half_duration}s)\n\n")
                
                f.write("=" * 70 + "\n")
                f.write("VIDEO 1 (FIRST HALF)\n")
                f.write("=" * 70 + "\n")
                f.write(f"Start Image: opening_frame_{timestamp}.png\n")
                f.write(f"Duration: {half_duration} seconds\n\n")
                f.write("PROMPT:\n")
                f.write("-" * 40 + "\n")
                f.write(image_result.first_half_prompt + "\n")
                f.write("-" * 40 + "\n\n")
                
                f.write("=" * 70 + "\n")
                f.write("VIDEO 2 (SECOND HALF - EXTEND FROM VIDEO 1)\n")
                f.write("=" * 70 + "\n")
                f.write(f"Start Image (Bridge): bridge_frame_{timestamp}.png\n")
                f.write(f"Duration: {total_duration - half_duration} seconds\n")
                f.write("Mode: Extend from Video 1\n\n")
                f.write("PROMPT:\n")
                f.write("-" * 40 + "\n")
                f.write(image_result.second_half_prompt + "\n")
                f.write("-" * 40 + "\n\n")
                
                f.write("=" * 70 + "\n")
                f.write("BRIDGE SCENE (TRANSITION POINT)\n")
                f.write("=" * 70 + "\n")
                f.write(f"Image: bridge_frame_{timestamp}.png\n")
                f.write(f"Description: {image_result.bridge_scene_description}\n\n")
                
                f.write("=" * 70 + "\n")
                f.write("STYLE & CONTINUITY\n")
                f.write("=" * 70 + "\n")
                f.write(f"Style: {image_result.style_description}\n\n")
                f.write(f"Continuity: {image_result.visual_continuity_notes}\n\n")
                
                f.write("Negative Prompt:\n")
                f.write("human faces, people, portraits, blurry, distorted, low quality, watermark, text\n")
            
            print(f"💾 Plain text prompt saved to: {video_prompt_txt_file.name}")
            
            # Display summary
            print("\n" + "=" * 60)
            print("🎬 VIDEO 1 (FIRST HALF)")
            print("=" * 60)
            print(f"Image: opening_frame_{timestamp}.png")
            print(f"Duration: {half_duration}s")
            print(f"\nPrompt:\n{image_result.first_half_prompt}")
            
            print("\n" + "=" * 60)
            print("🎬 VIDEO 2 (SECOND HALF - EXTEND)")
            print("=" * 60)
            print(f"Bridge Image: bridge_frame_{timestamp}.png")
            print(f"Duration: {total_duration - half_duration}s")
            print(f"\nPrompt:\n{image_result.second_half_prompt}")
            
            print("\n" + "=" * 60)
            print("🔗 BRIDGE SCENE")
            print("=" * 60)
            print(f"Description: {image_result.bridge_scene_description}")
            
            print("\n🔜 Next Steps:")
            print("   1. Use opening_frame image to generate Video 1 (first half)")
            print("   2. Use bridge_frame image + Veo3 extend to generate Video 2")
            print("   3. Combine videos for final 15-20s output")
            print("   4. Add text overlays during post-processing")
            print(f"   5. All files saved in: {OUTPUT_DIR}/")
            
            return True
    
    print("\n❌ Flow test failed. Check errors above.")
    return False


def build_video_generation_prompt(script_result, image_result):
    """Build a comprehensive prompt for PiAPI video generation."""
    # Combine visual descriptions from all scenes
    scene_visuals = []
    for scene in script_result.scenes:
        visual = scene.get("visual_description", "")
        motion = scene.get("motion_description", "")
        if visual:
            scene_text = visual
            if motion:
                scene_text += f" {motion}"
            scene_visuals.append(scene_text)
    
    # Build main prompt
    prompt_parts = [
        f"Professional kitchen product video advertisement for a high-performance blender.",
        f"Visual style: {image_result.style_description}",
        "",
        "Scene progression:",
    ]
    
    for i, scene_visual in enumerate(scene_visuals, 1):
        prompt_parts.append(f"{i}. {scene_visual}")
    
    prompt_parts.extend([
        "",
        "Camera and motion:",
        *[f"- {motion}" for motion in image_result.motion_suggestions[:3]],
        "",
        "Visual continuity notes:",
        image_result.visual_continuity_notes,
        "",
        "Requirements: No human faces, product-focused, smooth transitions, professional lighting, cinematic quality."
    ])
    
    return "\n".join(prompt_parts)


def main():
    """Main entry point."""
    print("\n" + "🎬" * 30)
    print("   VIDEO AD AUTOMATION - Agent Flow Test")
    print("🎬" * 30)
    
    if not check_environment():
        print("\n⚠️  Please set required environment variables and try again.")
        sys.exit(1)
    
    print("\n" + "-" * 60)
    print("Select test mode:")
    print("  1. Test Script Generator only")
    print("  2. Test Image Generator only (prompts)")
    print("  3. Test Full Flow (Script → Image prompts)")
    print("-" * 60)
    
    choice = input("\nEnter choice (1/2/3) [default: 3]: ").strip() or "3"
    
    if choice == "1":
        test_script_generator()
    elif choice == "2":
        test_image_generator()
    elif choice == "3":
        test_full_flow()
    else:
        print("Invalid choice. Running full flow test...")
        test_full_flow()
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
