import tiktoken
import base64
from PIL import Image
from io import BytesIO
import math, re

def get_image_dims(image):
    image = re.sub(r"data:image\/\w+;base64,", "", image)
    image = Image.open(BytesIO(base64.b64decode(image)))
    return image.size

def calculate_image_token_cost(image, detail="high"):
    LOW_DETAIL_COST = 85
    HIGH_DETAIL_COST_PER_TILE = 170

    # width, height = get_image_dims(image)
    width, height = 1440, 3200

    if detail == "low":
        return LOW_DETAIL_COST

    # Resize logic for images larger than 2048x2048
    if max(width, height) > 2048:
        ratio = 2048 / max(width, height)
        width = int(width * ratio)
        height = int(height * ratio)
    
    print(width, height)
    # Calculate number of tiles needed for high detail
    num_tiles = math.ceil(width / 512) * math.ceil(height / 512)
    print(num_tiles)
    total_tokens = LOW_DETAIL_COST + (HIGH_DETAIL_COST_PER_TILE * num_tiles)

    return total_tokens

# https://platform.openai.com/docs/guides/vision/calculating-costs
base64_image = "data:image/png;base64,..."
token_count = calculate_image_token_cost(base64_image)
print(f"Token数量: {token_count}")