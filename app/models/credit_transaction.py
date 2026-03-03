"""Credit Transaction database model"""

from datetime import datetime


class CreditTransactionModel:
    """Credit Transaction model representing the credit_transactions collection structure"""

    COLLECTION_NAME = "credit_transactions"

    REASON_PHOTOSHOOT_GENERATION = "Photoshoot generation"

    TYPE_DEBIT = "debit"
    TYPE_CREDIT = "credit"

    @staticmethod
    def create_debit_document(
        user_id: str,
        generation_id: str,
        reason: str = "Photoshoot generation",
        amount: int = 1,
    ) -> dict:
        """Create a new credit debit transaction document"""
        now = datetime.utcnow()
        return {
            "user_id": user_id,
            "generation_id": generation_id,
            "type": CreditTransactionModel.TYPE_DEBIT,
            "amount": amount,
            "reason": reason,
            "created_at": now,
            "updated_at": now,
        }

    @staticmethod
    def create_credit_document(
        user_id: str,
        credit_count: int,
        payment_amount: float,
        reason: str = "Credit purchase",
    ) -> dict:
        """Create a new credit (top-up) transaction document"""
        now = datetime.utcnow()
        return {
            "user_id": user_id,
            "generation_id": None,
            "type": CreditTransactionModel.TYPE_CREDIT,
            "amount": credit_count,
            "payment_amount": payment_amount,
            "reason": reason,
            "created_at": now,
            "updated_at": now,
        }

    @staticmethod
    def serialize_transaction(transaction_doc: dict) -> dict:
        """Serialize credit transaction document for API response"""
        if not transaction_doc:
            return None

        transaction_doc["id"] = str(transaction_doc.pop("_id"))
        transaction_doc["created_at"] = transaction_doc["created_at"].isoformat() if transaction_doc.get("created_at") else None
        transaction_doc["updated_at"] = transaction_doc["updated_at"].isoformat() if transaction_doc.get("updated_at") else None

        return transaction_doc
