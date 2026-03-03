"""Credits and Payment endpoints"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.core.dependencies import get_db, get_current_user
from app.models.user import UserModel
from app.models.credit_transaction import CreditTransactionModel
from app.schemas.credits import AddCreditsRequest, AddCreditsResponse, CreditTransactionResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/credits", tags=["Credits"])


@router.post("/add", response_model=AddCreditsResponse, status_code=status.HTTP_201_CREATED)
async def add_credits(
    payload: AddCreditsRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Add credits to the authenticated user's account after a payment

    - **credit_count**: Number of credits to add (must be > 0)
    - **payment_amount**: Amount paid by the user (must be > 0)

    This is a secured endpoint — requires a valid access token.
    Records the transaction in the credit_transactions collection and
    increments the user's credit balance.
    """
    try:
        user_id = current_user.get("id")
        users_collection = db[UserModel.COLLECTION_NAME]
        credit_transactions_collection = db[CreditTransactionModel.COLLECTION_NAME]

        # Record the credit transaction
        transaction_doc = CreditTransactionModel.create_credit_document(
            user_id=user_id,
            credit_count=payload.credit_count,
            payment_amount=payload.payment_amount,
        )
        result = await credit_transactions_collection.insert_one(transaction_doc)
        transaction_doc["_id"] = result.inserted_id

        # Increment user credits
        updated_user = await users_collection.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$inc": {"credits": payload.credit_count}},
            return_document=True
        )

        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        logger.info(
            f"User {user_id} purchased {payload.credit_count} credits "
            f"for {payload.payment_amount}. New balance: {updated_user.get('credits')}"
        )

        serialized = CreditTransactionModel.serialize_transaction(transaction_doc)

        return AddCreditsResponse(
            success=True,
            message=f"{payload.credit_count} credit(s) added successfully.",
            credits_added=payload.credit_count,
            current_credits=updated_user.get("credits", 0),
            transaction=CreditTransactionResponse(**serialized)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding credits for user {current_user.get('id')}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process credit purchase"
        )


@router.get("/transactions", response_model=dict, status_code=status.HTTP_200_OK)
async def get_credit_transactions(
    skip: int = 0,
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get all credit transactions for the authenticated user

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return (max 100)

    Returns both debit (photoshoot usage) and credit (purchase) transactions.
    """
    try:
        if limit > 100:
            limit = 100

        user_id = current_user.get("id")
        credit_transactions_collection = db[CreditTransactionModel.COLLECTION_NAME]

        total = await credit_transactions_collection.count_documents({"user_id": user_id})

        cursor = credit_transactions_collection.find(
            {"user_id": user_id}
        ).sort("created_at", -1).skip(skip).limit(limit)

        transactions = await cursor.to_list(length=limit)
        serialized = [CreditTransactionModel.serialize_transaction(t) for t in transactions]

        return {
            "success": True,
            "total": total,
            "transactions": serialized
        }

    except Exception as e:
        logger.error(f"Error fetching transactions for user {current_user.get('id')}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch credit transactions"
        )
