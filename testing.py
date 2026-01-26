import base64
from openai import OpenAI

client = OpenAI(api_key="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")

def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def generate_social_post_content(
    image_path: str,
    company_info: dict
) -> str:
    """
    Takes any social media post image and generates matching content
    based strictly on the company's information.
    """

    image_base64 = encode_image(image_path)

    system_prompt = """
You are a marketing content generator.

Your task:
- Analyze the uploaded social media post image
- Understand its structure (headline, main message, footer/contact)
- Generate ONLY the content required to recreate the same type of post
- Do NOT add extra explanations
- Do NOT add emojis unless present in the image
- Match tone, layout intent, and hierarchy
"""

    user_prompt = f"""
Company Information:
Company Name: {company_info['company_name']}
Email: {company_info['company_email']}
Phone: {company_info['phone_number']}

Company Description:
{company_info['company_information']}

Rules:
- Use ONLY the above company information
- Adapt content to the uploaded image style
- Output clean, ready-to-use text
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
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
        max_tokens=300,
        temperature=0.4
    )

    return response.choices[0].message.content.strip()


# ------------------ USAGE ------------------

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

content = generate_social_post_content(
    image_path="image.png",  # any random social media image
    company_info=company_info
)

print(content)



