from PIL import Image
from io import BytesIO

from google import genai
from google.genai import types

client = genai.Client(
    api_key="AIzaSyBZ3EMW0SQQpbsY3IrAZXGC8TH5eXEiIZ4",
)

model = "gemini-3-pro-image-preview"

generate_content_config = types.GenerateContentConfig(
    response_modalities=[
        "IMAGE",
        "TEXT",
    ],
    image_config=types.ImageConfig(
        image_size="4K",
        aspect_ratio="16:9",
    ),
)

def save_binary_file(file_name, data):
    f = open(file_name, "wb")
    f.write(data)
    f.close()
    print(f"File saved to to: {file_name}")


def generate_image(prompt, image_urls):
    parts = []
    for image_url in image_urls:
        exten = image_url.split(".")[-1]
        if exten.lower() in ["jpg", "jpeg"]:
            exten = "jpeg"
        parts.append(types.Part.from_uri(
            uri=image_url,
            mime_type=f"image/{exten.lower()}",
        ))
    
    parts.append(types.Part.from_text(text=prompt))

    contents = [
        types.Content(
            role="user",
            parts=parts,
        ),
    ]
    
    try:
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=generate_content_config,
        )
        for part in response.candidates[0].content.parts:
            if part.text is not None:
                print(part.text)
            elif part.inline_data is not None:
                output_filename = f"{uuid.uuid4()}_photoshoot_{unique_num + 1}.png"
                image = Image.open(BytesIO(part.inline_data.data))
                image.save(output_filename)
                print(f"stored image: {output_filename}")
                return output_filename

        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

