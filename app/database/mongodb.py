"""MongoDB database connection and management"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class MongoDB:
    """MongoDB connection manager"""
    
    client: AsyncIOMotorClient = None
    database: AsyncIOMotorDatabase = None


# Global MongoDB instance
mongodb_client = MongoDB()


async def connect_to_mongodb():
    """Connect to MongoDB on application startup"""
    try:
        logger.info(f"Connecting to MongoDB at {settings.mongodb_uri}")
        mongodb_client.client = AsyncIOMotorClient(
            settings.mongodb_uri,
            serverSelectionTimeoutMS=5000
        )
        mongodb_client.database = mongodb_client.client[settings.mongodb_db_name]
        
        # Test connection
        await mongodb_client.client.admin.command('ping')
        logger.info(f"Successfully connected to MongoDB database: {settings.mongodb_db_name}")
        
        # Create indexes
        await create_indexes()
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def close_mongodb_connection():
    """Close MongoDB connection on application shutdown"""
    try:
        if mongodb_client.client:
            mongodb_client.client.close()
            logger.info("MongoDB connection closed")
    except Exception as e:
        logger.error(f"Error closing MongoDB connection: {e}")
        raise


async def create_indexes():
    """Create database indexes for optimal performance"""
    try:
        # Users collection indexes
        users_collection = mongodb_client.database.users
        await users_collection.create_index(
            [("email", ASCENDING)], 
            unique=True, 
            name="email_unique_idx"
        )
        await users_collection.create_index(
            [("created_at", ASCENDING)], 
            name="created_at_idx"
        )
        
        # OTP collection indexes
        otp_collection = mongodb_client.database.otps
        await otp_collection.create_index(
            [("email", ASCENDING)], 
            name="email_idx"
        )
        await otp_collection.create_index(
            [("expires_at", ASCENDING)], 
            name="expires_at_idx"
        )
        await otp_collection.create_index(
            [("created_at", ASCENDING)], 
            expireAfterSeconds=3600,  # Auto-delete OTPs after 1 hour
            name="created_at_ttl_idx"
        )
        
        # Templates collection indexes
        templates_collection = mongodb_client.database.templates
        await templates_collection.create_index(
            [("is_active", ASCENDING)],
            name="is_active_idx"
        )
        await templates_collection.create_index(
            [("created_at", ASCENDING)],
            name="created_at_idx"
        )

        # Photoshoot Generations collection indexes
        photoshoot_generations_collection = mongodb_client.database.photoshoot_generations
        await photoshoot_generations_collection.create_index(
            [("user_id", ASCENDING)],
            name="user_id_idx"
        )
        await photoshoot_generations_collection.create_index(
            [("status", ASCENDING)],
            name="status_idx"
        )
        await photoshoot_generations_collection.create_index(
            [("task_id", ASCENDING)],
            name="task_id_idx"
        )
        await photoshoot_generations_collection.create_index(
            [("created_at", ASCENDING)],
            name="created_at_idx"
        )
        await photoshoot_generations_collection.create_index(
            [("user_id", ASCENDING), ("created_at", ASCENDING)],
            name="user_created_idx"
        )

        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.warning(f"Index creation warning: {e}")


def get_database() -> AsyncIOMotorDatabase:
    """Get the database instance"""
    if mongodb_client.database is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongodb first.")
    return mongodb_client.database
