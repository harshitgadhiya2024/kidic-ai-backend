#!/bin/bash

# Pre-Wedding Photoshoot Generator Setup Script

echo "=========================================="
echo "Pre-Wedding Photoshoot Generator Setup"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"
echo ""

# Install required packages
echo "📦 Installing required Python packages..."
pip3 install -r requirements_prewedding.txt

if [ $? -eq 0 ]; then
    echo "✓ Packages installed successfully"
else
    echo "❌ Failed to install packages"
    exit 1
fi

echo ""
echo "=========================================="
echo "Configuration"
echo "=========================================="
echo ""
echo "Please set the following environment variables:"
echo ""
echo "export AWS_ACCESS_KEY_ID='your-access-key-id'"
echo "export AWS_SECRET_ACCESS_KEY='your-secret-access-key'"
echo "export AWS_S3_BUCKET_NAME='your-bucket-name'"
echo "export AWS_S3_REGION='us-east-1'  # Optional"
echo ""
echo "You can add these to your ~/.bashrc or ~/.zshrc file"
echo ""
echo "=========================================="
echo "Usage"
echo "=========================================="
echo ""
echo "Interactive mode:"
echo "  python3 pre_wedding_photoshoot_generator.py"
echo ""
echo "Command line mode:"
echo "  python3 pre_wedding_photoshoot_generator.py groom.jpg bride.jpg 9:16"
echo ""
echo "✅ Setup complete!"
echo ""

