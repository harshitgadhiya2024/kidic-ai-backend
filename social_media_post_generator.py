"""
Standalone Social Media Post Generator

This script generates social media posts by:
1. Analyzing a reference image to understand its structure
2. Generating content based on company information
3. Uploading the reference image to S3
4. Generating a new image with the same structure but company-specific content
5. Uploading the generated image to S3

Usage:
    python social_media_post_generator.py --image path/to/image.png --config company_config.json
"""

import os
import sys
import json
import time
import uuid
import base64
import argparse
import requests
from typing import Dict, Optional, Tuple
from io import BytesIO
from PIL import Image

import boto3
from botocore.exceptions import ClientError
from openai import OpenAI
from google import genai
from google.genai import types


# ==================== CONFIGURATION ====================

class Config:
    """Configuration for the social media post generator"""

    # OpenAI Configuration
    OPENAI_API_KEY = "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"

    # Seeddream Configuration
    SEEDDREAM_API_KEY = "b2cf9ed7e326d2680366d702fa58a93c"
    SEEDDREAM_CREATE_TASK_URL = "https://api.kie.ai/api/v1/jobs/createTask"
    SEEDDREAM_GET_TASK_URL = "https://api.kie.ai/api/v1/jobs/recordInfo"

    # Gemini Configuration (Fallback)
    GEMINI_API_KEY = "AIzaSyBZ3EMW0SQQpbsY3IrAZXGC8TH5eXEiIZ4"
    GEMINI_MODEL = "gemini-3-pro-image-preview"

    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID = "AKIAVXREEUVCE4BD4DH3"
    AWS_SECRET_ACCESS_KEY = "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"
    AWS_S3_BUCKET_NAME = "aavishailabs-uploads-prod"
    AWS_S3_REGION = "eu-north-1"

    # Company Branding Colors
    BRAND_COLORS = ["#15355F", "#A99431"]

    # Image Generation Settings
    MAX_RETRIES = 60
    RETRY_DELAY = 5  # seconds
    IMAGE_RESOLUTION = "4K"
    DEFAULT_ASPECT_RATIO = "1:1"


# ==================== S3 SERVICE ====================

class S3Service:
    """Service for uploading files to AWS S3"""

    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
            region_name=Config.AWS_S3_REGION
        )
        self.bucket_name = Config.AWS_S3_BUCKET_NAME
        self.region = Config.AWS_S3_REGION

    def upload_file(
        self,
        file_path: str,
        folder: str = "social-media-posts"
    ) -> Optional[str]:
        """
        Upload a file to S3 and return public URL

        Args:
            file_path: Local path to the file
            folder: S3 folder/prefix

        Returns:
            Public URL of uploaded file or None if failed
        """
        try:
            # Generate unique filename
            file_ext = os.path.splitext(file_path)[1]
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            object_key = f"{folder}/{unique_filename}"

            # Read file content
            with open(file_path, 'rb') as f:
                file_content = f.read()

            # Determine content type
            content_type = 'image/png' if file_ext.lower() == '.png' else 'image/jpeg'

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

        except ClientError as e:
            print(f"✗ Failed to upload file to S3: {e}")
            return None

    def upload_bytes(
        self,
        file_content: bytes,
        filename: str,
        folder: str = "social-media-posts"
    ) -> Optional[str]:
        """
        Upload bytes content to S3 and return public URL

        Args:
            file_content: File content as bytes
            filename: Filename with extension
            folder: S3 folder/prefix

        Returns:
            Public URL of uploaded file or None if failed
        """
        try:
            # Generate unique filename
            file_ext = os.path.splitext(filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            object_key = f"{folder}/{unique_filename}"

            # Determine content type
            content_type = 'image/png' if file_ext.lower() == '.png' else 'image/jpeg'

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

        except ClientError as e:
            print(f"✗ Failed to upload bytes to S3: {e}")
            return None


# ==================== CONTENT GENERATION SERVICE ====================

class ContentGenerator:
    """Service for generating social media post content using OpenAI"""

    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)

    def encode_image(self, image_path: str) -> str:
        """Encode image to base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def generate_content(
        self,
        image_path: str,
        company_info: Dict
    ) -> str:
        """
        Generate social media post content based on reference image and company info

        Args:
            image_path: Path to reference image
            company_info: Dictionary containing company information

        Returns:
            Generated content as string
        """
        print("\n📝 Generating content based on reference image...")

        image_base64 = self.encode_image(image_path)

        system_prompt = """
You are a marketing content generator specialized in social media posts.

Your task:
- Analyze the uploaded social media post image carefully
- Understand its structure (headline, main message, subtext, footer/contact, call-to-action)
- Identify the layout, hierarchy, and content sections
- Generate ONLY the content required to recreate the same type of post with the same structure
- Do NOT add extra explanations or commentary
- Do NOT add emojis unless present in the reference image
- Match the tone, layout intent, and hierarchy exactly
- Keep the same number of sections and text blocks as the reference
"""

        user_prompt = f"""
Company Information:
Company Name: {company_info.get('company_name', 'N/A')}
Email: {company_info.get('company_email', 'N/A')}
Phone: {company_info.get('phone_number', 'N/A')}
Website: {company_info.get('website', 'N/A')}

Company Description:
{company_info.get('company_information', 'N/A')}

Brand Colors: {', '.join(Config.BRAND_COLORS)}

Rules:
- Use ONLY the above company information
- Adapt content to match the uploaded image's exact structure and layout
- Maintain the same visual hierarchy as the reference image
- Output clean, ready-to-use text for each section
- Specify which text goes in which section (headline, body, footer, etc.)
- Keep content concise and impactful like the reference
"""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500,
            temperature=0.4
        )

        content = response.choices[0].message.content.strip()
        print(f"✓ Content generated successfully")
        return content


# ==================== IMAGE GENERATION SERVICE ====================

class ImageGenerator:
    """Service for generating images using Seeddream with Gemini fallback"""

    def __init__(self):
        self.gemini_client = genai.Client(api_key="AIzaSyBZ3EMW0SQQpbsY3IrAZXGC8TH5eXEiIZ4")

    def _convert_aspect_ratio(self, aspect_ratio: str) -> str:
        """Convert aspect ratio to Seeddream format"""
        ratio_map = {
            "16:9": "landscape_16_9",
            "9:16": "portrait_9_16",
            "1:1": "square_hd",
            "4:3": "landscape_4_3",
            "3:4": "portrait_3_4"
        }
        return ratio_map.get(aspect_ratio, "square_hd")

    def generate_with_seeddream(
        self,
        reference_image_url: str,
        content: str,
        aspect_ratio: str = "1:1"
    ) -> Optional[str]:
        """
        Generate image using Seeddream API

        Args:
            reference_image_url: URL of reference image
            content: Generated content for the post
            aspect_ratio: Image aspect ratio

        Returns:
            Path to generated image file or None if failed
        """
        print("\n🎨 Generating image with Seeddream...")

        try:
            # Create prompt for image generation
            prompt = f"""
Create a social media post image with the EXACT SAME structure and layout as the reference image.

CRITICAL REQUIREMENTS:
- Maintain the EXACT SAME layout structure, positioning, and visual hierarchy as the reference
- Use the EXACT SAME design elements (shapes, borders, sections, backgrounds)
- Keep the SAME number of text sections in the SAME positions
- Preserve the SAME visual style and composition

CONTENT TO USE:
{content}

BRANDING:
- Primary Color: {Config.BRAND_COLORS[0]}
- Secondary Color: {Config.BRAND_COLORS[1]}
- Use these colors for backgrounds, accents, and design elements

STYLE:
- Professional, modern, clean design
- High resolution, sharp text
- Maintain readability and visual balance
- Match the reference image's aesthetic exactly
"""

            # Convert aspect ratio
            seeddream_aspect_ratio = self._convert_aspect_ratio(aspect_ratio)

            # Create task payload
            payload = json.dumps({
                "input": {
                    "image_resolution": Config.IMAGE_RESOLUTION,
                    "image_size": seeddream_aspect_ratio,
                    "prompt": prompt,
                    "image_urls": [reference_image_url]
                },
                "model": "bytedance/seedream-v4-edit"
            })

            headers = {
                'Authorization': f'Bearer {Config.SEEDDREAM_API_KEY}',
                'Content-Type': 'application/json'
            }

            # Create task
            response = requests.post(
                Config.SEEDDREAM_CREATE_TASK_URL,
                headers=headers,
                data=payload
            )
            response.raise_for_status()
            task_id = response.json().get("data", {}).get("taskId")
            print(f"  Task created: {task_id}")

            # Poll for result
            retry_count = 0
            while retry_count < Config.MAX_RETRIES:
                time.sleep(Config.RETRY_DELAY)

                response = requests.get(
                    f"{Config.SEEDDREAM_GET_TASK_URL}?taskId={task_id}",
                    headers=headers
                )
                response.raise_for_status()

                status = response.json().get("data", {}).get("state")

                if status == "success":
                    result = response.json().get("data", {}).get("resultJson")
                    result = json.loads(result)
                    result_url = result.get("resultUrls")[0]

                    # Download image
                    output_filename = f"generated_{uuid.uuid4()}.png"
                    img_response = requests.get(result_url, stream=True)
                    img_response.raise_for_status()

                    with open(output_filename, "wb") as f:
                        for chunk in img_response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)

                    print(f"✓ Image generated successfully with Seeddream")
                    return output_filename

                elif status == "fail":
                    print("✗ Seeddream task failed, falling back to Gemini...")
                    return None

                else:
                    retry_count += 1
                    print(f"  Waiting for completion... ({retry_count}/{Config.MAX_RETRIES})")

            print("✗ Seeddream task timed out, falling back to Gemini...")
            return None

        except Exception as e:
            print(f"✗ Seeddream error: {e}")
            return None

    def generate_with_gemini(
        self,
        reference_image_url: str,
        content: str,
        aspect_ratio: str = "1:1"
    ) -> Optional[str]:
        """
        Generate image using Gemini API (fallback)

        Args:
            reference_image_url: URL of reference image
            content: Generated content for the post
            aspect_ratio: Image aspect ratio

        Returns:
            Path to generated image file or None if failed
        """
        print("\n🎨 Generating image with Gemini (fallback)...")

        try:
            # Create prompt for image generation
            prompt = f"""
Create a social media post image with the EXACT SAME structure and layout as the reference image.

CRITICAL REQUIREMENTS:
- Maintain the EXACT SAME layout structure, positioning, and visual hierarchy as the reference
- Use the EXACT SAME design elements (shapes, borders, sections, backgrounds)
- Keep the SAME number of text sections in the SAME positions
- Preserve the SAME visual style and composition

CONTENT TO USE:
{content}

BRANDING:
- Primary Color: {Config.BRAND_COLORS[0]}
- Secondary Color: {Config.BRAND_COLORS[1]}
- Use these colors for backgrounds, accents, and design elements

STYLE:
- Professional, modern, clean design
- High resolution, sharp text
- Maintain readability and visual balance
- Match the reference image's aesthetic exactly
"""

            # Configure Gemini
            generate_content_config = types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
                image_config=types.ImageConfig(
                    image_size="4K",
                    aspect_ratio=aspect_ratio,
                ),
            )

            # Prepare content parts
            parts = [
                types.Part.from_uri(
                    file_uri=reference_image_url,
                    mime_type="image/png",
                ),
                types.Part.from_text(text=prompt)
            ]

            contents = [
                types.Content(
                    role="user",
                    parts=parts,
                ),
            ]

            # Generate image
            response = self.gemini_client.models.generate_content(
                model=Config.GEMINI_MODEL,
                contents=contents,
                config=generate_content_config,
            )

            # Extract image data
            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    print(f"  Gemini response: {part.text}")
                elif part.inline_data is not None:
                    output_filename = f"generated_{uuid.uuid4()}.png"
                    image = Image.open(BytesIO(part.inline_data.data))
                    image.save(output_filename)
                    print(f"✓ Image generated successfully with Gemini")
                    return output_filename

            print("✗ No image data in Gemini response")
            return None

        except Exception as e:
            print(f"✗ Gemini error: {e}")
            return None

    def generate_image(
        self,
        reference_image_url: str,
        content: str,
        aspect_ratio: str = "1:1"
    ) -> Optional[str]:
        """
        Generate image with fallback mechanism (Seeddream -> Gemini)

        Args:
            reference_image_url: URL of reference image
            content: Generated content for the post
            aspect_ratio: Image aspect ratio

        Returns:
            Path to generated image file or None if failed
        """
        # Try Seeddream first
        result = self.generate_with_seeddream(reference_image_url, content, aspect_ratio)

        if result:
            return result

        # Fallback to Gemini
        result = self.generate_with_gemini(reference_image_url, content, aspect_ratio)

        return result


# ==================== MAIN ORCHESTRATOR ====================

class SocialMediaPostGenerator:
    """Main orchestrator for social media post generation"""

    def __init__(self):
        self.s3_service = S3Service()
        self.content_generator = ContentGenerator()
        self.image_generator = ImageGenerator()

    def generate_post(
        self,
        image_path: str,
        company_info: Dict,
        aspect_ratio: str = "1:1"
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Generate a complete social media post

        Args:
            image_path: Path to reference image
            company_info: Dictionary containing company information
            aspect_ratio: Desired aspect ratio for generated image

        Returns:
            Tuple of (generated_content, reference_image_s3_url, generated_image_s3_url)
        """
        print("\n" + "="*60)
        print("🚀 SOCIAL MEDIA POST GENERATOR")
        print("="*60)

        # Step 1: Validate input
        if not os.path.exists(image_path):
            print(f"✗ Error: Image file not found: {image_path}")
            return None, None, None

        print(f"\n📸 Reference Image: {image_path}")
        print(f"🏢 Company: {company_info.get('company_name', 'N/A')}")
        print(f"📐 Aspect Ratio: {aspect_ratio}")

        # Step 2: Generate content based on reference image
        try:
            content = self.content_generator.generate_content(image_path, company_info)
            print(f"\n📄 Generated Content:\n{'-'*60}\n{content}\n{'-'*60}")
        except Exception as e:
            print(f"✗ Error generating content: {e}")
            return None, None, None

        # Step 3: Upload reference image to S3
        print("\n☁️  Uploading reference image to S3...")
        reference_s3_url = self.s3_service.upload_file(
            image_path,
            folder="social-media-posts/references"
        )

        if not reference_s3_url:
            print("✗ Error: Failed to upload reference image to S3")
            return content, None, None

        # Step 4: Generate new image with same structure
        generated_image_path = self.image_generator.generate_image(
            reference_s3_url,
            content,
            aspect_ratio
        )

        if not generated_image_path:
            print("✗ Error: Failed to generate image")
            return content, reference_s3_url, None

        # Step 5: Upload generated image to S3
        print("\n☁️  Uploading generated image to S3...")
        generated_s3_url = self.s3_service.upload_file(
            generated_image_path,
            folder="social-media-posts/generated"
        )

        if not generated_s3_url:
            print("✗ Error: Failed to upload generated image to S3")
            return content, reference_s3_url, None

        # Clean up local generated file
        try:
            os.remove(generated_image_path)
            print(f"  Cleaned up local file: {generated_image_path}")
        except:
            pass

        # Success!
        print("\n" + "="*60)
        print("✅ SOCIAL MEDIA POST GENERATED SUCCESSFULLY!")
        print("="*60)
        print(f"\n📝 Content: Generated")
        print(f"📸 Reference Image S3 URL: {reference_s3_url}")
        print(f"🎨 Generated Image S3 URL: {generated_s3_url}")
        print("\n" + "="*60)

        return content, reference_s3_url, generated_s3_url



# ==================== CLI INTERFACE ====================

def load_company_config(config_path: str) -> Dict:
    """Load company configuration from JSON file"""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"✗ Error loading config file: {e}")
        sys.exit(1)


def validate_environment():
    """Validate that all required environment variables are set"""
    required_vars = {
        'OPENAI_API_KEY': Config.OPENAI_API_KEY,
        'SEEDDREAM_API_KEY': Config.SEEDDREAM_API_KEY,
        'GEMINI_API_KEY': Config.GEMINI_API_KEY,
        'AWS_ACCESS_KEY_ID': Config.AWS_ACCESS_KEY_ID,
        'AWS_SECRET_ACCESS_KEY': Config.AWS_SECRET_ACCESS_KEY,
        'AWS_S3_BUCKET_NAME': Config.AWS_S3_BUCKET_NAME,
    }

    missing_vars = [var for var, value in required_vars.items() if not value]

    if missing_vars:
        print("✗ Error: Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nPlease set these environment variables before running the script.")
        sys.exit(1)


def main():
    company_info = {
        "company_name": "Stylic AI",
        "company_email": "info@stylic.ai",
        "phone_number": "+91-9316727742",
        "website": "https://stylic.ai",
        "company_information": """
            Stylic.ai is an AI-powered fashion imagery and styling platform that uses generative artificial intelligence to produce high-quality fashion visuals for online stores and marketing. It’s designed to replace or augment traditional photography with AI-generated product photos and styled fashion images — saving brands time, money and creative effort.
            
            ✔ Core Concept
            Users upload product assets (like flat photos or text descriptions).
            The AI generates photorealistic visuals — such as model shots, styled outfits, lifestyle imagery, or campaign visuals — automatically.
            Output images are ready to publish on e-commerce platforms or ad campaigns.
            It eliminates the need for expensive photoshoots.
            
            📌 How Stylic.ai Works (Typical Workflow)
            Upload Images or Style Info
            Submit product photos or text descriptions about garments.
            
            AI Processing
            The system uses machine learning and computer vision to understand garments, textures and context.
            
            Output Realistic Visuals
            Automatically generate finished fashion visuals (model-ready, lifestyle scenes, etc.).
            
            This can greatly streamline a brand’s creative pipeline — from product listing visuals to fashion campaigns.
            📈 Business Impact & Value
            A platform like Stylic.ai brings several advantages to fashion brands and e-commerce businesses:

            ⭐ Save Time & Cost
            AI replaces traditional photography — no studio shoots, models, lighting crews, or post-production editing.

            📸 Consistent Visual Style
            Produces uniform, brand-aligned images that fit your aesthetic and campaigns.

            🚀 Faster Product Launches
            Quickly generate visual content for new collections — especially useful for fast fashion and seasonal drops.

            📊 Better Engagement
            High-quality visuals often lead to higher engagement, click-through rates and ultimately conversion rates on e-commerce sites.
        """
    }

    input_img_path = "image.png"
    # Generate post
    generator = SocialMediaPostGenerator()
    content, reference_url, generated_url = generator.generate_post(
        input_img_path,
        company_info,
        "1:1"
    )

    results = {
        'content': content,
        'reference_image_url': reference_url,
        'generated_image_url': generated_url,
        'company_info': company_info,
        'aspect_ratio': "1:1",
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }

    with open("results.json", 'w') as f:
        json.dump(results, f, indent=2)


if __name__ == '__main__':
    main()
