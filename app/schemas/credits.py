"""Credits / Payment Pydantic schemas"""

from pydantic import BaseModel, Field


class AddCreditsRequest(BaseModel):
    """Request schema for adding credits after a payment"""
    credit_count: int = Field(..., gt=0, description="Number of credits to add")
    payment_amount: float = Field(..., gt=0, description="Amount paid by the user")

    class Config:
        json_schema_extra = {
            "example": {
                "credit_count": 10,
                "payment_amount": 9.99
            }
        }


class CreditTransactionResponse(BaseModel):
    """Response schema for a single credit transaction record"""
    id: str
    user_id: str
    type: str
    amount: int
    payment_amount: float | None = None
    reason: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class AddCreditsResponse(BaseModel):
    """Response schema for the add-credits endpoint"""
    success: bool
    message: str
    credits_added: int
    current_credits: int
    transaction: CreditTransactionResponse
