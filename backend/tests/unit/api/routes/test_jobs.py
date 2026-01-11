from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import pytest
from src.api.main import app  # Assuming the FastAPI app is in src.api.main
from tests.fixtures.factories import create_user, create_product, create_job, create_adjustments


@pytest.fixture
def client():
    """Create test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers():
    """Create authentication headers."""
    return {"Authorization": "Bearer test-token"}


class TestJobRoutes:
    
    def test_list_jobs_empty(self, client, auth_headers):
        """Test listing jobs when none exist."""
        with patch('src.api.jobs.get_jobs_for_user') as mock_get_jobs:
            mock_get_jobs.return_value = []
            
            response = client.get("/jobs", headers=auth_headers)
            assert response.status_code == 200
            assert response.json() == []
    
    def test_list_jobs_with_status_filter(self, client, auth_headers):
        """Test listing jobs with status filter."""
        with patch('src.api.jobs.get_jobs_for_user') as mock_get_jobs:
            user = create_user()
            job = create_job(user_id=user["user_id"], product_id="test-product-id")
            mock_get_jobs.return_value = [job]
            
            response = client.get("/jobs?status=PENDING", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["status"] == "PENDING"
    
    def test_create_job_success(self, client, auth_headers):
        """Test successful job creation."""
        with patch('src.api.jobs.get_product_by_id') as mock_get_product, \
             patch('src.api.jobs.create_job') as mock_create_job, \
             patch('src.api.jobs.start_video_generation_workflow') as mock_start_wf:
            
            user = create_user()
            product = create_product(user_id=user["user_id"])
            job = create_job(user_id=user["user_id"], product_id=product["product_id"])
            
            mock_get_product.return_value = product
            mock_create_job.return_value = job
            mock_start_wf.return_value = {"executionArn": "test-execution-arn"}
            
            response = client.post("/jobs", json={
                "product_id": product["product_id"]
            }, headers=auth_headers)
            assert response.status_code == 201
            data = response.json()
            assert data["job_id"] == job["job_id"]
            assert data["status"] == "PENDING"
    
    def test_create_job_product_not_found(self, client, auth_headers):
        """Test creating job with non-existent product."""
        with patch('src.api.jobs.get_product_by_id') as mock_get_product:
            mock_get_product.return_value = None  # Product not found
            
            response = client.post("/jobs", json={
                "product_id": "non-existent-product-id"
            }, headers=auth_headers)
            assert response.status_code == 404
            assert response.json()["detail"] == "Product not found"
    
    def test_create_job_with_adjustments(self, client, auth_headers):
        """Test creating job with adjustments."""
        with patch('src.api.jobs.get_product_by_id') as mock_get_product, \
             patch('src.api.jobs.create_job') as mock_create_job, \
             patch('src.api.jobs.start_video_generation_workflow') as mock_start_wf:
            
            user = create_user()
            product = create_product(user_id=user["user_id"])
            job = create_job(user_id=user["user_id"], product_id=product["product_id"])
            adjustments = create_adjustments()
            
            mock_get_product.return_value = product
            mock_create_job.return_value = job
            mock_start_wf.return_value = {"executionArn": "test-execution-arn"}
            
            response = client.post("/jobs", json={
                "product_id": product["product_id"],
                "adjustments": adjustments
            }, headers=auth_headers)
            assert response.status_code == 201
            data = response.json()
            assert data["job_id"] == job["job_id"]
            assert data["adjustments"]["background_style"] == adjustments["background_style"]
    
    def test_get_job_success(self, client, auth_headers):
        """Test getting a job successfully."""
        with patch('src.api.jobs.get_job_by_id') as mock_get_job:
            user = create_user()
            job = create_job(user_id=user["user_id"], product_id="test-product-id")
            mock_get_job.return_value = job
            
            response = client.get(f"/jobs/{job['job_id']}", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert data["job_id"] == job["job_id"]
            assert data["status"] == job["status"]
    
    def test_get_job_not_found(self, client, auth_headers):
        """Test getting a non-existent job."""
        with patch('src.api.jobs.get_job_by_id') as mock_get_job:
            mock_get_job.return_value = None  # Job not found
            
            response = client.get("/jobs/non-existent-id", headers=auth_headers)
            assert response.status_code == 404
            assert response.json()["detail"] == "Job not found"
    
    def test_get_job_wrong_user(self, client, auth_headers):
        """Test getting a job owned by another user (403)."""
        with patch('src.api.jobs.get_job_by_id') as mock_get_job:
            other_user = create_user()
            job = create_job(user_id=other_user["user_id"], product_id="test-product-id")  # Different user
            mock_get_job.return_value = job
            
            response = client.get(f"/jobs/{job['job_id']}", headers=auth_headers)
            assert response.status_code == 403
            assert response.json()["detail"] == "Access denied"
    
    def test_regenerate_job_success(self, client, auth_headers):
        """Test successful job regeneration."""
        with patch('src.api.jobs.get_job_by_id') as mock_get_job, \
             patch('src.api.jobs.update_job') as mock_update_job, \
             patch('src.api.jobs.start_video_generation_workflow') as mock_start_wf:
            
            user = create_user()
            job = create_job(user_id=user["user_id"], product_id="test-product-id")
            job["status"] = "COMPLETE"  # Completed job can be regenerated
            updated_job = job.copy()
            updated_job["status"] = "PENDING"
            
            mock_get_job.return_value = job
            mock_update_job.return_value = updated_job
            mock_start_wf.return_value = {"executionArn": "test-execution-arn"}
            
            response = client.post(f"/jobs/{job['job_id']}/regenerate", json={
                "adjustments": create_adjustments()
            }, headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "PENDING"
    
    def test_regenerate_job_not_complete(self, client, auth_headers):
        """Test regenerating a job that is not complete."""
        with patch('src.api.jobs.get_job_by_id') as mock_get_job:
            user = create_user()
            job = create_job(user_id=user["user_id"], product_id="test-product-id")
            job["status"] = "PROCESSING"  # Not complete, shouldn't be regenerable
            mock_get_job.return_value = job
            
            response = client.post(f"/jobs/{job['job_id']}/regenerate", json={
                "adjustments": create_adjustments()
            }, headers=auth_headers)
            assert response.status_code == 400
            assert response.json()["detail"] == "Cannot regenerate job that is not complete"
    
    def test_get_download_url_success(self, client, auth_headers):
        """Test getting video download URL successfully."""
        with patch('src.api.jobs.get_job_by_id') as mock_get_job, \
             patch('src.api.jobs.generate_presigned_video_url') as mock_gen_url:
            
            user = create_user()
            job = create_job(user_id=user["user_id"], product_id="test-product-id")
            job["status"] = "COMPLETE"  # Job must be complete to download
            job["video_url"] = "https://test-videos.s3.amazonaws.com/test-video.mp4"
            
            mock_get_job.return_value = job
            mock_gen_url.return_value = "https://presigned-url.com/test-video.mp4"
            
            response = client.get(f"/jobs/{job['job_id']}/video-download-url", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert "download_url" in data
            assert data["download_url"] == "https://presigned-url.com/test-video.mp4"
    
    def test_get_download_url_not_ready(self, client, auth_headers):
        """Test getting video download URL when video is not ready."""
        with patch('src.api.jobs.get_job_by_id') as mock_get_job:
            user = create_user()
            job = create_job(user_id=user["user_id"], product_id="test-product-id")
            job["status"] = "PROCESSING"  # Not complete yet
            job["video_url"] = None  # No video URL yet
            
            mock_get_job.return_value = job
            
            response = client.get(f"/jobs/{job['job_id']}/video-download-url", headers=auth_headers)
            assert response.status_code == 400
            assert response.json()["detail"] == "Video not ready for download"
    
    def test_create_job_step_function_error(self, client, auth_headers):
        """Test job creation when Step Functions fails."""
        with patch('src.api.jobs.get_product_by_id') as mock_get_product, \
             patch('src.api.jobs.create_job') as mock_create_job, \
             patch('src.api.jobs.start_video_generation_workflow') as mock_start_wf:
            
            user = create_user()
            product = create_product(user_id=user["user_id"])
            job = create_job(user_id=user["user_id"], product_id=product["product_id"])
            
            mock_get_product.return_value = product
            mock_create_job.return_value = job
            mock_start_wf.side_effect = Exception("Step Functions error")
            
            response = client.post("/jobs", json={
                "product_id": product["product_id"]
            }, headers=auth_headers)
            assert response.status_code == 500
            assert "detail" in response.json()