# Pre-Wedding Photoshoot Generator

A standalone Python script to generate professional pre-wedding photoshoots from groom and bride images using AI.

## Features

- 📸 Upload groom and bride images to AWS S3
- 🎨 Generate photorealistic pre-wedding photoshoots
- 🔄 Dual AI engine support (Seeddream + Gemini fallback)
- 🎯 Customizable aspect ratios (Portrait, Landscape, Square)
- 💪 Robust error handling and retry logic
- 🖥️ Interactive CLI interface

## Prerequisites

### Required Python Packages

```bash
pip install boto3 requests pillow google-genai
```

### Environment Variables

Set the following environment variables before running the script:

```bash
# AWS S3 Configuration (Required)
export AWS_ACCESS_KEY_ID="your-access-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
export AWS_S3_BUCKET_NAME="your-bucket-name"
export AWS_S3_REGION="us-east-1"  # Optional, default: us-east-1

# API Keys (Optional - defaults are provided in the script)
export SEEDDREAM_API_KEY="your-seeddream-api-key"
export GEMINI_API_KEY="your-gemini-api-key"
```

## Usage

### Method 1: Interactive Mode

Simply run the script without arguments:

```bash
python pre_wedding_photoshoot_generator.py
```

You'll be prompted to enter:
1. Path to groom's image
2. Path to bride's image
3. Desired aspect ratio (Portrait/Landscape/Square)

### Method 2: Command Line Arguments

```bash
python pre_wedding_photoshoot_generator.py <groom_image_path> <bride_image_path> [aspect_ratio]
```

**Examples:**

```bash
# Portrait mode (9:16) - Default
python pre_wedding_photoshoot_generator.py groom.jpg bride.jpg

# Landscape mode (16:9)
python pre_wedding_photoshoot_generator.py groom.jpg bride.jpg 16:9

# Square mode (1:1)
python pre_wedding_photoshoot_generator.py groom.jpg bride.jpg 1:1
```

## Workflow

The script follows these steps:

1. **Validate Input Files** - Checks if groom and bride images exist
2. **Upload to S3** - Uploads both images to AWS S3 and gets public URLs
3. **Build Prompt** - Creates a detailed prompt with pre-wedding photoshoot specifications
4. **Generate Photoshoot** - Uses Seeddream API (with Gemini as fallback) to generate the image
5. **Save Result** - Downloads and saves the generated photoshoot locally

## Photoshoot Configuration

The script uses predefined pre-wedding photoshoot settings:

- **Background**: Mediterranean street-art aesthetic with vibrant murals
- **Pose**: Casual couple pose, holding hands, natural and romantic
- **Clothing**: Modern casual style (black shirt & beige chinos for groom, black dress for bride)
- **Ornaments**: Minimal jewelry, watches, natural makeup
- **Lighting**: Bright natural sunlight, warm daylight tones
- **Mood**: Fresh, cheerful, romantic, travel-photo vibe

You can customize these settings by modifying the `PreWeddingDetails` class in the script.

## Output

The generated photoshoot will be saved as:
```
<uuid>_prewedding_photoshoot.png
```

Example: `a1b2c3d4-5e6f-7g8h-9i0j-k1l2m3n4o5p6_prewedding_photoshoot.png`

## Error Handling

- If Seeddream API fails, the script automatically falls back to Gemini API
- If S3 upload fails, the script will exit with an error message
- All errors are logged with descriptive messages

## Troubleshooting

### AWS Credentials Error
```
⚠️  ERROR: AWS credentials not configured!
```
**Solution**: Set the required environment variables (see Prerequisites section)

### File Not Found Error
```
✗ Groom image not found: /path/to/image.jpg
```
**Solution**: Verify the image path is correct and the file exists

### S3 Upload Failed
```
✗ Failed to upload to S3
```
**Solution**: Check your AWS credentials, bucket name, and permissions

## API Information

- **Seeddream API**: Primary image generation engine (bytedance/seedream-v4-edit)
- **Gemini API**: Fallback image generation engine (gemini-3-pro-image-preview)

## License

This script is provided as-is for pre-wedding photoshoot generation purposes.

