import numpy as np
import torch
import torchvision.transforms as T
from PIL import Image
from torchvision.transforms.functional import InterpolationMode
from transformers import AutoModel, AutoTokenizer
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)

image_path = "/root/InternLM/feikuai/2024-10-23_20-17-28/screenshot_1729685850.png"

def build_transform(input_size):
    MEAN, STD = IMAGENET_MEAN, IMAGENET_STD
    transform = T.Compose([
        T.Lambda(lambda img: img.convert('RGB') if img.mode != 'RGB' else img),
        T.Resize((input_size, input_size), interpolation=InterpolationMode.BICUBIC),
        T.ToTensor(),
        T.Normalize(mean=MEAN, std=STD)
    ])
    return transform

def find_closest_aspect_ratio(aspect_ratio, target_ratios, width, height, image_size):
    best_ratio_diff = float('inf')
    best_ratio = (1, 1)
    area = width * height
    for ratio in target_ratios:
        target_aspect_ratio = ratio[0] / ratio[1]
        ratio_diff = abs(aspect_ratio - target_aspect_ratio)
        if ratio_diff < best_ratio_diff:
            best_ratio_diff = ratio_diff
            best_ratio = ratio
        elif ratio_diff == best_ratio_diff:
            if area > 0.5 * image_size * image_size * ratio[0] * ratio[1]:
                best_ratio = ratio
    return best_ratio

def dynamic_preprocess(image, min_num=1, max_num=12, image_size=448, use_thumbnail=False):
    orig_width, orig_height = image.size
    aspect_ratio = orig_width / orig_height

    # calculate the existing image aspect ratio
    target_ratios = set(
        (i, j) for n in range(min_num, max_num + 1) for i in range(1, n + 1) for j in range(1, n + 1) if
        i * j <= max_num and i * j >= min_num)
    target_ratios = sorted(target_ratios, key=lambda x: x[0] * x[1])

    # find the closest aspect ratio to the target
    target_aspect_ratio = find_closest_aspect_ratio(
        aspect_ratio, target_ratios, orig_width, orig_height, image_size)

    # calculate the target width and height
    target_width = image_size * target_aspect_ratio[0]
    target_height = image_size * target_aspect_ratio[1]
    print(target_width, target_aspect_ratio[0])
    print(target_height, target_aspect_ratio[1])
    blocks = target_aspect_ratio[0] * target_aspect_ratio[1]

    # resize the image
    resized_img = image.resize((target_width, target_height))
    processed_images = []
    for i in range(blocks):
        box = (
            (i % (target_width // image_size)) * image_size,
            (i // (target_width // image_size)) * image_size,
            ((i % (target_width // image_size)) + 1) * image_size,
            ((i // (target_width // image_size)) + 1) * image_size
        )
        # split the image
        split_img = resized_img.crop(box)
        processed_images.append(split_img)
    assert len(processed_images) == blocks
    if use_thumbnail and len(processed_images) != 1:
        thumbnail_img = image.resize((image_size, image_size))
        processed_images.append(thumbnail_img)
    return processed_images

def load_image(image_file, input_size=448, max_num=12):
    image = Image.open(image_file).convert('RGB')
    transform = build_transform(input_size=input_size)
    images = dynamic_preprocess(image, image_size=input_size, use_thumbnail=True, max_num=max_num)
    pixel_values = [transform(image) for image in images]
    pixel_values = torch.stack(pixel_values)
    return pixel_values

# If you want to load a model using multiple GPUs, please refer to the `Multiple GPUs` section.
path = '/root/OS-Atlas-Base-4B'
model = AutoModel.from_pretrained(
    path,
    torch_dtype=torch.bfloat16,
    low_cpu_mem_usage=True,
    trust_remote_code=True).eval().cuda()
tokenizer = AutoTokenizer.from_pretrained(path, trust_remote_code=True, use_fast=False)

# set the max number of tiles in `max_num`
pixel_values = load_image(image_path, max_num=6).to(torch.bfloat16).cuda()
generation_config = dict(max_new_tokens=1024, do_sample=True)


import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# from lmdeploy import pipeline
# from lmdeploy.vl import load_image

# pipe = pipeline('/root/InternLM/InternVL2-2B-starbucks—mini-xml-epoch40-20241031-latest-bbox/') # 40epoch referring

# image_path = "/root/InternLM/feikuai/2024-10-23_20-17-28/screenshot_1729685850.png"
# image = load_image(image_path)

# grounding_info = ['7张好礼劵', '咖啡生活馆,精美星杯送到家', '多人团餐', '省心购', '专星送,来尝奇妙狂欢特饮', '订单', '啡快,在线点，到店取', '送心意', '外卖拼单']
# grounding_info = ['星会员', '首页', '我的']
grounding_info = ['星会员']

original_image = cv2.imread(image_path)

def cv2AddChineseText(img, text, position, textColor, textSize):
    if (isinstance(img, np.ndarray)):  # 判断是否OpenCV图片类型
        img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img)
    fontStyle = ImageFont.truetype(
        "/root/InternLM/code/SimSun.ttf", textSize, encoding="utf-8")
    # 绘制文本
    draw.text(position, text, textColor, font=fontStyle)
    # 转换回OpenCV格式
    return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)

def draw_bounding_boxes(image, boxes, label, scale_x=1, scale_y=1):
    x1, y1, x2, y2 = boxes
    x1, y1, x2, y2 = int(x1 * scale_x), int(y1 * scale_y), int(x2 * scale_x), int(y2 * scale_y)
    
    # 确保坐标不超出图片边界
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(image.shape[1], x2), min(image.shape[0], y2)
    
    cv2.rectangle(image, (x1, y1), (x2, y2), (255, 0, 0), 3)  # 使用红色边界框，宽度为3
    
    text = f"{label}"
    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
    text_x = x1
    text_y = y1 - text_size[1] - 10  # 调整文字位置，使其位于框的左上角
    if text_y < 0:  # 防止文字超出图像上边界
        text_y = y1 + 10
    
    # cv2.rectangle(image, (text_x, text_y), (text_x + text_size[0], text_y + text_size[1] + 10), (255, 255, 255), -1)  # 文字背景
    # cv2.putText(image, text, (text_x, text_y + text_size[1] + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)  # 文字颜色为黑色
    # 中文修正
    image = cv2AddChineseText(image, text, (text_x, text_y + text_size[1] + 5), (0, 0, 0), 20)


    top_left_text = f"({x1}, {y1})"
    bottom_right_text = f"({x2}, {y2})"
    cv2.putText(image, top_left_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)  # 左上角坐标，绿色
    cv2.putText(image, bottom_right_text, (x2, y2 + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)  # 右下角坐标，绿色

    return image

for i in grounding_info:
    # response = pipe(('如果我想要“{}”，需要点击哪个区域, 输入以框坐标[x1, y1, x2, y2]的格式输出'.format(i), image))
    # boxes = eval(response.text)

    # question = "In the screenshot of this web page, please give me the coordinates of the element I want to click on according to my instructions(with point).\n\"'Champions League' link\""
    question = "In this UI screenshot, what is the position of the element corresponding to the command \'{}\' (with bbox)?".format(i)

    response, history = model.chat(tokenizer, pixel_values, question, generation_config, history=None, return_history=True)
    print(f'User: {question}\nAssistant: {response}')
    
    boxes = eval(response.split('[')[-1].split(']')[0])
    scale_x = 1 # 448 1440 448
    scale_y = 1 # 448 3200 896
    # import pdb;pdb.set_trace()
    original_image = draw_bounding_boxes(original_image, boxes, i, scale_x, scale_y)

    output_path = 'screen_output_image_check.jpg'
    cv2.imwrite(output_path, original_image)