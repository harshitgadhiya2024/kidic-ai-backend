import requests
import json, time, uuid
from PIL import Image
from io import BytesIO

from google import genai
from google.genai import types

# seeddream configuration
seeddream_api_key = "40b52e0679540938b8c8f1741a3a9545"
seeddream_create_task_url = "https://api.kie.ai/api/v1/jobs/createTask"
seeddream_get_task_url = "https://api.kie.ai/api/v1/jobs/recordInfo"

# gemini configuration
gemini_api_key = "AIzaSyBZ3EMW0SQQpbsY3IrAZXGC8TH5eXEiIZ4"

client = genai.Client(
    api_key=gemini_api_key,
)

model = "gemini-3-pro-image-preview"

# save file in gemini
def save_gemini_binary_file(file_name, data):
    f = open(file_name, "wb")
    f.write(data)
    f.close()
    print(f"File saved to to: {file_name}")

# save file in seeddream
def save_seeddream_file(file_name, file_url):
    response = requests.get(file_url, stream=True)
    response.raise_for_status()

    with open(file_name, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    
    print(f"File saved to to: {file_name}")

# generate image using gemini
def generate_image(prompt, image_urls, aspect_ratio):
    generate_content_config = types.GenerateContentConfig(
        response_modalities=[
            "IMAGE",
            "TEXT",
        ],
        image_config=types.ImageConfig(
            image_size="4K",
            aspect_ratio=aspect_ratio,
        ),
    )


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
                # want to download this image and want to store in s3 bucket and get public url of it
                return output_filename

        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

# main function (using seeddream)
def main_function(image_urls, prompt, aspect_ratio):
    if aspect_ratio == "16:9":
        aspect_ratio = "landscape_16_9"
    elif aspect_ratio == "9:16":
        aspect_ratio = "portrait_9_16"
    elif aspect_ratio == "1:1":
        aspect_ratio = "square_hd"
    else:
        aspect_ratio = "landscape_16_9"
    
    try:
        payload = json.dumps({
            "input": {
                "image_resolution": "4K",
                "image_size": aspect_ratio,
                "prompt": prompt,
                "image_urls": image_urls
            },
            "model": "bytedance/seedream-v4-edit"
        })

        headers = {
            'Authorization': f'Bearer {seeddream_api_key}',
            'Content-Type': 'application/json'
        } 

        try:
            response = requests.request("POST", seeddream_create_task_url, headers=headers, data=payload)
            response.raise_for_status()
            task_id = response.json().get("data", {}).get("taskId")
            print(task_id)


            # pool for result (make it in background)
            max_retries = 60
            retry_count = 0

            while retry_count < max_retries:
                try:
                    response = requests.get(f"{seeddream_get_task_url}?taskId={task_id}", headers=headers)
                    response.raise_for_status()
                    status = response.json().get("data", {}).get("state")
                    if status == "success":
                        result = response.json().get("data", {}).get("resultJson")
                        result = json.loads(result)
                        result = result.get("resultUrls")[0]
                        print(result)
                        output_filename = f"{uuid.uuid4()}_photoshoot.png"
                        save_seeddream_file(output_filename, result)
                        # want to download this image and want to store in s3 bucket and get public url of it
                        retry_count = 100
                        return output_filename

                    elif status == "fail":
                        print("Task failed")
                        retry_count = 100
                        output_filename = generate_image(prompt, image_urls, "16:9")
                        return output_filename
                    else:
                        print(f"{retry_count} Task status: {status}")
                        retry_count += 1
                        time.sleep(5)

                except Exception as e:
                    print(f"Error: {e}")
                    retry_count = 100
                    output_filename = generate_image(prompt, image_urls, "16:9")
                    return output_filename

        except Exception as e:
            print(f"Error: {e}")
            output_filename = generate_image(prompt, image_urls, "16:9")
            return output_filename

    except Exception as e:
        print(f"Error: {e}")
        output_filename = generate_image(prompt, image_urls, "16:9")
        return output_filename


cloth_details = "The baby is dressed in a festive Christmas elf costume consisting of a deep green (forest/emerald green) velvet or plush top with white trim on the collar and cuffs. The outfit has long sleeves with white cuffs creating a classic Santa's helper look. On the head, the baby wears a matching green Santa/elf hat with white trim and a fluffy red pompom attached to the side. The bottom appears to be simple shorts or diaper cover, paired with red and white candy cane striped socks or leg warmers."
pose_details = "The baby is seated on a wooden sleigh in a relaxed, confident pose. The body is positioned at a slight angle with the torso turned toward the camera. One hand rests casually on the rope handle of the sleigh while the other hand is placed on the lap or sleigh edge. The legs are bent naturally with feet positioned comfortably on the sleigh base. The baby's head is upright with a joyful, engaging smile directed at the camera."

prompt = f"""
    A photorealistic photoshoot of a baby wearing specific clothes and posing as described.
    
    [SUBJECT DETAILS]
    Subject: The baby from the provided reference image.
    Expression: Joyful, engaging smile, looking at camera.
    
    [CLOTHING DETAILS]
    The baby is wearing: {cloth_details}
    
    [POSE DETAILS]
    Pose: {pose_details}
    
    [ENVIRONMENT]
    Background: Use the provided background reference image strictly.
    Lighting: Professional studio lighting, seamless integration with background, soft shadows.
    
    [STYLE & QUALITY]
    High resolution, 8k, photorealistic, cinematic lighting, sharp focus, highly detailed texture.
"""

image_urls = [
       "https://nehodating-uploads-prod.s3.ca-central-1.amazonaws.com/uploads/user_694653138fb7669cabd4a5f4/20260119_072211_d7886a04.png",
       "https://aavishailabs-uploads-prod.s3.eu-north-1.amazonaws.com/uploads/image/user_696e0e6e78181b3dc6b333e5/20260119_115449_b57f5972.png"
    ]

main_function(image_urls, prompt, "16:9")

