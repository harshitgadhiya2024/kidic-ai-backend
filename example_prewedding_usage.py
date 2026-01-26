#!/usr/bin/env python3
"""
Example usage of Pre-Wedding Photoshoot Generator
This demonstrates how to use the generator programmatically
"""

import os
from pre_wedding_photoshoot_generator import PreWeddingPhotoshootGenerator

def example_usage():
    """Example of using the pre-wedding photoshoot generator"""
    
    # Set environment variables (if not already set)
    # os.environ["AWS_ACCESS_KEY_ID"] = "your-access-key"
    # os.environ["AWS_SECRET_ACCESS_KEY"] = "your-secret-key"
    # os.environ["AWS_S3_BUCKET_NAME"] = "your-bucket-name"
    # os.environ["AWS_S3_REGION"] = "us-east-1"
    
    # Initialize the generator
    generator = PreWeddingPhotoshootGenerator()
    
    # Example 1: Generate portrait photoshoot (9:16)
    print("\n=== Example 1: Portrait Photoshoot ===")
    result = generator.generate_photoshoot(
        groom_image_path="path/to/groom.jpg",
        bride_image_path="path/to/bride.jpg",
        aspect_ratio="9:16"
    )
    
    if result:
        print(f"✅ Portrait photoshoot saved: {result}")
    
    # Example 2: Generate landscape photoshoot (16:9)
    print("\n=== Example 2: Landscape Photoshoot ===")
    result = generator.generate_photoshoot(
        groom_image_path="path/to/groom.jpg",
        bride_image_path="path/to/bride.jpg",
        aspect_ratio="16:9"
    )
    
    if result:
        print(f"✅ Landscape photoshoot saved: {result}")
    
    # Example 3: Generate square photoshoot (1:1)
    print("\n=== Example 3: Square Photoshoot ===")
    result = generator.generate_photoshoot(
        groom_image_path="path/to/groom.jpg",
        bride_image_path="path/to/bride.jpg",
        aspect_ratio="1:1"
    )
    
    if result:
        print(f"✅ Square photoshoot saved: {result}")


if __name__ == "__main__":
    example_usage()

