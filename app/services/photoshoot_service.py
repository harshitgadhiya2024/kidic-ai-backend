"""Photoshoot Generation Service"""

import logging
import requests
import json
import asyncio
from typing import Tuple, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from google import genai
from google.genai import types

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

        # Initialize Gemini client
        self.gemini_client = genai.Client(api_key=settings.gemini_api_key)

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
    
    def _convert_aspect_ratio(self, aspect_ratio: str) -> str:
        """Convert aspect ratio to Seeddream format"""
        aspect_ratio_map = {
            "16:9": "landscape_16_9",
            "9:16": "portrait_9_16",
            "1:1": "square_hd",
        }
        return aspect_ratio_map.get(aspect_ratio, "landscape_16_9")
    
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
            # Convert aspect ratio
            converted_aspect_ratio = self._convert_aspect_ratio(aspect_ratio)
            
            # Build prompt
            prompt = self._build_prompt(cloths_details, pose_details)
            
            # Prepare payload
            payload = json.dumps({
                "input": {
                    "image_resolution": "4K",
                    "image_size": converted_aspect_ratio,
                    "prompt": prompt,
                    "image_urls": [kid_image_url, pass_image_url]
                },
                "model": "bytedance/seedream-v4-edit"
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

    def _convert_aspect_ratio_for_gemini(self, aspect_ratio: str) -> str:
        """Convert aspect ratio to Gemini format"""
        # Gemini uses format like "16:9", "9:16", "1:1"
        # Already in correct format, just return as-is
        return aspect_ratio

    async def generate_image_with_gemini(
        self,
        kid_image_url: str,
        pass_image_url: str,
        aspect_ratio: str,
        cloths_details: str,
        pose_details: str,
        generation_id: str,
        user_id: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Generate image using Gemini API (fallback method)

        Returns:
            Tuple[bool, Optional[str], Optional[str]]: (success, s3_url, error_message)
        """
        try:
            logger.info(f"Attempting Gemini generation for generation_id: {generation_id}")

            # Build prompt
            prompt = self._build_prompt(cloths_details, pose_details)

            # Convert aspect ratio for Gemini
            gemini_aspect_ratio = self._convert_aspect_ratio_for_gemini(aspect_ratio)

            # Configure generation
            generate_content_config = types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
                image_config=types.ImageConfig(
                    image_size="4K",
                    aspect_ratio=gemini_aspect_ratio,
                ),
            )

            # Prepare image parts
            parts = []
            for image_url in [kid_image_url, pass_image_url]:
                exten = image_url.split(".")[-1]
                if exten.lower() in ["jpg", "jpeg"]:
                    exten = "jpeg"
                parts.append(types.Part.from_uri(
                    uri=image_url,
                    mime_type=f"image/{exten.lower()}",
                ))

            parts.append(types.Part.from_text(text=prompt))

            contents = [
                types.Content(
                    role="user",
                    parts=parts,
                ),
            ]

            # Generate image
            response = self.gemini_client.models.generate_content(
                model=settings.gemini_model,
                contents=contents,
                config=generate_content_config,
            )

            # Extract image data
            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    logger.info(f"Gemini response text: {part.text}")
                elif part.inline_data is not None:
                    # Get image data
                    image_data = part.inline_data.data

                    # Upload to S3
                    filename = f"{generation_id}_photoshoot_gemini.png"
                    s3_url = await s3_service.upload_file(
                        file_content=image_data,
                        file_name=filename,
                        content_type="image/png",
                        folder="photoshoots",
                        user_id=user_id
                    )

                    if s3_url:
                        logger.info(f"Gemini image uploaded to S3: {s3_url}")
                        return True, s3_url, None
                    else:
                        return False, None, "Failed to upload Gemini image to S3"

            return False, None, "No image data in Gemini response"

        except Exception as e:
            logger.error(f"Error generating image with Gemini: {str(e)}")
            return False, None, str(e)

    async def poll_task_result(
        self,
        task_id: str,
        generation_id: str,
        user_id: str,
        kid_image_url: str,
        pass_image_url: str,
        aspect_ratio: str,
        cloths_details: str,
        pose_details: str,
        max_retries: int = 60,
        retry_interval: int = 5
    ):
        """
        Poll Seeddream API for task result and update database
        Falls back to Gemini if Seeddream fails
        This runs in the background
        """
        try:
            headers = {
                'Authorization': f'Bearer {settings.seeddream_api_key}',
                'Content-Type': 'application/json'
            }

            retry_count = 0

            while retry_count < max_retries:
                try:
                    # Sleep before checking (async)
                    await asyncio.sleep(retry_interval)

                    # Check task status
                    response = requests.get(
                        f"{settings.seeddream_get_task_url}?taskId={task_id}",
                        headers=headers
                    )
                    response.raise_for_status()

                    task_status = response.json().get("data", {}).get("state")

                    if task_status == "success":
                        # Get result URL
                        result_json = response.json().get("data", {}).get("resultJson")
                        result_data = json.loads(result_json)
                        result_url = result_data.get("resultUrls", [])[0]

                        logger.info(f"Task {task_id} completed successfully: {result_url}")

                        # Download and upload to S3
                        s3_url = await self.download_and_upload_to_s3(
                            result_url,
                            user_id,
                            generation_id
                        )

                        if s3_url:
                            # Update database with success
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
                            # Failed to upload to S3
                            await self.generations_collection.update_one(
                                {"_id": ObjectId(generation_id)},
                                PhotoshootGenerationModel.mark_as_failed("Failed to upload result to S3")
                            )

                        return

                    elif task_status == "fail":
                        logger.error(f"Task {task_id} failed, attempting Gemini fallback")

                        # Fallback to Gemini
                        success, s3_url, error_msg = await self.generate_image_with_gemini(
                            kid_image_url=kid_image_url,
                            pass_image_url=pass_image_url,
                            aspect_ratio=aspect_ratio,
                            cloths_details=cloths_details,
                            pose_details=pose_details,
                            generation_id=generation_id,
                            user_id=user_id
                        )

                        if success and s3_url:
                            # Update database with Gemini result
                            await self.generations_collection.update_one(
                                {"_id": ObjectId(generation_id)},
                                PhotoshootGenerationModel.mark_as_completed(
                                    s3_url,
                                    model_used=PhotoshootGenerationModel.MODEL_GEMINI
                                )
                            )
                            logger.info(f"Generation {generation_id} completed with Gemini fallback")
                            await self._deduct_credit(user_id, generation_id)
                        else:
                            # Both Seeddream and Gemini failed
                            await self.generations_collection.update_one(
                                {"_id": ObjectId(generation_id)},
                                PhotoshootGenerationModel.mark_as_failed(
                                    f"Seeddream failed, Gemini fallback also failed: {error_msg}"
                                )
                            )

                        return

                    else:
                        logger.info(f"Task {task_id} status: {task_status} (retry {retry_count}/{max_retries})")
                        retry_count += 1

                except Exception as e:
                    logger.error(f"Error polling task {task_id}: {str(e)}")
                    retry_count += 1

            # Max retries reached - try Gemini fallback
            logger.error(f"Task {task_id} polling timeout after {max_retries} retries, attempting Gemini fallback")

            success, s3_url, error_msg = await self.generate_image_with_gemini(
                kid_image_url=kid_image_url,
                pass_image_url=pass_image_url,
                aspect_ratio=aspect_ratio,
                cloths_details=cloths_details,
                pose_details=pose_details,
                generation_id=generation_id,
                user_id=user_id
            )

            if success and s3_url:
                # Update database with Gemini result
                await self.generations_collection.update_one(
                    {"_id": ObjectId(generation_id)},
                    PhotoshootGenerationModel.mark_as_completed(
                        s3_url,
                        model_used=PhotoshootGenerationModel.MODEL_GEMINI
                    )
                )
                logger.info(f"Generation {generation_id} completed with Gemini fallback after timeout")
                await self._deduct_credit(user_id, generation_id)
            else:
                # Both timeout and Gemini failed
                await self.generations_collection.update_one(
                    {"_id": ObjectId(generation_id)},
                    PhotoshootGenerationModel.mark_as_failed(
                        f"Seeddream timeout, Gemini fallback failed: {error_msg}"
                    )
                )

        except Exception as e:
            logger.error(f"Fatal error in poll_task_result: {str(e)}, attempting Gemini fallback")
            try:
                # Try Gemini as last resort
                success, s3_url, error_msg = await self.generate_image_with_gemini(
                    kid_image_url=kid_image_url,
                    pass_image_url=pass_image_url,
                    aspect_ratio=aspect_ratio,
                    cloths_details=cloths_details,
                    pose_details=pose_details,
                    generation_id=generation_id,
                    user_id=user_id
                )

                if success and s3_url:
                    await self.generations_collection.update_one(
                        {"_id": ObjectId(generation_id)},
                        PhotoshootGenerationModel.mark_as_completed(
                            s3_url,
                            model_used=PhotoshootGenerationModel.MODEL_GEMINI
                        )
                    )
                    logger.info(f"Generation {generation_id} completed with Gemini fallback after error")
                    await self._deduct_credit(user_id, generation_id)
                else:
                    await self.generations_collection.update_one(
                        {"_id": ObjectId(generation_id)},
                        PhotoshootGenerationModel.mark_as_failed(
                            f"Polling error: {str(e)}, Gemini fallback failed: {error_msg}"
                        )
                    )
            except Exception as fallback_error:
                logger.error(f"Gemini fallback also failed: {str(fallback_error)}")
                try:
                    await self.generations_collection.update_one(
                        {"_id": ObjectId(generation_id)},
                        PhotoshootGenerationModel.mark_as_failed(
                            f"Complete failure - Seeddream error: {str(e)}, Gemini error: {str(fallback_error)}"
                        )
                    )
                except:
                    pass

