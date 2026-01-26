import requests
import json, time

api_key = "40b52e0679540938b8c8f1741a3a9545"
url = "https://api.kie.ai/api/v1/jobs/createTask"
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

payload = json.dumps({
  "input": {
    "prompt": prompt,
    "aspect_ratio": "16:9",
    "resolution": "2K",
    "input_urls": [
       "https://nehodating-uploads-prod.s3.ca-central-1.amazonaws.com/uploads/user_694653138fb7669cabd4a5f4/20260119_072211_d7886a04.png",
       "https://aavishailabs-uploads-prod.s3.eu-north-1.amazonaws.com/uploads/image/user_696e0e6e78181b3dc6b333e5/20260119_115449_b57f5972.png"
    ]
  },
  "model": "flux-2/flex-image-to-image"
})
headers = {
  'Authorization': f'Bearer {api_key}',
  'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)

# print(response.text)

task_id = response.json().get("data", {}).get("taskId")

print(task_id)

# task_id = "855c249af05a1176349b5ac6c0c55565"

max_retries = 60
retry_count = 0

while retry_count < max_retries:
    try:
        response = requests.get(f"https://api.kie.ai/api/v1/jobs/recordInfo?taskId={task_id}", headers=headers)
        response.raise_for_status()
        status = response.json().get("data", {}).get("state")
        if status == "success":
            result = response.json().get("data", {}).get("resultJson")
            result = json.loads(result)
            result = result.get("resultUrls")[0]
            print(result)
            print("Task completed successfully")
            break
        elif status == "fail":
            print("Task failed")
            print(response.text)
            break
        else:
            print(f"Task status: {status}")
            retry_count += 1
            time.sleep(5)
    except Exception as e:
        print(f"Error: {e}")
        retry_count += 1
        time.sleep(5)


