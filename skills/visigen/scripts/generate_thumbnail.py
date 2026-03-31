"""
VISIGEN thumbnail generation script.
Wraps the KIE API with face reference support.
Usage: python generate_thumbnail.py <prompt_json_file> <output_file>
"""

import os
import sys
import json
import time
import base64
import requests

ENV_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'infographic-generator', '.env')
REFERENCE_IMAGE_PATH = os.path.join(os.path.dirname(__file__), '..', 'references', 'rich_reference.jpg')


def load_api_key():
    if not os.path.exists(ENV_PATH):
        print(f"ERROR: .env not found at {ENV_PATH}")
        sys.exit(1)
    with open(ENV_PATH, 'r') as f:
        for line in f:
            if line.startswith('KIE_API_KEY='):
                return line.strip().split('=', 1)[1].strip('"\'')
    print("ERROR: KIE_API_KEY not found in .env")
    sys.exit(1)


def encode_image_base64(image_path):
    """Encode a local image to base64 PNG data URI for KIE API image_input.
    Converts JPEG/HEIC to PNG since KIE API only accepts PNG."""
    if not os.path.exists(image_path):
        return None
    try:
        from PIL import Image
        import io
        img = Image.open(image_path).convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        return f"data:image/png;base64,{b64}"
    except ImportError:
        # Fallback: send as-is if Pillow not available
        ext = os.path.splitext(image_path)[1].lower().lstrip('.')
        mime = 'jpeg' if ext in ('jpg', 'jpeg') else ext
        with open(image_path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode('utf-8')
        return f"data:image/{mime};base64,{b64}"


def run():
    if len(sys.argv) < 3:
        print("Usage: python generate_thumbnail.py <prompt_json_file> <output_file>")
        sys.exit(1)

    prompt_file = sys.argv[1]
    output_file = sys.argv[2]

    api_key = load_api_key()

    with open(prompt_file, 'r', encoding='utf-8') as f:
        prompt_json = json.load(f)

    api_parameters = prompt_json.pop("api_parameters", {})
    image_input = prompt_json.pop("image_input", None)

    # Auto-inject face reference if not explicitly set and reference image exists
    if image_input is None:
        image_input = encode_image_base64(REFERENCE_IMAGE_PATH)
        if image_input:
            print(f"Face reference loaded from: {REFERENCE_IMAGE_PATH}")
        else:
            print(f"WARNING: No face reference found at {REFERENCE_IMAGE_PATH}. Generating without face reference.")

    prompt_string = json.dumps(prompt_json) if isinstance(prompt_json, dict) else prompt_json
    # If the prompt_json just has a "prompt" key, extract it
    if isinstance(prompt_json, dict) and "prompt" in prompt_json and len(prompt_json) == 1:
        prompt_string = prompt_json["prompt"]

    url = "https://api.kie.ai/api/v1/jobs/createTask"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "nano-banana-2",
        "input": {
            "prompt": prompt_string,
            "aspect_ratio": api_parameters.get("aspect_ratio", "16:9"),
            "resolution": api_parameters.get("resolution", "2K"),
            "output_format": api_parameters.get("output_format", "png")
        }
    }

    if image_input:
        payload["input"]["image_input"] = image_input

    print("Creating thumbnail task via KIE API...")
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    result = response.json()

    # If face reference was rejected, retry without it
    if isinstance(result, dict) and result.get("code") != 200 and image_input:
        print(f"WARNING: Face reference rejected by API ({result.get('msg')}). Retrying without face reference...")
        payload["input"].pop("image_input", None)
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()

    if not result or not isinstance(result, dict):
        print(f"ERROR: Unexpected API response: {result}")
        sys.exit(1)

    if result.get("code") != 200:
        print(f"ERROR: API error {result.get('code')}: {result.get('msg')}")
        sys.exit(1)

    task_id = (result.get("data") or {}).get("taskId")
    if not task_id:
        print("ERROR: No taskId returned")
        print(json.dumps(result, indent=2))
        sys.exit(1)

    print(f"Task ID: {task_id}. Polling for result...")

    poll_url = "https://api.kie.ai/api/v1/jobs/recordInfo"
    poll_params = {"taskId": task_id}

    for attempt in range(60):
        time.sleep(4)
        try:
            poll_resp = requests.get(poll_url, headers=headers, params=poll_params, timeout=15)
            poll_resp.raise_for_status()
            poll_result = poll_resp.json()
        except Exception as e:
            print(f"Poll {attempt+1} error: {e}")
            continue

        data = poll_result.get("data", {})
        if not data:
            print(f"Poll {attempt+1}: empty data, retrying...")
            continue

        state = data.get("state")
        print(f"Poll {attempt+1}: state = {state}")

        if state in ("success", "completed"):
            result_json = json.loads(data.get("resultJson", "{}"))
            result_urls = result_json.get("resultUrls", [])
            if result_urls:
                image_url = result_urls[0]
                print(f"Downloading from {image_url}")
                img_resp = requests.get(image_url, timeout=30)
                img_resp.raise_for_status()
                os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
                with open(output_file, 'wb') as f:
                    f.write(img_resp.content)
                print(f"Saved to {output_file}")
                sys.exit(0)
            else:
                print("ERROR: No result URLs in response")
                print(json.dumps(data, indent=2))
                sys.exit(1)

        elif state in ("failed", "error"):
            print("ERROR: Task failed.")
            print(json.dumps(data, indent=2))
            sys.exit(1)

    print("ERROR: Timed out waiting for generation")
    sys.exit(1)


if __name__ == "__main__":
    run()
