import cv2
from modelscope.pipelines import pipeline
from modelscope.hub.snapshot_download import snapshot_download

from MobileAgent.crop import calculate_size, calculate_iou
from modelscope.pipelines import pipeline
from PIL import Image, ImageDraw
import torch

def remove_boxes(boxes_filt, size, iou_threshold=0.5):
    boxes_to_remove = set()

    for i in range(len(boxes_filt)):
        if calculate_size(boxes_filt[i]) > 0.05*size[0]*size[1]:
            boxes_to_remove.add(i)
        for j in range(len(boxes_filt)):
            if calculate_size(boxes_filt[j]) > 0.05*size[0]*size[1]:
                boxes_to_remove.add(j)
            if i == j:
                continue
            if i in boxes_to_remove or j in boxes_to_remove:
                continue
            iou = calculate_iou(boxes_filt[i], boxes_filt[j])
            if iou >= iou_threshold:
                boxes_to_remove.add(j)

    boxes_filt = [box for idx, box in enumerate(boxes_filt) if idx not in boxes_to_remove]
    
    return boxes_filt

def det(input_image_path, caption, groundingdino_model, box_threshold=0.05, text_threshold=0.5):
    image = Image.open(input_image_path)
    size = image.size

    caption = caption.lower()
    caption = caption.strip()
    if not caption.endswith('.'):
        caption = caption + '.'
    
    inputs = {
        'IMAGE_PATH': input_image_path,
        'TEXT_PROMPT': caption,
        'BOX_TRESHOLD': box_threshold,
        'TEXT_TRESHOLD': text_threshold
    }

    result = groundingdino_model(inputs)
    boxes_filt = result['boxes']

    H, W = size[1], size[0]
    for i in range(boxes_filt.size(0)):
        boxes_filt[i] = boxes_filt[i] * torch.Tensor([W, H, W, H])
        boxes_filt[i][:2] -= boxes_filt[i][2:] / 2
        boxes_filt[i][2:] += boxes_filt[i][:2]

    boxes_filt = boxes_filt.cpu().int().tolist()
    filtered_boxes = remove_boxes(boxes_filt, size)  # [:9]
    coordinates = []
    for box in filtered_boxes:
        coordinates.append([box[0], box[1], box[2], box[3]])

    return coordinates

def visualize_boxes_on_image(image_path, boxes, output_path):
    """
    在指定的原图上可视化框，并保存结果。

    参数:
    image_path -- 原图文件的路径
    boxes -- 包含多个坐标列表的列表，每个坐标列表格式为 [x1, y1, x2, y2]
    output_path -- 输出文件的路径
    """
    # 打开原图
    image = Image.open(image_path)

    # 创建一个可以用来对图像进行绘制的对象
    draw = ImageDraw.Draw(image)

    # 遍历所有的框
    for box in boxes:
        x1, y1, x2, y2 = box
        # 在图像上绘制矩形框
        draw.rectangle([x1, y1, x2, y2], outline='red', width=2)

    # 保存结果到新的文件
    image.save(output_path)


image_path = "screenshot/screenshot.jpg"
model_dir = snapshot_download('AI-ModelScope/GroundingDINO')
pipe = pipeline('grounding-dino-task', model=model_dir)
coordinates = det(image_path, "icon", pipe)
visualize_boxes_on_image(image_path, boxes=coordinates, output_path='icon_vis_image.jpg')