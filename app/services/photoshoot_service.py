"""Photoshoot Generation Service"""

import logging
import requests
import json
import asyncio
from typing import Tuple, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.models.photoshoot_generation import PhotoshootGenerationModel
from app.models.template import TemplateModel
from app.models.user import UserModel
from app.models.credit_transaction import CreditTransactionModel
from app.services.s3_service import s3_service
from app.config import settings

logger = logging.getLogger(__name__)


class PhotoshootService:
    """Service for managing photoshoot generation"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.generations_collection = db[PhotoshootGenerationModel.COLLECTION_NAME]
        self.templates_collection = db[TemplateModel.COLLECTION_NAME]
        self.users_collection = db[UserModel.COLLECTION_NAME]
        self.credit_transactions_collection = db[CreditTransactionModel.COLLECTION_NAME]

    async def _deduct_credit(self, user_id: str, generation_id: str):
        """Deduct 1 credit from the user and record the transaction"""
        try:
            await self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$inc": {"credits": -1}}
            )

            transaction_doc = CreditTransactionModel.create_debit_document(
                user_id=user_id,
                generation_id=generation_id,
                reason=CreditTransactionModel.REASON_PHOTOSHOOT_GENERATION,
            )
            await self.credit_transactions_collection.insert_one(transaction_doc)

            logger.info(f"1 credit deducted for user {user_id}, generation {generation_id}")
        except Exception as e:
            logger.error(f"Failed to deduct credit for user {user_id}, generation {generation_id}: {str(e)}")
    
    async def get_template_by_id(self, template_id: str) -> Optional[dict]:
        """Get template by ID"""
        try:
            template = await self.templates_collection.find_one({
                "_id": ObjectId(template_id),
                "is_active": True
            })
            return template
        except Exception as e:
            logger.error(f"Error fetching template: {str(e)}")
            return None
    
    def _build_prompt(self, cloths_details: str, pose_details: str) -> str:
        """Build the generation prompt"""
        return f"""
    A photorealistic photoshoot of a baby wearing specific clothes and posing as described.
    
    [SUBJECT DETAILS]
    Subject: The baby from the provided reference image.
    Expression: Joyful, engaging smile, looking at camera.
    
    [CLOTHING DETAILS]
    The baby is wearing: {cloths_details}
    
    [POSE DETAILS]
    Pose: {pose_details}
    
    [ENVIRONMENT]
    Background: Use the provided background reference image strictly.
    Lighting: Professional studio lighting, seamless integration with background, soft shadows.
    
    [STYLE & QUALITY]
    High resolution, 8k, photorealistic, cinematic lighting, sharp focus, highly detailed texture.
"""
    
    async def create_seeddream_task(
        self,
        kid_image_url: str,
        pass_image_url: str,
        aspect_ratio: str,
        cloths_details: str,
        pose_details: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Create a Seeddream generation task

        Returns:
            Tuple[bool, Optional[str], Optional[str]]: (success, task_id, error_message)
        """
        try:
            # Build prompt
            prompt = self._build_prompt(cloths_details, pose_details)

            # Prepare payload matching kie.ai API structure
            payload = json.dumps({
                "model": settings.seeddream_model,
                "input": {
                    "prompt": prompt,
                    "image_urls": [kid_image_url, pass_image_url],
                    "aspect_ratio": aspect_ratio,
                    "quality": settings.seeddream_quality
                }
            })

            headers = {
                'Authorization': f'Bearer {settings.seeddream_api_key}',
                'Content-Type': 'application/json'
            }

            # Create task
            response = requests.post(settings.seeddream_create_task_url, headers=headers, data=payload)
            response.raise_for_status()

            task_id = response.json().get("data", {}).get("taskId")

            if not task_id:
                return False, None, "Failed to get task ID from Seeddream API"

            logger.info(f"Seeddream task created: {task_id}")
            return True, task_id, None

        except Exception as e:
            logger.error(f"Error creating Seeddream task: {str(e)}")
            return False, None, str(e)
    
    async def download_and_upload_to_s3(
        self,
        image_url: str,
        user_id: str,
        generation_id: str
    ) -> Optional[str]:
        """
        Download image from URL and upload to S3

        Returns:
            S3 public URL or None if failed
        """
        try:
            # Download image
            response = requests.get(image_url, stream=True)
            response.raise_for_status()

            # Read image content
            image_content = response.content

            # Upload to S3
            filename = f"{generation_id}_photoshoot.png"
            s3_url = await s3_service.upload_file(
                file_content=image_content,
                file_name=filename,
                content_type="image/png",
                folder="photoshoots",
                user_id=user_id
            )

            if s3_url:
                logger.info(f"Image uploaded to S3: {s3_url}")
            else:
                logger.error("Failed to upload image to S3")

            return s3_url

        except Exception as e:
            logger.error(f"Error downloading and uploading image: {str(e)}")
            return None

    async def poll_task_result(
        self,
        task_id: str,
        generation_id: str,
        user_id: str,
        max_retries: int = 60,
        retry_interval: int = 5
    ):
        """
        Poll Seeddream API for task result and update database.
        Runs in the background.
        """
        headers = {
            'Authorization': f'Bearer {settings.seeddream_api_key}',
            'Content-Type': 'application/json'
        }

        retry_count = 0

        try:
            while retry_count < max_retries:
                await asyncio.sleep(retry_interval)

                try:
                    response = requests.get(
                        f"{settings.seeddream_get_task_url}?taskId={task_id}",
                        headers=headers
                    )
                    response.raise_for_status()

                    task_status = response.json().get("data", {}).get("state")

                    if task_status == "success":
                        result_json = response.json().get("data", {}).get("resultJson")
                        result_data = json.loads(result_json)
                        result_url = result_data.get("resultUrls", [])[0]

                        logger.info(f"Task {task_id} completed successfully: {result_url}")

                        s3_url = await self.download_and_upload_to_s3(result_url, user_id, generation_id)

                        if s3_url:
                            await self.generations_collection.update_one(
                                {"_id": ObjectId(generation_id)},
                                PhotoshootGenerationModel.mark_as_completed(
                                    s3_url,
                                    model_used=PhotoshootGenerationModel.MODEL_SEEDDREAM
                                )
                            )
                            logger.info(f"Generation {generation_id} marked as completed")
                            await self._deduct_credit(user_id, generation_id)
                        else:
                            await self.generations_collection.update_one(
                                {"_id": ObjectId(generation_id)},
                                PhotoshootGenerationModel.mark_as_failed("Failed to upload result to S3")
                            )
                        return

                    elif task_status == "fail":
                        logger.error(f"Task {task_id} failed")
                        await self.generations_collection.update_one(
                            {"_id": ObjectId(generation_id)},
                            PhotoshootGenerationModel.mark_as_failed("Seeddream task failed")
                        )
                        return

                    else:
                        logger.info(f"Task {task_id} status: {task_status} (retry {retry_count}/{max_retries})")
                        retry_count += 1

                except Exception as e:
                    logger.error(f"Error polling task {task_id}: {str(e)}")
                    retry_count += 1

            # Max retries reached
            logger.error(f"Task {task_id} polling timeout after {max_retries} retries")
            await self.generations_collection.update_one(
                {"_id": ObjectId(generation_id)},
                PhotoshootGenerationModel.mark_as_failed("Generation timed out")
            )

        except Exception as e:
            logger.error(f"Fatal error in poll_task_result: {str(e)}")
            try:
                await self.generations_collection.update_one(
                    {"_id": ObjectId(generation_id)},
                    PhotoshootGenerationModel.mark_as_failed(f"Unexpected error: {str(e)}")
                )
            except Exception:
                pass

