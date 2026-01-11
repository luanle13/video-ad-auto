from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import pytest
from src.api.main import app  # Assuming the FastAPI app is in src.api.main
from tests.fixtures.factories import create_user, create_product


@pytest.fixture
def client():
    """Create test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers():
    """Create authentication headers."""
    return {"Authorization": "Bearer test-token"}


class TestProductRoutes:
    
    def test_list_products_empty(self, client, auth_headers):
        """Test listing products when none exist."""
        with patch('src.api.products.get_products_for_user') as mock_get_products:
            mock_get_products.return_value = []
            
            response = client.get("/products", headers=auth_headers)
            assert response.status_code == 200
            assert response.json() == []
    
    def test_list_products_with_data(self, client, auth_headers):
        """Test listing products when some exist."""
        with patch('src.api.products.get_products_for_user') as mock_get_products:
            user = create_user()
            product = create_product(user_id=user["user_id"])
            mock_get_products.return_value = [product]
            
            response = client.get("/products", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["title"] == product["title"]
    
    def test_create_product_success(self, client, auth_headers):
        """Test successful product creation."""
        with patch('src.api.products.create_product') as mock_create_product:
            user = create_user()
            product_data = {
                "title": "Test Product",
                "description": "Test Description",
                "price": 29.99,
                "image_keys": ["images/test.jpg"]
            }
            
            created_product = create_product(
                user_id=user["user_id"],
                product_id="test-product-id"
            )
            created_product.update(product_data)
            mock_create_product.return_value = created_product
            
            response = client.post("/products", json=product_data, headers=auth_headers)
            assert response.status_code == 201
            data = response.json()
            assert data["title"] == "Test Product"
            assert data["user_id"] == user["user_id"]
    
    def test_create_product_validation_error(self, client, auth_headers):
        """Test product creation with validation errors."""
        with patch('src.api.products.create_product') as mock_create_product:
            # Mock to raise validation error
            mock_create_product.side_effect = ValueError("Invalid product data")
            
            response = client.post("/products", json={
                "title": "",  # Invalid - empty title
                "description": "Valid description",
                "price": -10,  # Invalid - negative price
                "image_keys": []
            }, headers=auth_headers)
            assert response.status_code == 422
    
    def test_create_product_missing_required_fields(self, client, auth_headers):
        """Test product creation with missing required fields."""
        response = client.post("/products", json={
            "title": "Test Product"
            # Missing description, price, and image_keys
        }, headers=auth_headers)
        assert response.status_code == 422
    
    def test_get_product_success(self, client, auth_headers):
        """Test getting a product successfully."""
        with patch('src.api.products.get_product_by_id') as mock_get_product:
            user = create_user()
            product = create_product(user_id=user["user_id"])
            mock_get_product.return_value = product
            
            response = client.get(f"/products/{product['product_id']}", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert data["product_id"] == product["product_id"]
            assert data["title"] == product["title"]
    
    def test_get_product_not_found(self, client, auth_headers):
        """Test getting a non-existent product."""
        with patch('src.api.products.get_product_by_id') as mock_get_product:
            mock_get_product.return_value = None  # Product not found
            
            response = client.get("/products/non-existent-id", headers=auth_headers)
            assert response.status_code == 404
            assert response.json()["detail"] == "Product not found"
    
    def test_get_product_wrong_user(self, client, auth_headers):
        """Test getting a product owned by another user (403)."""
        with patch('src.api.products.get_product_by_id') as mock_get_product:
            other_user = create_user()
            product = create_product(user_id=other_user["user_id"])  # Different user
            mock_get_product.return_value = product
            
            response = client.get(f"/products/{product['product_id']}", headers=auth_headers)
            assert response.status_code == 403
            assert response.json()["detail"] == "Access denied"
    
    def test_delete_product_success(self, client, auth_headers):
        """Test successful product deletion."""
        with patch('src.api.products.delete_product') as mock_delete_product:
            user = create_user()
            product = create_product(user_id=user["user_id"])
            mock_delete_product.return_value = True  # Deletion successful
            
            response = client.delete(f"/products/{product['product_id']}", headers=auth_headers)
            assert response.status_code == 204  # No content
    
    def test_delete_product_not_found(self, client, auth_headers):
        """Test deleting a non-existent product."""
        with patch('src.api.products.delete_product') as mock_delete_product:
            mock_delete_product.return_value = False  # Product not found
            
            response = client.delete("/products/non-existent-id", headers=auth_headers)
            assert response.status_code == 404
            assert response.json()["detail"] == "Product not found"
    
    def test_delete_product_wrong_user(self, client, auth_headers):
        """Test deleting a product owned by another user (403)."""
        with patch('src.api.products.delete_product') as mock_delete_product:
            other_user = create_user()
            product = create_product(user_id=other_user["user_id"])  # Different user
            mock_delete_product.return_value = False  # Access denied
            
            response = client.delete(f"/products/{product['product_id']}", headers=auth_headers)
            assert response.status_code == 403
            assert response.json()["detail"] == "Access denied"
    
    def test_get_upload_url_success(self, client, auth_headers):
        """Test getting S3 upload URL successfully."""
        with patch('src.api.products.generate_presigned_url') as mock_generate_url:
            mock_generate_url.return_value = {
                "key": "uploads/test-image.jpg",
                "url": "https://test-bucket.s3.amazonaws.com/uploads/test-image.jpg",
                "fields": {
                    "AWSAccessKeyId": "test-key",
                    "policy": "test-policy",
                    "signature": "test-signature"
                }
            }
            
            response = client.post("/products/upload-url", json={
                "filename": "test-image.jpg",
                "content_type": "image/jpeg"
            }, headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert "key" in data
            assert "url" in data
            assert "fields" in data
            assert data["key"] == "uploads/test-image.jpg"