"""Contact Us endpoints"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.dependencies import get_db, get_current_user
from app.models.contact_us import ContactUsModel
from app.schemas.contact_us import ContactUsRequest, ContactUsCreateResponse, ContactUsResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contact-us", tags=["Contact Us"])


@router.post("", response_model=ContactUsCreateResponse, status_code=status.HTTP_201_CREATED)
async def submit_contact_us(
    payload: ContactUsRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Submit a contact us message

    - **message**: The message content from the user
    - **subject**: The subject of the message

    This is a secured endpoint — requires a valid access token.
    """
    try:
        contact_collection = db[ContactUsModel.COLLECTION_NAME]

        contact_doc = ContactUsModel.create_contact_document(
            user_id=current_user.get("id"),
            message=payload.message,
            subject=payload.subject,
        )

        result = await contact_collection.insert_one(contact_doc)
        contact_doc["_id"] = result.inserted_id

        logger.info(f"Contact us message submitted by user {current_user.get('id')}: {str(result.inserted_id)}")

        serialized = ContactUsModel.serialize_contact(contact_doc)

        return ContactUsCreateResponse(
            success=True,
            message="Your message has been submitted successfully.",
            data=ContactUsResponse(**serialized)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting contact us message: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit contact us message"
        )
