"""Database models"""

from app.models.user import UserModel
from app.models.otp import OTPModel
from app.models.template import TemplateModel
from app.models.photoshoot_generation import PhotoshootGenerationModel
from app.models.contact_us import ContactUsModel
from app.models.credit_transaction import CreditTransactionModel

__all__ = ["UserModel", "OTPModel", "TemplateModel", "PhotoshootGenerationModel", "ContactUsModel", "CreditTransactionModel"]
