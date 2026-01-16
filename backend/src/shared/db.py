"""DynamoDB client and table operations."""
from datetime import datetime, timezone
from typing import Any, TypeVar
from uuid import uuid4
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from pydantic import BaseModel
from src.shared.config import get_settings
from src.shared.exceptions import ConflictError, NotFoundError
from src.shared.logging import get_logger

logger = get_logger(__name__)
T = TypeVar("T", bound=BaseModel)


class DynamoDBClient:
    """DynamoDB client wrapper with typed operations."""

    def __init__(self, dynamodb_resource=None) -> None:
        settings = get_settings()
        self._dynamodb = dynamodb_resource or boto3.resource("dynamodb", region_name=settings.aws_region)
        self._users_table = self._dynamodb.Table(settings.dynamodb_users_table)
        self._products_table = self._dynamodb.Table(settings.dynamodb_products_table)
        self._jobs_table = self._dynamodb.Table(settings.dynamodb_jobs_table)
    
    @staticmethod
    def generate_id() -> str:
        """Generate a unique ID."""
        return str(uuid4())
    
    @staticmethod
    def now_iso() -> str:
        """Get current UTC timestamp in ISO format."""
        return datetime.now(timezone.utc).isoformat()
    
    @staticmethod
    def ttl_timestamp(days: int) -> int:
        """Generate TTL timestamp N days from now."""
        from datetime import timedelta
        return int((datetime.now(timezone.utc) + timedelta(days=days)).timestamp())
    
    # === Users ===
    
    def create_user(self, user_id: str, email: str) -> dict[str, Any]:
        """Create a new user."""
        now = self.now_iso()
        item = {
            "user_id": user_id,
            "email": email,
            "created_at": now,
            "updated_at": now,
        }
        try:
            self._users_table.put_item(
                Item=item,
                ConditionExpression="attribute_not_exists(user_id)",
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise ConflictError(f"User already exists: {user_id}")
            raise
        logger.info("user_created", user_id=user_id, email=email)
        return item
    
    def get_user(self, user_id: str) -> dict[str, Any]:
        """Get user by ID."""
        response = self._users_table.get_item(Key={"user_id": user_id})
        if "Item" not in response:
            raise NotFoundError("User", user_id)
        return response["Item"]
    
    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        """Get user by email using GSI."""
        response = self._users_table.query(
            IndexName="email-index",
            KeyConditionExpression=Key("email").eq(email),
            Limit=1,
        )
        items = response.get("Items", [])
        return items[0] if items else None
    
    # === Products ===
    
    def create_product(
        self,
        user_id: str,
        title: str,
        description: str,
        price: str,
        image_keys: list[str],
    ) -> dict[str, Any]:
        """Create a new product."""
        product_id = self.generate_id()
        now = self.now_iso()
        item = {
            "user_id": user_id,
            "product_id": product_id,
            "title": title,
            "description": description,
            "price": price,
            "image_keys": image_keys,
            "created_at": now,
            "updated_at": now,
        }
        self._products_table.put_item(Item=item)
        logger.info("product_created", user_id=user_id, product_id=product_id)
        return item
    
    def get_product(self, user_id: str, product_id: str) -> dict[str, Any]:
        """Get product by user_id and product_id."""
        response = self._products_table.get_item(
            Key={"user_id": user_id, "product_id": product_id}
        )
        if "Item" not in response:
            raise NotFoundError("Product", product_id)
        return response["Item"]
    
    def list_products(self, user_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """List products for a user."""
        response = self._products_table.query(
            KeyConditionExpression=Key("user_id").eq(user_id),
            Limit=limit,
            ScanIndexForward=False,  # Newest first
        )
        return response.get("Items", [])
    
    def delete_product(self, user_id: str, product_id: str) -> None:
        """Delete a product."""
        self._products_table.delete_item(
            Key={"user_id": user_id, "product_id": product_id}
        )
        logger.info("product_deleted", user_id=user_id, product_id=product_id)

    def add_product_image(
        self, user_id: str, product_id: str, image_id: str
    ) -> dict[str, Any]:
        """Add an image ID to a product's image_keys list."""
        response = self._products_table.update_item(
            Key={"user_id": user_id, "product_id": product_id},
            UpdateExpression="SET image_keys = list_append(image_keys, :img), updated_at = :now",
            ExpressionAttributeValues={
                ":img": [image_id],
                ":now": self.now_iso(),
            },
            ConditionExpression="attribute_exists(user_id)",
            ReturnValues="ALL_NEW",
        )
        logger.info(
            "product_image_added",
            user_id=user_id,
            product_id=product_id,
            image_id=image_id,
        )
        return response["Attributes"]

    # === Jobs ===
    
    def create_job(
        self,
        user_id: str,
        product_id: str,
        adjustments: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new video generation job."""
        job_id = self.generate_id()
        now = self.now_iso()
        item = {
            "user_id": user_id,
            "job_id": job_id,
            "product_id": product_id,
            "status": "PENDING",
            "adjustments": adjustments or {},
            "step_outputs": {},
            "created_at": now,
            "updated_at": now,
            "expires_at": self.ttl_timestamp(days=30),  # 30-day TTL
        }
        self._jobs_table.put_item(Item=item)
        logger.info("job_created", user_id=user_id, job_id=job_id, product_id=product_id)
        return item
    
    def get_job(self, user_id: str, job_id: str) -> dict[str, Any]:
        """Get job by user_id and job_id."""
        response = self._jobs_table.get_item(
            Key={"user_id": user_id, "job_id": job_id}
        )
        if "Item" not in response:
            raise NotFoundError("Job", job_id)
        return response["Item"]
    
    def list_jobs(
        self,
        user_id: str,
        limit: int = 50,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        """List jobs for a user, optionally filtered by status."""
        if status:
            response = self._jobs_table.query(
                IndexName="status-index",
                KeyConditionExpression=Key("user_id").eq(user_id) & Key("status").eq(status),
                Limit=limit,
                ScanIndexForward=False,
            )
        else:
            response = self._jobs_table.query(
                KeyConditionExpression=Key("user_id").eq(user_id),
                Limit=limit,
                ScanIndexForward=False,
            )
        return response.get("Items", [])
    
    def update_job_status(
        self,
        user_id: str,
        job_id: str,
        status: str,
        error_message: str | None = None,
    ) -> dict[str, Any]:
        """Update job status."""
        update_expr = "SET #status = :status, updated_at = :now"
        expr_values: dict[str, Any] = {
            ":status": status,
            ":now": self.now_iso(),
        }
        expr_names = {"#status": "status"}
        
        if error_message:
            update_expr += ", error_message = :error"
            expr_values[":error"] = error_message
        
        response = self._jobs_table.update_item(
            Key={"user_id": user_id, "job_id": job_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
            ReturnValues="ALL_NEW",
        )
        logger.info("job_status_updated", job_id=job_id, status=status)
        return response["Attributes"]
    
    def update_job_step_output(
        self,
        user_id: str,
        job_id: str,
        step_name: str,
        output: dict[str, Any],
    ) -> dict[str, Any]:
        """Update job with step output."""
        response = self._jobs_table.update_item(
            Key={"user_id": user_id, "job_id": job_id},
            UpdateExpression="SET step_outputs.#step = :output, updated_at = :now",
            ExpressionAttributeNames={"#step": step_name},
            ExpressionAttributeValues={
                ":output": output,
                ":now": self.now_iso(),
            },
            ReturnValues="ALL_NEW",
        )
        logger.info("job_step_completed", job_id=job_id, step=step_name)
        return response["Attributes"]
    
    def update_job_video(
        self,
        user_id: str,
        job_id: str,
        video_key: str,
        audio_key: str,
    ) -> dict[str, Any]:
        """Update job with generated video/audio keys."""
        response = self._jobs_table.update_item(
            Key={"user_id": user_id, "job_id": job_id},
            UpdateExpression="""
                SET video_key = :video, 
                    audio_key = :audio, 
                    #status = :status,
                    updated_at = :now
            """,
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":video": video_key,
                ":audio": audio_key,
                ":status": "COMPLETE",
                ":now": self.now_iso(),
            },
            ReturnValues="ALL_NEW",
        )
        logger.info("job_completed", job_id=job_id, video_key=video_key)
        return response["Attributes"]


# Singleton instance
_db_client: DynamoDBClient | None = None


def get_db() -> DynamoDBClient:
    """Get DynamoDB client singleton."""
    global _db_client
    if _db_client is None:
        _db_client = DynamoDBClient()
    return _db_client