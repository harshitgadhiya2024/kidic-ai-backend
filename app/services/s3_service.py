"""S3 service for file upload and management"""

import logging
import uuid
import boto3
from datetime import datetime
from typing import Optional, Tuple
from botocore.exceptions import ClientError
from app.config import settings

logger = logging.getLogger(__name__)


class S3Service:
    """Service for managing files in AWS S3"""
    
    def __init__(self):
        """Initialize AWS S3 client"""
        # Only initialize if AWS credentials are provided
        if settings.aws_access_key_id and settings.aws_secret_access_key:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_s3_region
            )
            self.bucket_name = settings.aws_s3_bucket_name
            self.region = settings.aws_s3_region
            self.enabled = True
        else:
            self.s3_client = None
            self.bucket_name = None
            self.region = None
            self.enabled = False
            logger.warning("S3 service not configured - AWS credentials missing")
    
    def _generate_unique_filename(self, original_filename: str) -> str:
        """
        Generate a unique filename to prevent collisions
        
        Args:
            original_filename: Original filename from upload
            
        Returns:
            str: Unique filename with timestamp and UUID
        """
        # Get file extension
        file_parts = original_filename.rsplit('.', 1)
        extension = file_parts[1] if len(file_parts) > 1 else ''
        
        # Generate unique filename with timestamp and UUID
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        
        if extension:
            return f"{timestamp}_{unique_id}.{extension}"
        return f"{timestamp}_{unique_id}"
    
    def _get_content_type(self, filename: str) -> str:
        """
        Determine content type based on file extension
        
        Args:
            filename: Name of the file
            
        Returns:
            str: MIME type for the file
        """
        extension = filename.lower().rsplit('.', 1)[-1] if '.' in filename else ''
        
        # Common content types
        content_types = {
            # Images
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'svg': 'image/svg+xml',
            'bmp': 'image/bmp',
            'ico': 'image/x-icon',
            
            # Videos
            'mp4': 'video/mp4',
            'avi': 'video/x-msvideo',
            'mov': 'video/quicktime',
            'wmv': 'video/x-ms-wmv',
            'flv': 'video/x-flv',
            'webm': 'video/webm',
            'mkv': 'video/x-matroska',
            
            # Audio
            'mp3': 'audio/mpeg',
            'wav': 'audio/wav',
            'ogg': 'audio/ogg',
            'aac': 'audio/aac',
            'm4a': 'audio/mp4',
            
            # Documents
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'xls': 'application/vnd.ms-excel',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'ppt': 'application/vnd.ms-powerpoint',
            'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'txt': 'text/plain',
            'csv': 'text/csv',
            
            # Archives
            'zip': 'application/zip',
            'rar': 'application/x-rar-compressed',
            '7z': 'application/x-7z-compressed',
            'tar': 'application/x-tar',
            'gz': 'application/gzip',
            
            # Other
            'json': 'application/json',
            'xml': 'application/xml',
            'html': 'text/html',
            'css': 'text/css',
            'js': 'application/javascript',
        }
        
        return content_types.get(extension, 'application/octet-stream')
    
    def _sanitize_metadata(self, value: str) -> str:
        """
        Sanitize metadata value to contain only ASCII characters
        
        Args:
            value: Original metadata value
            
        Returns:
            ASCII-safe metadata value
        """
        # Encode to ASCII, replacing non-ASCII chars with '?', then decode back
        return value.encode('ascii', 'ignore').decode('ascii')
    
    async def upload_file(
        self,
        file_content: bytes,
        file_name: str,
        content_type: str = 'application/octet-stream',
        folder: str = 'uploads',
        user_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Upload a file to S3
        
        Args:
            file_content: File content as bytes
            file_name: Original file name
            content_type: MIME type of the file (optional, will be auto-detected)
            folder: S3 folder/prefix for organization
            user_id: Optional user ID to organize files by user
            
        Returns:
            Public URL of uploaded file or None if failed
        """
        if not self.enabled:
            logger.error("S3 service not configured - cannot upload file")
            return None
        
        try:
            # Generate unique filename
            unique_filename = self._generate_unique_filename(file_name)
            
            # Construct S3 object key
            key_parts = [folder]
            if user_id:
                key_parts.append(f"user_{user_id}")
            key_parts.append(unique_filename)
            
            object_key = '/'.join(key_parts)
            
            # Auto-detect content type if not provided or is default
            if content_type == 'application/octet-stream':
                content_type = self._get_content_type(file_name)
            
            # Sanitize metadata values to ASCII-only
            safe_filename = self._sanitize_metadata(file_name or "unknown")
            safe_user_id = self._sanitize_metadata(user_id or "anonymous")
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=file_content,
                ContentType=content_type,
                Metadata={
                    'original-filename': safe_filename,
                    'upload-timestamp': datetime.utcnow().isoformat(),
                    'user-id': safe_user_id
                }
            )
            
            # Generate public URL
            file_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{object_key}"
            
            logger.info(f"File uploaded successfully to S3: {file_url}")
            return file_url
            
        except ClientError as e:
            logger.error(f"Failed to upload file to S3: {e.response['Error']['Message']}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error uploading file to S3: {str(e)}")
            return None
    
    async def delete_file(self, file_url: str) -> bool:
        """
        Delete a file from S3 using its URL
        
        Args:
            file_url: S3 URL of the file to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if not self.enabled:
            logger.error("S3 service not configured")
            return False
        
        try:
            # Extract object key from URL
            if self.bucket_name not in file_url:
                logger.error("Invalid file URL - bucket name not found")
                return False
            
            url_parts = file_url.split(f"{self.bucket_name}.s3.{self.region}.amazonaws.com/")
            if len(url_parts) != 2:
                logger.error("Could not parse file URL")
                return False
            
            object_key = url_parts[1]
            
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            
            logger.info(f"File deleted successfully from S3: {object_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete file from S3: {e.response['Error']['Message']}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting file from S3: {str(e)}")
            return False
    
    def get_file_info(self, file_url: str) -> Tuple[bool, str, Optional[dict]]:
        """
        Get metadata information about a file from S3
        
        Args:
            file_url: Public URL of the file
            
        Returns:
            Tuple[bool, str, Optional[dict]]: (success, message, file_info)
        """
        if not self.enabled:
            return False, "S3 service not configured", None
        
        try:
            # Extract object key from URL
            if self.bucket_name not in file_url:
                return False, "Invalid file URL", None
            
            url_parts = file_url.split(f"{self.bucket_name}.s3.{self.region}.amazonaws.com/")
            if len(url_parts) != 2:
                return False, "Could not parse file URL", None
            
            object_key = url_parts[1]
            
            # Get object metadata
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            
            file_info = {
                'size': response.get('ContentLength'),
                'content_type': response.get('ContentType'),
                'last_modified': response.get('LastModified').isoformat() if response.get('LastModified') else None,
                'metadata': response.get('Metadata', {})
            }
            
            return True, "File info retrieved successfully", file_info
            
        except ClientError as e:
            if e.response.get('Error', {}).get('Code') == '404':
                return False, "File not found", None
            error_message = e.response.get('Error', {}).get('Message', str(e))
            return False, f"AWS S3 Error: {error_message}", None
            
        except Exception as e:
            return False, f"Failed to get file info: {str(e)}", None
    
    async def generate_presigned_url(
        self,
        s3_key: str,
        expiration: int = 3600
    ) -> Optional[str]:
        """
        Generate a presigned URL for temporary access to a private file
        
        Args:
            s3_key: S3 key of the file
            expiration: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Presigned URL or None if failed
        """
        if not self.enabled:
            logger.error("S3 service not configured")
            return None
        
        try:
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expiration
            )
            
            return presigned_url
            
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e.response['Error']['Message']}")
            return None


# Global S3 service instance
s3_service = S3Service()
