"""Database models"""

from app.models.user import UserModel
from app.models.otp import OTPModel
from app.models.template import TemplateModel
from app.models.photoshoot_generation import PhotoshootGenerationModel

__all__ = ["UserModel", "OTPModel", "TemplateModel", "PhotoshootGenerationModel"]
