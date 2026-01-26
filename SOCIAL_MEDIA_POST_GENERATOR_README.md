# Social Media Post Generator

A standalone Python script that generates professional social media posts by analyzing reference images and creating new posts with your company's branding and information.

## 🌟 Features

- **Content Generation**: Analyzes reference images and generates matching content using OpenAI GPT-4
- **Image Generation**: Creates new images with the same structure using Seeddream API
- **Fallback Mechanism**: Automatically falls back to Gemini API if Seeddream fails
- **S3 Integration**: Uploads both reference and generated images to AWS S3
- **Brand Consistency**: Uses your company's brand colors (#15355F, #A99431)
- **Structure Preservation**: Maintains the exact layout and structure of reference images

## 📋 Prerequisites

### Required Python Packages

```bash
pip install openai boto3 pillow requests google-genai
```

### Required API Keys & Credentials

You need the following environment variables set:

- `OPENAI_API_KEY` - OpenAI API key for content generation
- `SEEDDREAM_API_KEY` - Seeddream API key for image generation
- `GEMINI_API_KEY` - Google Gemini API key for fallback image generation
- `AWS_ACCESS_KEY_ID` - AWS access key for S3 uploads
- `AWS_SECRET_ACCESS_KEY` - AWS secret key for S3 uploads
- `AWS_S3_BUCKET_NAME` - S3 bucket name for file storage
- `AWS_S3_REGION` - AWS region (optional, default: us-east-1)

## 🚀 Quick Start

### 1. Set Environment Variables

Create a `.env` file or export variables:

```bash
export OPENAI_API_KEY="your-openai-api-key"
export SEEDDREAM_API_KEY="your-seeddream-api-key"
export GEMINI_API_KEY="your-gemini-api-key"
export AWS_ACCESS_KEY_ID="your-aws-access-key"
export AWS_SECRET_ACCESS_KEY="your-aws-secret-key"
export AWS_S3_BUCKET_NAME="your-s3-bucket-name"
export AWS_S3_REGION="us-east-1"
```

### 2. Prepare Company Configuration

Create a JSON file with your company information (see `company_config_example.json`):

```json
{
  "company_name": "Your Company Name",
  "company_email": "info@yourcompany.com",
  "phone_number": "+1-555-0100",
  "website": "https://yourcompany.com",
  "company_information": "Your company description and key information..."
}
```

### 3. Run the Script

```bash
python social_media_post_generator.py --image reference.png --config company_config.json
```

## 📖 Usage Examples

### Basic Usage with Config File

```bash
python social_media_post_generator.py \
  --image reference_post.png \
  --config company_config.json
```

### With Custom Aspect Ratio

```bash
python social_media_post_generator.py \
  --image reference_post.png \
  --config company_config.json \
  --aspect-ratio 16:9
```

### Inline Company Information (No Config File)

```bash
python social_media_post_generator.py \
  --image reference_post.png \
  --company-name "Acme Corp" \
  --company-email "info@acme.com" \
  --company-phone "+1-555-0100" \
  --company-website "https://acme.com" \
  --company-info "We make great products"
```

### Save Results to JSON

```bash
python social_media_post_generator.py \
  --image reference_post.png \
  --config company_config.json \
  --output results.json
```

## 🎯 How It Works

The script follows a 5-step process:

### Step 1: Input Validation
- Validates the reference image path
- Loads company information from config file or CLI arguments

### Step 2: Content Generation
- Analyzes the reference image structure using OpenAI Vision
- Generates matching content based on your company information
- Maintains the same layout hierarchy and sections

### Step 3: Reference Image Upload
- Uploads the reference image to S3
- Returns a public URL for the reference image

### Step 4: Image Generation (with Fallback)
- **Primary**: Attempts to generate image using Seeddream API
- **Fallback**: If Seeddream fails, uses Gemini API
- Maintains exact same structure as reference image
- Applies your company's brand colors (#15355F, #A99431)

### Step 5: Generated Image Upload
- Uploads the generated image to S3
- Returns a public URL for the generated image
- Cleans up local temporary files

## 🎨 Supported Aspect Ratios

- `1:1` - Square (default)
- `16:9` - Landscape
- `9:16` - Portrait (Stories)
- `4:3` - Standard landscape
- `3:4` - Standard portrait

## 📁 Output

The script provides:

1. **Console Output**: Progress updates and final URLs
2. **Generated Content**: Text content for the social media post
3. **Reference Image S3 URL**: Public URL of uploaded reference image
4. **Generated Image S3 URL**: Public URL of generated social media post

### Optional JSON Output

Use `--output results.json` to save:

```json
{
  "content": "Generated post content...",
  "reference_image_url": "https://bucket.s3.region.amazonaws.com/...",
  "generated_image_url": "https://bucket.s3.region.amazonaws.com/...",
  "company_info": {...},
  "aspect_ratio": "1:1",
  "timestamp": "2026-01-21 10:30:45"
}
```

## 🔧 Configuration

### Brand Colors

The script uses these brand colors by default (defined in the script):
- Primary: `#15355F` (Dark Blue)
- Secondary: `#A99431` (Gold)

To change brand colors, edit the `Config.BRAND_COLORS` in the script.

### Image Generation Settings

- **Resolution**: 4K (high quality)
- **Max Retries**: 60 attempts (5 minutes with 5-second intervals)
- **Retry Delay**: 5 seconds between status checks

## ⚠️ Error Handling

The script includes comprehensive error handling:

- Missing environment variables → Clear error message
- Invalid image path → Validation error
- Seeddream API failure → Automatic fallback to Gemini
- S3 upload failure → Graceful degradation with error messages
- Network issues → Retry mechanism with timeout

## 📝 Notes

- The script preserves the exact structure and layout of reference images
- Generated images maintain the same visual hierarchy
- Content is tailored to your company while matching the reference style
- All generated files are uploaded to S3 for easy access
- Local temporary files are automatically cleaned up

## 🤝 Support

For issues or questions, refer to the main project documentation or contact the development team.

