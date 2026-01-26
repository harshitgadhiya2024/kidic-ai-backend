"""Template management endpoints (public APIs)"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.core.dependencies import get_db
from app.models import TemplateModel
from app.schemas.template import (
    CreateTemplateRequest,
    UpdateTemplateRequest,
    TemplateResponse,
    TemplateListResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/templates", tags=["Templates (Public)"])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_template(
    request: CreateTemplateRequest,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Create a new template (Public API)
    
    - **main_image_url**: Main image URL
    - **pass_image_url**: Pass image URL
    - **pose_details**: Description of the pose
    - **cloths_details**: Description of the clothes
    - **aspect_ratio**: Aspect ratio (e.g., '16:9', '1:1', '4:3')
    
    Returns the created template with ID.
    """
    try:
        templates_collection = db[TemplateModel.COLLECTION_NAME]
        
        # Create template document
        template_doc = TemplateModel.create_template_document(
            main_image_url=request.main_image_url,
            pass_image_url=request.pass_image_url,
            pose_details=request.pose_details,
            cloths_details=request.cloths_details,
            aspect_ratio=request.aspect_ratio
        )
        
        # Insert into database
        result = await templates_collection.insert_one(template_doc)
        template_doc["_id"] = result.inserted_id
        
        logger.info(f"Template created: {result.inserted_id}")
        
        return {
            "success": True,
            "message": "Template created successfully",
            "template": TemplateModel.serialize_template(template_doc)
        }
        
    except Exception as e:
        logger.error(f"Error creating template: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating template: {str(e)}"
        )


@router.get("", response_model=dict, status_code=status.HTTP_200_OK)
async def get_all_templates(
    skip: int = Query(0, ge=0, description="Number of templates to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of templates to return"),
    include_inactive: bool = Query(False, description="Include inactive templates"),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get all templates (Public API)
    
    - **skip**: Number of templates to skip (pagination)
    - **limit**: Maximum number of templates to return (max 100)
    - **include_inactive**: Include soft-deleted templates (default: False)
    
    Returns list of templates with pagination.
    """
    try:
        templates_collection = db[TemplateModel.COLLECTION_NAME]
        
        # Build query filter
        query_filter = {} if include_inactive else {"is_active": True}
        
        # Get total count
        total = await templates_collection.count_documents(query_filter)
        
        # Get templates with pagination
        cursor = templates_collection.find(query_filter).skip(skip).limit(limit).sort("created_at", -1)
        templates = await cursor.to_list(length=limit)
        
        # Serialize templates
        serialized_templates = [TemplateModel.serialize_template(t) for t in templates]
        
        return {
            "success": True,
            "total": total,
            "count": len(serialized_templates),
            "skip": skip,
            "limit": limit,
            "templates": serialized_templates
        }
        
    except Exception as e:
        logger.error(f"Error fetching templates: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching templates: {str(e)}"
        )


@router.get("/{template_id}", response_model=dict, status_code=status.HTTP_200_OK)
async def get_template_by_id(
    template_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get a specific template by ID (Public API)
    
    - **template_id**: Template ID
    
    Returns template details if found.
    """
    try:
        templates_collection = db[TemplateModel.COLLECTION_NAME]
        
        # Validate ObjectId
        try:
            obj_id = ObjectId(template_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid template ID format"
            )
        
        # Find template
        template = await templates_collection.find_one({"_id": obj_id})
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        # Check if active
        if not template.get("is_active", False):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found or has been deleted"
            )
        
        return {
            "success": True,
            "template": TemplateModel.serialize_template(template)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching template {template_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching template: {str(e)}"
        )


@router.patch("/{template_id}", response_model=dict, status_code=status.HTTP_200_OK)
async def update_template(
    template_id: str,
    request: UpdateTemplateRequest,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Update a template (Public API)
    
    - **template_id**: Template ID
    - **All fields are optional** - only provided fields will be updated
    
    Returns updated template.
    """
    try:
        templates_collection = db[TemplateModel.COLLECTION_NAME]
        
        # Validate ObjectId
        try:
            obj_id = ObjectId(template_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid template ID format"
            )
        
        # Check if at least one field is provided
        update_data = request.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one field must be provided for update"
            )
        
        # Update template
        result = await templates_collection.update_one(
            {"_id": obj_id, "is_active": True},
            TemplateModel.update_template_document(**update_data)
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found or has been deleted"
            )
        
        # Get updated template
        updated_template = await templates_collection.find_one({"_id": obj_id})
        
        logger.info(f"Template updated: {template_id}")
        
        return {
            "success": True,
            "message": "Template updated successfully",
            "template": TemplateModel.serialize_template(updated_template)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating template {template_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating template: {str(e)}"
        )


@router.delete("/{template_id}", response_model=dict, status_code=status.HTTP_200_OK)
async def delete_template(
    template_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Soft delete a template (Public API)
    
    - **template_id**: Template ID
    
    Marks the template as inactive (is_active = False) instead of permanently deleting it.
    """
    try:
        templates_collection = db[TemplateModel.COLLECTION_NAME]
        
        # Validate ObjectId
        try:
            obj_id = ObjectId(template_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid template ID format"
            )
        
        # Soft delete (set is_active to False)
        result = await templates_collection.update_one(
            {"_id": obj_id, "is_active": True},
            TemplateModel.soft_delete()
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found or already deleted"
            )
        
        logger.info(f"Template soft deleted: {template_id}")
        
        return {
            "success": True,
            "message": "Template deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting template {template_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting template: {str(e)}"
        )
