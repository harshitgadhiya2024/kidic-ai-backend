#!/usr/bin/env python3
"""
Pre-Wedding Photoshoot Generator
Standalone script to generate pre-wedding photoshoots from groom and bride images
"""

import os
import sys
import json
import time
import uuid
import boto3
import requests
from PIL import Image
from io import BytesIO
from typing import Optional, List
from botocore.exceptions import ClientError
from google import genai
from google.genai import types


# ==================== CONFIGURATION ====================
class Config:
    """Configuration for the pre-wedding photoshoot generator"""
    
    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID = "AKIAVXREEUVCE4BD4DH3"
    AWS_SECRET_ACCESS_KEY = "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"
    AWS_S3_BUCKET_NAME = "aavishailabs-uploads-prod"
    AWS_S3_REGION = "eu-north-1"
    
    # Seeddream API Configuration
    SEEDDREAM_API_KEY = "d0a556f31b9db608e6b02afd9b9d8602"
    SEEDDREAM_CREATE_TASK_URL = "https://api.kie.ai/api/v1/jobs/createTask"
    SEEDDREAM_GET_TASK_URL = "https://api.kie.ai/api/v1/jobs/recordInfo"
    
    # Gemini API Configuration (Fallback)
    GEMINI_API_KEY = "AIzaSyBZ3EMW0SQQpbsY3IrAZXGC8TH5eXEiIZ4"
    GEMINI_MODEL = "gemini-3-pro-image-preview"


# ==================== PRE-WEDDING PHOTOSHOOT DETAILS ====================
class PreWeddingDetails:
    """Pre-wedding photoshoot configuration details"""
    
    BACKGROUND = "A vibrant artistic wall mural with a Mediterranean street-art aesthetic. The wall is painted in shades of turquoise, teal, and aqua blue with a mosaic tile texture. Large hand-painted sunflower and floral mandala patterns in warm tones of yellow, orange, beige, and brown are spread across the wall. A white arched window with teal-blue wooden frames appears on the left side, giving a European coastal town vibe. Bright daylight, clear shadows, colorful and cheerful atmosphere, artistic urban backdrop, high detail, realistic texture."
    
    POSE = """
    A couple standing casually facing each other, holding hands naturally. The man is leaning slightly against the wall with one leg bent and relaxed posture, looking at the woman with a soft smile. The woman stands confidently, body slightly angled toward the man, smiling back. Their hands meet at the center, creating a balanced and romantic composition. Natural candid pose, not stiff, lifestyle photography style.
    
    Camera & Framing
    Full-body shot, eye-level camera angle, vertical composition, centered subjects with decorative mural filling the background, shallow depth of field but background still visible.
    """
    
    CLOTHING = """
    Man Clothing
    Man wearing a solid black full-sleeve casual shirt, buttoned up, fitted but comfortable. Light beige chinos with a clean tailored look. Dark casual shoes suitable for walking. Modern urban casual style, minimalistic, neutral color palette, no logos, clean and neat appearance.
    
    Woman Clothing
    Woman wearing a simple yet elegant black short dress with long sleeves. Dress has a relaxed fit, modest neckline, and ends above the knees. Minimalist fashion style, modern casual look, suitable for outdoor lifestyle photography.
    """
    
    ORNAMENTS = """
    women ornaments
    Woman wearing a wristwatch on one hand. No heavy jewelry. Minimal makeup, natural look suitable for daytime outdoor photography.
    
    man ornaments
    Man wearing a simple watch on one wrist. No heavy jewelry. Minimal makeup, natural look suitable for daytime outdoor photography.
    """
    
    LIGHTING_AND_MOOD = """
    Bright natural sunlight, soft shadows on the ground, warm daylight tones. Fresh, cheerful, romantic, travel-photo vibe. Realistic skin tones, high clarity, DSLR-quality photography, cinematic yet natural.
    """


# ==================== S3 SERVICE ====================
class S3Service:
    """Service for uploading files to AWS S3"""
    
    def __init__(self):
        if not Config.AWS_ACCESS_KEY_ID or not Config.AWS_SECRET_ACCESS_KEY:
            print("⚠️  Warning: AWS credentials not configured. S3 upload will fail.")
            self.enabled = False
            return
        
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
            region_name=Config.AWS_S3_REGION
        )
        self.bucket_name = Config.AWS_S3_BUCKET_NAME
        self.region = Config.AWS_S3_REGION
        self.enabled = True
    
    def upload_file_from_path(
        self,
        file_path: str,
        folder: str = "pre-wedding-uploads"
    ) -> Optional[str]:
        """
        Upload a file from local path to S3 and return public URL
        
        Args:
            file_path: Local path to the file
            folder: S3 folder/prefix
        
        Returns:
            Public URL of uploaded file or None if failed
        """
        if not self.enabled:
            print("✗ S3 service not configured")
            return None
        
        try:
            # Read file content
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # Get filename and extension
            filename = os.path.basename(file_path)
            file_ext = os.path.splitext(file_path)[1]
            
            # Generate unique filename
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            object_key = f"{folder}/{unique_filename}"
            
            # Determine content type
            content_type = self._get_content_type(file_ext)

            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=file_content,
                ContentType=content_type
            )

            # Generate public URL
            file_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{object_key}"
            print(f"✓ File uploaded to S3: {file_url}")
            return file_url

        except FileNotFoundError:
            print(f"✗ File not found: {file_path}")
            return None
        except ClientError as e:
            print(f"✗ Failed to upload to S3: {e}")
            return None
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
            return None

    def _get_content_type(self, file_ext: str) -> str:
        """Determine content type based on file extension"""
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
        }
        return content_types.get(file_ext.lower(), 'application/octet-stream')


# ==================== IMAGE GENERATION SERVICE ====================
class ImageGenerationService:
    """Service for generating images using Seeddream and Gemini APIs"""

    def __init__(self):
        self.seeddream_api_key = Config.SEEDDREAM_API_KEY
        self.seeddream_create_url = Config.SEEDDREAM_CREATE_TASK_URL
        self.seeddream_get_url = Config.SEEDDREAM_GET_TASK_URL

        # Initialize Gemini client
        self.gemini_client = genai.Client(api_key=Config.GEMINI_API_KEY)
        self.gemini_model = Config.GEMINI_MODEL

    def generate_with_seeddream(
        self,
        image_urls: List[str],
        prompt: str,
        aspect_ratio: str = "9:16"
    ) -> Optional[str]:
        """
        Generate image using Seeddream API

        Args:
            image_urls: List of reference image URLs
            prompt: Generation prompt
            aspect_ratio: Image aspect ratio (16:9, 9:16, 1:1)

        Returns:
            Local path to generated image or None if failed
        """
        # Convert aspect ratio
        aspect_ratio_map = {
            "16:9": "landscape_16_9",
            "9:16": "portrait_16_9",
            "1:1": "square_hd"
        }
        seeddream_aspect_ratio = aspect_ratio_map.get(aspect_ratio, "landscape_16_9")

        try:
            # Create task
            payload = json.dumps({
                "input": {
                    "image_resolution": "4K",
                    "image_size": seeddream_aspect_ratio,
                    "prompt": prompt,
                    "image_urls": image_urls
                },
                "model": "bytedance/seedream-v4-edit"
            })

            headers = {
                'Authorization': f'Bearer {self.seeddream_api_key}',
                'Content-Type': 'application/json'
            }

            print("🎨 Creating Seeddream task...")
            response = requests.post(self.seeddream_create_url, headers=headers, data=payload)
            response.raise_for_status()
            print(response.text)

            task_id = response.json().get("data", {}).get("taskId")
            print(f"✓ Task created: {task_id}")

            # Poll for result
            max_retries = 60
            retry_count = 0

            while retry_count < max_retries:
                time.sleep(5)

                response = requests.get(f"{self.seeddream_get_url}?taskId={task_id}", headers=headers)
                response.raise_for_status()
                print(response.text)

                status = response.json().get("data", {}).get("state")

                if status == "success":
                    result = response.json().get("data", {}).get("resultJson")
                    result = json.loads(result)
                    result_url = result.get("resultUrls")[0]

                    print(f"✓ Generation successful!")

                    # Download and save image
                    output_filename = f"{uuid.uuid4()}_prewedding_photoshoot.png"
                    self._download_image(result_url, output_filename)
                    return output_filename

                elif status == "fail":
                    print("✗ Seeddream task failed, falling back to Gemini...")
                    return self.generate_with_gemini(image_urls, prompt, aspect_ratio)

                else:
                    print(f"⏳ Task status: {status} (attempt {retry_count + 1}/{max_retries})")
                    retry_count += 1

            print("✗ Seeddream timeout, falling back to Gemini...")
            return self.generate_with_gemini(image_urls, prompt, aspect_ratio)

        except Exception as e:
            print(f"✗ Seeddream error: {e}")
            print("Falling back to Gemini...")
            # return self.generate_with_gemini(image_urls, prompt, aspect_ratio)

    def generate_with_gemini(
        self,
        image_urls: List[str],
        prompt: str,
        aspect_ratio: str = "9:16"
    ) -> Optional[str]:
        """
        Generate image using Gemini API (fallback)

        Args:
            image_urls: List of reference image URLs
            prompt: Generation prompt
            aspect_ratio: Image aspect ratio

        Returns:
            Local path to generated image or None if failed
        """
        try:
            print("🎨 Generating with Gemini...")

            generate_content_config = types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
                image_config=types.ImageConfig(
                    image_size="4K",
                    aspect_ratio=aspect_ratio,
                ),
            )

            # Build parts for the request
            parts = []
            for image_url in image_urls:
                exten = image_url.split(".")[-1]
                if exten.lower() in ["jpg", "jpeg"]:
                    exten = "jpeg"
                parts.append(types.Part.from_uri(
                    file_uri=image_url,
                    mime_type=f"image/{exten.lower()}",
                ))

            parts.append(types.Part.from_text(text=prompt))

            contents = [
                types.Content(
                    role="user",
                    parts=parts,
                ),
            ]

            # Generate content
            response = self.gemini_client.models.generate_content(
                model=self.gemini_model,
                contents=contents,
                config=generate_content_config,
            )

            # Extract and save image
            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    print(part.text)
                elif part.inline_data is not None:
                    output_filename = f"{uuid.uuid4()}_prewedding_photoshoot.png"
                    image = Image.open(BytesIO(part.inline_data.data))
                    image.save(output_filename)
                    print(f"✓ Image saved: {output_filename}")
                    return output_filename

            return None

        except Exception as e:
            print(f"✗ Gemini error: {e}")
            return None

    def _download_image(self, url: str, filename: str):
        """Download image from URL and save to file"""
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        print(f"✓ Image saved: {filename}")


# ==================== PROMPT BUILDER ====================
class PromptBuilder:
    """Build prompts for pre-wedding photoshoot generation"""

    @staticmethod
    def build_prewedding_prompt() -> str:
        """Build the complete pre-wedding photoshoot prompt"""
        details = PreWeddingDetails

        prompt = f"""
A photorealistic pre-wedding photoshoot of a couple (groom and bride) from the provided reference images.

[SUBJECT DETAILS]
Subject: The groom and bride from the provided reference images.
Expression: Natural, romantic, joyful expressions, looking at each other or camera as described in pose.

[POSE DETAILS]
{details.POSE}

[CLOTHING DETAILS]
{details.CLOTHING}

[ORNAMENTS & ACCESSORIES]
{details.ORNAMENTS}

[BACKGROUND & ENVIRONMENT]
{details.BACKGROUND}

[LIGHTING & MOOD]
{details.LIGHTING_AND_MOOD}

[STYLE & QUALITY]
High resolution, 8k, photorealistic, professional photography, cinematic lighting, sharp focus, highly detailed texture, DSLR quality, natural color grading, romantic atmosphere.
"""
        return prompt.strip()


# ==================== MAIN WORKFLOW ====================
class PreWeddingPhotoshootGenerator:
    """Main class for pre-wedding photoshoot generation workflow"""

    def __init__(self):
        self.s3_service = S3Service()
        self.image_service = ImageGenerationService()

    def generate_photoshoot(
        self,
        groom_image_path: str,
        bride_image_path: str,
        aspect_ratio: str = "9:16"
    ) -> Optional[str]:
        """
        Complete workflow to generate pre-wedding photoshoot

        Args:
            groom_image_path: Local path to groom's image
            bride_image_path: Local path to bride's image
            aspect_ratio: Desired aspect ratio (16:9, 9:16, 1:1)

        Returns:
            Path to generated photoshoot image or None if failed
        """
        print("\n" + "="*60)
        print("PRE-WEDDING PHOTOSHOOT GENERATOR")
        print("="*60 + "\n")

        # Step 1: Validate input files
        print("📋 Step 1: Validating input files...")
        if not os.path.exists(groom_image_path):
            print(f"✗ Groom image not found: {groom_image_path}")
            return None
        if not os.path.exists(bride_image_path):
            print(f"✗ Bride image not found: {bride_image_path}")
            return None
        print("✓ Input files validated\n")

        # Step 2: Upload images to S3
        # print("📋 Step 2: Uploading images to S3...")
        # groom_url = self.s3_service.upload_file_from_path(groom_image_path)
        # if not groom_url:
        #     print("✗ Failed to upload groom image")
        #     return None

        # bride_url = self.s3_service.upload_file_from_path(bride_image_path)
        # if not bride_url:
        #     print("✗ Failed to upload bride image")
        #     return None

        # print(f"✓ Groom image URL: {groom_url}")
        # print(f"✓ Bride image URL: {bride_url}\n")

        # Step 3: Build prompt
        print("📋 Step 3: Building generation prompt...")
        prompt = PromptBuilder.build_prewedding_prompt()
        print("✓ Prompt built\n")

        # Step 4: Generate photoshoot
        print("📋 Step 4: Generating pre-wedding photoshoot...")
        groom_url = "https://aavishailabs-uploads-prod.s3.eu-north-1.amazonaws.com/pre-wedding-uploads/2134ebb8-ff26-422a-8f2e-8f29cee70db8.png"
        bride_url = "https://aavishailabs-uploads-prod.s3.eu-north-1.amazonaws.com/pre-wedding-uploads/e32f6a08-fe3f-40bd-883f-af05971ac490.png"
        image_urls = [groom_url, bride_url]
        output_file = self.image_service.generate_with_seeddream(
            image_urls=image_urls,
            prompt=prompt,
            aspect_ratio=aspect_ratio
        )

        if output_file:
            print(f"\n✅ SUCCESS! Photoshoot generated: {output_file}")
            print("="*60 + "\n")
            return output_file
        else:
            print("\n❌ FAILED to generate photoshoot")
            print("="*60 + "\n")
            return None


# ==================== CLI INTERFACE ====================
def main():
    """Main entry point for CLI usage"""
    print("\n" + "="*60)
    print("PRE-WEDDING PHOTOSHOOT GENERATOR - CLI")
    print("="*60 + "\n")

    groom_path = "groom.png"
    bride_path = "bride.png"
    aspect_ratio = "9:16"

    # Generate photoshoot
    generator = PreWeddingPhotoshootGenerator()
    result = generator.generate_photoshoot(
        groom_image_path=groom_path,
        bride_image_path=bride_path,
        aspect_ratio=aspect_ratio
    )

    if result:
        print(f"🎉 Photoshoot saved to: {result}")
        sys.exit(0)
    else:
        print("❌ Failed to generate photoshoot")
        sys.exit(1)


if __name__ == "__main__":
    main()

