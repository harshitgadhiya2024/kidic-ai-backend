"""Kid Photoshoot Generation endpoints"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.core.dependencies import get_db, get_current_user
from app.models.photoshoot_generation import PhotoshootGenerationModel
from app.schemas.photoshoot import (
    PhotoshootGenerationResponse,
    GeneratePhotoshootResponse,
    PhotoshootGenerationListResponse
)
from app.services.photoshoot_service import PhotoshootService
from app.services.s3_service import s3_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/photoshoot", tags=["Photoshoot Generation"])

# Allowed image types and max size
ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp']
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def get_file_extension(filename: str) -> str:
    """Extract file extension from filename"""
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return ''


@router.post("/generate", response_model=GeneratePhotoshootResponse, status_code=status.HTTP_201_CREATED)
async def generate_kid_photoshoot(
    template_id: str = Form(..., description="Template ID to use for generation"),
    kid_image: UploadFile = File(..., description="Kid image file"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Generate a kid photoshoot using a template and kid image
    
    - **template_id**: ID of the template to use
    - **kid_image**: Kid image file (jpg, jpeg, png, webp - max 10MB)
    
    This endpoint:
    1. Validates the template and uploads the kid image to S3
    2. Creates a generation task in the database
    3. Initiates the Seeddream API task
    4. Polls for results in the background
    5. Updates the database with the final S3 URL when complete
    
    Returns the generation record immediately with status "pending" or "processing".
    Use the GET endpoint to check the status and get the result URL.
    """
    try:
        photoshoot_service = PhotoshootService(db)
        
        # Validate file type
        file_ext = get_file_extension(kid_image.filename)
        if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
            )
        
        # Read and validate file size
        kid_image_content = await kid_image.read()
        file_size = len(kid_image_content)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE / 1024 / 1024}MB"
            )
        
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )
        
        # Step 1: Get template data
        template = await photoshoot_service.get_template_by_id(template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found or inactive"
            )
        
        # Step 2: Extract template data
        pass_image_url = template.get("pass_image_url")
        aspect_ratio = template.get("aspect_ratio")
        pose_details = template.get("pose_details")
        cloths_details = template.get("cloths_details")
        
        if not all([pass_image_url, aspect_ratio, pose_details, cloths_details]):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Template is missing required fields"
            )
        
        # Upload kid image to S3
        kid_image_url = await s3_service.upload_file(
            file_content=kid_image_content,
            file_name=kid_image.filename,
            content_type=kid_image.content_type or 'image/png',
            folder="kid_images",
            user_id=current_user.get('id')
        )
        
        if not kid_image_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload kid image to S3"
            )
        
        logger.info(f"Kid image uploaded to S3: {kid_image_url}")
        
        # Create generation record in database
        generations_collection = db[PhotoshootGenerationModel.COLLECTION_NAME]
        generation_doc = PhotoshootGenerationModel.create_generation_document(
            user_id=current_user.get('id'),
            template_id=template_id,
            kid_image_url=kid_image_url,
            status=PhotoshootGenerationModel.STATUS_PENDING
        )
        
        result = await generations_collection.insert_one(generation_doc)
        generation_id = str(result.inserted_id)
        generation_doc["_id"] = result.inserted_id
        
        logger.info(f"Generation record created: {generation_id}")
        
        # Step 3: Create Seeddream task
        success, task_id, error_msg = await photoshoot_service.create_seeddream_task(
            kid_image_url=kid_image_url,
            pass_image_url=pass_image_url,
            aspect_ratio=aspect_ratio,
            cloths_details=cloths_details,
            pose_details=pose_details
        )

        if not success:
            # Mark generation as failed
            await generations_collection.update_one(
                {"_id": ObjectId(generation_id)},
                PhotoshootGenerationModel.mark_as_failed(error_msg or "Failed to create Seeddream task")
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create generation task: {error_msg}"
            )

        # Update generation with task_id and mark as processing
        await generations_collection.update_one(
            {"_id": ObjectId(generation_id)},
            PhotoshootGenerationModel.mark_as_processing(task_id)
        )

        logger.info(f"Generation {generation_id} marked as processing with task_id: {task_id}")

        # Step 4: Start background polling (with Gemini fallback parameters)
        background_tasks.add_task(
            photoshoot_service.poll_task_result,
            task_id=task_id,
            generation_id=generation_id,
            user_id=current_user.get('id'),
            kid_image_url=kid_image_url,
            pass_image_url=pass_image_url,
            aspect_ratio=aspect_ratio,
            cloths_details=cloths_details,
            pose_details=pose_details
        )

        logger.info(f"Background polling started for task {task_id}")

        # Fetch updated generation document
        updated_generation = await generations_collection.find_one({"_id": ObjectId(generation_id)})

        return GeneratePhotoshootResponse(
            success=True,
            message="Photoshoot generation started. Poll the status endpoint to check progress.",
            generation=PhotoshootGenerationResponse(
                **PhotoshootGenerationModel.serialize_generation(updated_generation)
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating photoshoot: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{generation_id}", response_model=dict, status_code=status.HTTP_200_OK)
async def get_generation_status(
    generation_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get the status of a photoshoot generation

    - **generation_id**: ID of the generation to check

    Returns the generation record with current status and result URL (if completed).
    """
    try:
        generations_collection = db[PhotoshootGenerationModel.COLLECTION_NAME]

        # Fetch generation
        generation = await generations_collection.find_one({
            "_id": ObjectId(generation_id),
            "user_id": current_user.get('id')
        })

        if not generation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Generation not found"
            )

        return {
            "success": True,
            "generation": PhotoshootGenerationModel.serialize_generation(generation)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching generation status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch generation status"
        )


@router.get("", response_model=PhotoshootGenerationListResponse, status_code=status.HTTP_200_OK)
async def get_user_generations(
    skip: int = 0,
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get all photoshoot generations for the current user

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return (max 100)

    Returns a list of all generations for the authenticated user.
    """
    try:
        if limit > 100:
            limit = 100

        generations_collection = db[PhotoshootGenerationModel.COLLECTION_NAME]

        # Get total count
        total = await generations_collection.count_documents({"user_id": current_user.get('id')})

        # Fetch generations
        cursor = generations_collection.find(
            {"user_id": current_user.get('id')}
        ).sort("created_at", -1).skip(skip).limit(limit)

        generations = await cursor.to_list(length=limit)

        # Serialize generations
        serialized_generations = [
            PhotoshootGenerationModel.serialize_generation(gen) for gen in generations
        ]

        return PhotoshootGenerationListResponse(
            total=total,
            generations=serialized_generations
        )

    except Exception as e:
        logger.error(f"Error fetching user generations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch generations"
        )

