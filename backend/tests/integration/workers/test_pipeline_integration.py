"""Integration tests for full pipeline: agent -> TTS -> video with mocked services."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.handler import handler as agent_handler
from src.shared.db import get_db
from src.shared.storage import get_storage
from src.workers.handlers.tts_handler import handler as tts_handler
from src.workers.handlers.video_handler import handler as video_handler


@pytest.mark.asyncio
async def test_full_pipeline_agent_to_tts_to_video():
    """Test full pipeline: agent -> TTS -> video with mocked external services."""
    # Event for agent task
    agent_event = {
        "task": "analyze",
        "user_id": "user123",
        "job_id": "job456",
        "product": {
            "id": "prod789",
            "title": "Wireless Bluetooth Headphones",
            "description": "High-quality wireless headphones with noise cancellation",
            "price": "$99.99",
            "image_keys": ["image1.jpg", "image2.jpg"]
        }
    }
    
    with patch('src.agents.handler.get_db') as mock_agent_db, \
         patch('src.workers.handlers.tts_handler.get_db') as mock_tts_db, \
         patch('src.workers.handlers.video_handler.get_db') as mock_video_db, \
         patch('src.workers.handlers.tts_handler.get_storage') as mock_tts_storage, \
         patch('src.workers.handlers.video_handler.get_storage') as mock_video_storage, \
         patch('src.workers.handlers.tts_handler.get_tts_service') as mock_tts_service, \
         patch('src.workers.handlers.video_handler.get_video_service') as mock_video_service, \
         patch('httpx.AsyncClient.post') as mock_httpx_post, \
         patch('boto3.client') as mock_boto_client:
        
        # Setup all mocks
        mock_agent_db.return_value = MagicMock()
        mock_tts_db.return_value = MagicMock()
        mock_video_db.return_value = MagicMock()
        
        # Mock storage
        mock_tts_storage.return_value = get_storage()
        mock_video_storage.return_value = get_storage()
        
        # Mock TTS service
        mock_tts_service_instance = AsyncMock()
        mock_tts_service_instance.generate_speech.return_value = MagicMock(
            audio_data=b"generated tts audio",
            content_type="audio/mpeg",
            provider_used="ELEVENLABS",
            character_count=50,
            duration_estimate_seconds=5.0,
            voice_id="test-voice"
        )
        mock_tts_service.return_value = mock_tts_service_instance
        
        # Mock video service
        mock_video_service_instance = AsyncMock()
        mock_video_service_instance.generate_video.return_value = MagicMock(
            video_data=b"generated video content",
            duration_seconds=10.0,
            job_response=MagicMock(data={"status": "completed", "id": "job-456"})
        )
        mock_video_service.return_value = mock_video_service_instance
        
        # Mock external API calls
        mock_response = MagicMock()
        mock_response.content = b"tts audio content"
        mock_response.headers = {"content-type": "audio/mpeg"}
        mock_httpx_post.return_value.__aenter__.return_value = mock_response
        
        # Mock Polly client
        mock_polly = MagicMock()
        mock_boto_client.return_value = mock_polly
        mock_polly.synthesize_speech.return_value = {
            "AudioStream": MagicMock(read=lambda: b"polly audio content"),
            "ContentType": "audio/mpeg",
            "RequestCharacters": 50
        }
        
        # Step 1: Run agent to analyze product
        agent_result = await agent_handler(agent_event, {})
        assert agent_result["success"] is True
        assert agent_result["task"] == "analyze"
        
        # Prepare TTS event using agent output
        tts_event = {
            "user_id": "user123",
            "job_id": "job456",
            "tts_script": "Introducing our amazing wireless headphones!",
            "tts_ssml": None,
            "voice_gender": "female",
            "voice_style": "professional",
            "speaking_rate": 1.0,
            "provider": "AUTO"
        }
        
        # Step 2: Generate TTS
        tts_result = await tts_handler(tts_event, {})
        assert tts_result["success"] is True
        assert tts_result["provider_used"] == "ELEVENLABS"
        
        # Prepare video event using TTS output
        video_event = {
            "user_id": "user123",
            "job_id": "job456",
            "video_prompt": "A person wearing wireless headphones enjoying music",
            "audio_s3_key": "user123/job456/voiceover.mp3" if tts_result["success"] else None,
            "aspect_ratio": "9:16",
            "duration": 10
        }
        
        # Step 3: Generate video
        video_result = await video_handler(video_event, {})
        assert video_result["success"] is True
        assert video_result["duration_seconds"] == 10.0
        
        # Verify all services were called
        mock_tts_service_instance.generate_speech.assert_called_once()
        mock_video_service_instance.generate_video.assert_called_once()


@pytest.mark.asyncio
async def test_pipeline_with_moto_dynamodb():
    """Test pipeline with mocked DynamoDB using moto."""
    from moto import mock_dynamodb
    
    with mock_dynamodb():
        # Create mock DynamoDB table
        import boto3
        from src.shared.config import get_settings
        
        settings = get_settings()
        dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')
        
        # Create tables that would be used
        table = dynamodb.create_table(
            TableName=settings.dynamodb_jobs_table,
            KeySchema=[
                {
                    'AttributeName': 'job_id',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'job_id',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Wait for table to be created
        table.wait_until_exists()
        
        # Now test the pipeline with real DB operations
        agent_event = {
            "task": "generate",  # Generate script based on analysis
            "user_id": "user123",
            "job_id": "job456",
            "product": {
                "id": "prod789",
                "title": "Wireless Bluetooth Headphones",
                "description": "High-quality wireless headphones with noise cancellation",
                "price": "$99.99",
                "image_keys": ["image1.jpg"]
            },
            "context": {
                "analyze": {
                    "output": {
                        "key_features": ["wireless", "noise cancellation"],
                        "unique_selling_points": ["premium sound quality"],
                        "target_audience": "music lovers",
                        "visual_elements": ["headphones", "person listening"],
                        "product_category": "electronics",
                        "price_positioning": "premium",
                        "suggested_hooks": ["listen to perfection"]
                    }
                }
            }
        }
        
        with patch('src.workers.handlers.tts_handler.get_storage') as mock_tts_storage, \
             patch('src.workers.handlers.video_handler.get_storage') as mock_video_storage, \
             patch('src.workers.handlers.tts_handler.get_tts_service') as mock_tts_service, \
             patch('src.workers.handlers.video_handler.get_video_service') as mock_video_service, \
             patch('httpx.AsyncClient.post') as mock_httpx_post, \
             patch('boto3.client') as mock_boto_client:
            
            # Mock storage
            mock_tts_storage.return_value = get_storage()
            mock_video_storage.return_value = get_storage()
            
            # Mock services
            mock_tts_service_instance = AsyncMock()
            mock_tts_service_instance.generate_speech.return_value = MagicMock(
                audio_data=b"pipeline tts audio",
                content_type="audio/mpeg",
                provider_used="ELEVENLABS",
                character_count=60,
                duration_estimate_seconds=6.0,
                voice_id="test-voice"
            )
            mock_tts_service.return_value = mock_tts_service_instance
            
            mock_video_service_instance = AsyncMock()
            mock_video_service_instance.generate_video.return_value = MagicMock(
                video_data=b"pipeline video content",
                duration_seconds=15.0,
                job_response=MagicMock(data={"status": "completed", "id": "job-456"})
            )
            mock_video_service.return_value = mock_video_service_instance
            
            # Mock external API calls
            mock_response = MagicMock()
            mock_response.content = b"tts audio for pipeline"
            mock_response.headers = {"content-type": "audio/mpeg"}
            mock_httpx_post.return_value.__aenter__.return_value = mock_response
            
            # Mock Polly client
            mock_polly = MagicMock()
            mock_boto_client.return_value = mock_polly
            mock_polly.synthesize_speech.return_value = {
                "AudioStream": MagicMock(read=lambda: b"polly pipeline content"),
                "ContentType": "audio/mpeg",
                "RequestCharacters": 60
            }
            
            # Run agent step
            agent_result = await agent_handler(agent_event, {})
            assert agent_result["success"] is True
            
            # Run TTS step
            tts_event = {
                "user_id": "user123",
                "job_id": "job456",
                "tts_script": "Experience premium sound quality with our headphones!",
                "tts_ssml": None,
                "voice_gender": "male",
                "voice_style": "enthusiastic",
                "speaking_rate": 1.1,
                "provider": "AUTO"
            }
            
            tts_result = await tts_handler(tts_event, {})
            assert tts_result["success"] is True
            
            # Run video step
            video_event = {
                "user_id": "user123",
                "job_id": "job456",
                "video_prompt": "Person enjoying premium headphones with great sound",
                "audio_s3_key": "user123/job456/voiceover.mp3",
                "aspect_ratio": "16:9",
                "duration": 15
            }
            
            video_result = await video_handler(video_event, {})
            assert video_result["success"] is True
            assert video_result["duration_seconds"] == 15.0


@pytest.mark.asyncio
async def test_pipeline_with_agent_tts_video_flow():
    """Test complete flow with agent analysis, TTS generation, and video creation."""
    with patch('src.agents.handler.get_db') as mock_agent_db, \
         patch('src.workers.handlers.tts_handler.get_db') as mock_tts_db, \
         patch('src.workers.handlers.video_handler.get_db') as mock_video_db, \
         patch('src.workers.handlers.tts_handler.get_storage') as mock_tts_storage, \
         patch('src.workers.handlers.video_handler.get_storage') as mock_video_storage, \
         patch('src.workers.handlers.tts_handler.get_tts_service') as mock_tts_service, \
         patch('src.workers.handlers.video_handler.get_video_service') as mock_video_service, \
         patch('httpx.AsyncClient.post') as mock_httpx_post, \
         patch('boto3.client') as mock_boto_client:
        
        # Setup mocks
        mock_agent_db.return_value = MagicMock()
        mock_tts_db.return_value = MagicMock()
        mock_video_db.return_value = MagicMock()
        
        # Mock storage
        mock_tts_storage.return_value = MagicMock()
        mock_tts_storage.return_value.generate_audio_key.return_value = "user123/job456/voiceover.mp3"
        mock_tts_storage.return_value.upload_file.return_value = "s3://bucket/user123/job456/voiceover.mp3"
        
        mock_video_storage.return_value = MagicMock()
        mock_video_storage.return_value.generate_video_key.return_value = "user123/job456/output.mp4"
        mock_video_storage.return_value.upload_file.return_value = "s3://bucket/user123/job456/output.mp4"
        
        # Mock services
        mock_tts_service_instance = AsyncMock()
        mock_tts_service_instance.generate_speech.return_value = MagicMock(
            audio_data=b"complete pipeline audio",
            content_type="audio/mpeg",
            provider_used="ELEVENLABS",
            character_count=75,
            duration_estimate_seconds=7.5,
            voice_id="test-voice"
        )
        mock_tts_service.return_value = mock_tts_service_instance
        
        mock_video_service_instance = AsyncMock()
        mock_video_service_instance.generate_video.return_value = MagicMock(
            video_data=b"complete pipeline video",
            duration_seconds=20.0,
            job_response=MagicMock(data={"status": "completed", "id": "job-456", "video_url": "https://example.com/video.mp4"})
        )
        mock_video_service.return_value = mock_video_service_instance
        
        # Mock external API calls
        mock_response = MagicMock()
        mock_response.content = b"tts audio for complete pipeline"
        mock_response.headers = {"content-type": "audio/mpeg"}
        mock_httpx_post.return_value.__aenter__.return_value = mock_response
        
        # Mock Polly client
        mock_polly = MagicMock()
        mock_boto_client.return_value = mock_polly
        mock_polly.synthesize_speech.return_value = {
            "AudioStream": MagicMock(read=lambda: b"polly complete pipeline"),
            "ContentType": "audio/mpeg",
            "RequestCharacters": 75
        }
        
        # Simulate the complete workflow
        # 1. Agent analyzes product
        agent_event = {
            "task": "analyze",
            "user_id": "user123",
            "job_id": "job456",
            "product": {
                "id": "prod789",
                "title": "Premium Wireless Headphones",
                "description": "Top-tier wireless headphones with premium features",
                "price": "$199.99",
                "image_keys": ["headphone1.jpg"]
            }
        }
        
        agent_result = await agent_handler(agent_event, {})
        assert agent_result["success"] is True
        assert "analyze" in agent_result["task"] or agent_result["task"] == "analyze"
        
        # 2. TTS generates voiceover
        tts_event = {
            "user_id": "user123",
            "job_id": "job456",
            "tts_script": "Discover the ultimate listening experience with our premium headphones!",
            "tts_ssml": None,
            "voice_gender": "female",
            "voice_style": "professional",
            "speaking_rate": 1.0,
            "provider": "AUTO"
        }
        
        tts_result = await tts_handler(tts_event, {})
        assert tts_result["success"] is True
        assert tts_result["character_count"] == 75
        
        # 3. Video service creates final video
        video_event = {
            "user_id": "user123",
            "job_id": "job456",
            "video_prompt": "Showcasing premium wireless headphones with elegant design",
            "audio_s3_key": "user123/job456/voiceover.mp3",
            "aspect_ratio": "9:16",
            "duration": 20
        }
        
        video_result = await video_handler(video_event, {})
        assert video_result["success"] is True
        assert video_result["duration_seconds"] == 20.0
        
        # Verify all steps were executed
        mock_tts_service_instance.generate_speech.assert_called_once()
        mock_video_service_instance.generate_video.assert_called_once()
        
        # Verify storage operations
        mock_tts_storage.return_value.generate_audio_key.assert_called_once_with("user123", "job456")
        mock_video_storage.return_value.generate_video_key.assert_called_once_with("user123", "job456")


@pytest.mark.asyncio
async def test_pipeline_error_handling():
    """Test pipeline error handling when one step fails."""
    with patch('src.agents.handler.get_db') as mock_agent_db, \
         patch('src.workers.handlers.tts_handler.get_db') as mock_tts_db, \
         patch('src.workers.handlers.tts_handler.get_storage') as mock_tts_storage, \
         patch('src.workers.handlers.tts_handler.get_tts_service') as mock_tts_service:
        
        # Setup mocks
        mock_agent_db.return_value = MagicMock()
        mock_tts_db.return_value = MagicMock()
        
        # Mock storage
        mock_tts_storage.return_value = MagicMock()
        
        # Mock TTS service to fail
        mock_tts_service_instance = AsyncMock()
        mock_tts_service_instance.generate_speech.side_effect = Exception("TTS generation failed")
        mock_tts_service.return_value = mock_tts_service_instance
        
        # Agent step should succeed
        agent_event = {
            "task": "analyze",
            "user_id": "user123",
            "job_id": "job456",
            "product": {
                "id": "prod789",
                "title": "Test Product",
                "description": "Test description",
                "price": "$19.99",
                "image_keys": ["image1.jpg"]
            }
        }
        
        agent_result = await agent_handler(agent_event, {})
        assert agent_result["success"] is True
        
        # TTS step should fail gracefully
        tts_event = {
            "user_id": "user123",
            "job_id": "job456",
            "tts_script": "Test script for error handling",
            "tts_ssml": None,
            "voice_gender": "female",
            "voice_style": "neutral",
            "speaking_rate": 1.0,
            "provider": "AUTO"
        }
        
        with pytest.raises(Exception, match="TTS generation failed"):
            await tts_handler(tts_event, {})
        
        # Verify TTS service was called but failed
        mock_tts_service_instance.generate_speech.assert_called_once()


@pytest.mark.asyncio
async def test_pipeline_with_multiple_agents():
    """Test pipeline with multiple agent steps."""
    with patch('src.agents.handler.get_db') as mock_agent_db, \
         patch('src.workers.handlers.tts_handler.get_db') as mock_tts_db, \
         patch('src.workers.handlers.video_handler.get_db') as mock_video_db, \
         patch('src.workers.handlers.tts_handler.get_storage') as mock_tts_storage, \
         patch('src.workers.handlers.video_handler.get_storage') as mock_video_storage, \
         patch('src.workers.handlers.tts_handler.get_tts_service') as mock_tts_service, \
         patch('src.workers.handlers.video_handler.get_video_service') as mock_video_service, \
         patch('httpx.AsyncClient.post') as mock_httpx_post, \
         patch('boto3.client') as mock_boto_client:
        
        # Setup mocks
        mock_agent_db.return_value = MagicMock()
        mock_tts_db.return_value = MagicMock()
        mock_video_db.return_value = MagicMock()
        
        # Mock storage
        mock_tts_storage.return_value = get_storage()
        mock_video_storage.return_value = get_storage()
        
        # Mock services
        mock_tts_service_instance = AsyncMock()
        mock_tts_service_instance.generate_speech.return_value = MagicMock(
            audio_data=b"multi-agent audio",
            content_type="audio/mpeg",
            provider_used="ELEVENLABS",
            character_count=45,
            duration_estimate_seconds=4.5,
            voice_id="test-voice"
        )
        mock_tts_service.return_value = mock_tts_service_instance
        
        mock_video_service_instance = AsyncMock()
        mock_video_service_instance.generate_video.return_value = MagicMock(
            video_data=b"multi-agent video",
            duration_seconds=12.0,
            job_response=MagicMock(data={"status": "completed", "id": "job-456"})
        )
        mock_video_service.return_value = mock_video_service_instance
        
        # Mock external API calls
        mock_response = MagicMock()
        mock_response.content = b"tts audio for multi-agent"
        mock_response.headers = {"content-type": "audio/mpeg"}
        mock_httpx_post.return_value.__aenter__.return_value = mock_response
        
        # Mock Polly client
        mock_polly = MagicMock()
        mock_boto_client.return_value = mock_polly
        mock_polly.synthesize_speech.return_value = {
            "AudioStream": MagicMock(read=lambda: b"polly multi-agent content"),
            "ContentType": "audio/mpeg",
            "RequestCharacters": 45
        }
        
        # Run multiple agent steps
        # 1. Product analysis
        analyze_event = {
            "task": "analyze",
            "user_id": "user123",
            "job_id": "job456",
            "product": {
                "id": "prod789",
                "title": "Smart Home Device",
                "description": "Revolutionary smart home automation device",
                "price": "$149.99",
                "image_keys": ["device1.jpg"]
            }
        }
        
        analyze_result = await agent_handler(analyze_event, {})
        assert analyze_result["success"] is True
        
        # 2. Market insight
        market_event = {
            "task": "market_insight",
            "user_id": "user123",
            "job_id": "job456",
            "context": {
                "analyze": {
                    "output": {
                        "product_category": "smart_home",
                        "target_audience": "tech_enthusiasts",
                        "key_features": ["automation", "voice_control"],
                        "price_positioning": "mid_range"
                    }
                }
            }
        }
        
        market_result = await agent_handler(market_event, {})
        assert market_result["success"] is True
        
        # 3. Script generation using both analysis and market insight
        script_event = {
            "task": "generate",
            "user_id": "user123",
            "job_id": "job456",
            "product": {
                "id": "prod789",
                "title": "Smart Home Device",
                "price": "$149.99"
            },
            "context": {
                "analyze": analyze_result["output"],
                "market_insight": market_result["output"]
            },
            "adjustments": {
                "target_duration": 12,
                "tone": "innovative"
            }
        }
        
        script_result = await agent_handler(script_event, {})
        assert script_result["success"] is True
        
        # 4. TTS generation
        tts_event = {
            "user_id": "user123",
            "job_id": "job456",
            "tts_script": "Transform your home with our innovative smart device!",
            "tts_ssml": None,
            "voice_gender": "male",
            "voice_style": "innovative",
            "speaking_rate": 1.0,
            "provider": "AUTO"
        }
        
        tts_result = await tts_handler(tts_event, {})
        assert tts_result["success"] is True
        
        # 5. Video generation
        video_event = {
            "user_id": "user123",
            "job_id": "job456",
            "video_prompt": "Modern smart home with innovative devices working seamlessly",
            "audio_s3_key": "user123/job456/voiceover.mp3",
            "aspect_ratio": "9:16",
            "duration": 12
        }
        
        video_result = await video_handler(video_event, {})
        assert video_result["success"] is True
        assert video_result["duration_seconds"] == 12.0