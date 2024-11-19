from tqdm import tqdm
import json, random
from PIL import Image, ImageDraw, ImageFont

def process_conversation(conversations, image):
    # 将conversations分组，每组包含一个"from": "human"和一个"from": "gpt"
    new_conversations = []
    while len(conversations) >= 2:
        human_conversation = conversations[0]
        gpt_conversation = conversations[1]
        new_conversations.append({
            "image": image,
            "conversations": [human_conversation, gpt_conversation]
        })
        conversations = conversations[2:]  # 移除已处理的对话
    return new_conversations

def convert_bbox(x, y, w, h):
    # 转换坐标并取整
    # return [round(x), round(y), round(x + w), round(y + h)]
    # import pdb;pdb.set_trace()
    # w1200 h2600
    # return [round(x), round(y), round(w), round(h)]
    # w1000 h1000
    # return [round(x*10/12), round(y/2.6), round(w*10/12), round(h/2.6)]
    # 
    return [round((x+y)/2), round((w+h)/2)]

def convert_coordinates(x, y):
    return [round(x), round(y)]

def extract_label(question):
    # 从问题中提取关键词
    labels = ["专星送", "咖快", "咖啡生活馆", "外卖拼单", "星巴克"]
    for label in labels:
        if label in question:
            return label
    return question.split("？")[-1].strip()

def process_labelu_annotations(annotations):
    conversations = []
    for rect_result in annotations:
        try:
            label = extract_label(rect_result['attributes']['q'])
        except:
            continue
        coords = convert_bbox(rect_result['x'], rect_result['y'], rect_result['width'], rect_result['height'])

        # Grounding QA bbox
        # conversations.append({
        #     "from": "human",
        #     "value": f"<image>\n如果我想要“{label}”，需要点击哪个区域, 输入以框坐标[x1, y1, x2, y2]的格式输出"
        # })
        # conversations.append({
        #     "from": "gpt",
        #     "value": str(coords)
        # })

        # coordinates
        conversations.append({
            "from": "human",
            "value": f"<image>\n如果我想要“{label}”，需要点击哪个区域, 输入以框坐标[x, y]的格式输出"
        })
        conversations.append({
            "from": "gpt",
            "value": str(coords)
        })


        # Referring QA
        # conversations.append({
        #     "from": "human",
        #     # "value": f"<image>\nWhat are the icons in the {str(coords)} area of the phone's screen and what exactly do they mean?."
        #     "value": f"<image>\nWhat are the labels or text elements in the {str(coords)} area of the phone's screen and what exactly do they mean?"
        # })
        # conversations.append({
        #     "from": "gpt",
        #     "value": f"{label}"
        # })
        
        # {
        #     "from": "human",
        #     "value": "<image>\nWhat is the text at [x1, y1] in the cell phone screen?."
        # },
        # {
        #     "from": "gpt",
        #     "value": "对应的 OCR 结果"
        # }

    return conversations

def process_xml_annotations(annotations, parse_type='coordinates'):
    assert parse_type in ['bbox', 'coordinates']
    conversations = []

    for label, rect_result in annotations.items():
        if parse_type == 'coordinates':
            coords = convert_coordinates(rect_result[0], rect_result[1])
        elif parse_type == 'bbox':
            coords = convert_bbox(rect_result[0], rect_result[1], rect_result[2], rect_result[3])

        # Grounding QA bbox v1
        # conversations.append({
        #     "from": "human",
        #     "value": f"<image>\n如果我想要“{label}”，需要点击哪个区域, 输入以框坐标[x1, y1, x2, y2]的格式输出"
        # })
        # conversations.append({
        #     "from": "gpt",
        #     "value": str(coords)
        # })

        # coordinates
        # conversations.append({
        #     "from": "human",
        #     "value": f"<image>\n如果我想要“{label}”，需要点击哪个位置, 以坐标[x, y]的格式输出"
        # })
        # conversations.append({
        #     "from": "gpt",
        #     "value": str(coords)
        # })

        # coordinates ATLAS 4B prompt
        conversations.append({
            "from": "human",
            "value": f"<image>\nPlease analyze the screenshot of my mobile screen and provide the coordinates [x, y] of the '{label}' element that I want to tap on."
        })
        conversations.append({
            "from": "gpt",
            "value": str(coords)
        })

        conversations.append({
            "from": "human",
            "value": f"<image>\nPlease locate the '{label}' link in the provided mobile screenshot and specify its click coordinates in the format [x, y]. I need the exact pixel location for this element."
        })
        conversations.append({
            "from": "gpt",
            "value": str(coords)
        })

        conversations.append({
            "from": "human",
            "value": f"<image>\nFrom the mobile screenshot, identify the '{label}' link and give me the coordinates to click on it, formatted as [x, y]. Ensure the coordinates are in pixel values."
        })
        conversations.append({
            "from": "gpt",
            "value": str(coords)
        })

        conversations.append({
            "from": "human",
            "value": f"<image>\nIn the mobile screenshot, the '{label}' link is expected to be in the top navigation area. Please provide the click coordinates for this link in the [x, y] format."
        })
        conversations.append({
            "from": "gpt",
            "value": str(coords)
        })

        conversations.append({
            "from": "human",
            "value": f"<image>\nAnalyzing the attached mobile screenshot, I need the [x, y] coordinates for the '{label}' link. Please provide the pixel coordinates for precise targeting of this element."
        })
        conversations.append({
            "from": "gpt",
            "value": str(coords)
        })

        conversations.append({
            "from": "human",
            "value": f"<image>\nKindly determine the [x, y] coordinates for clicking the '{label}' link in this mobile screenshot. The coordinates should be in pixel format, pinpointing the exact location of the link."
        })
        conversations.append({
            "from": "gpt",
            "value": str(coords)
        })

        # Referring QA
        # conversations.append({
        #     "from": "human",
        #     # "value": f"<image>\nWhat are the icons in the {str(coords)} area of the phone's screen and what exactly do they mean?."
        #     "value": f"<image>\nWhat are the labels or text elements in the {str(coords)} area of the phone's screen and what exactly do they mean?"
        # })
        # conversations.append({
        #     "from": "gpt",
        #     "value": f"{label}"
        # })
        
        # {
        #     "from": "human",
        #     "value": "<image>\nWhat is the text at [x1, y1] in the cell phone screen?."
        # },
        # {
        #     "from": "gpt",
        #     "value": "对应的 OCR 结果"
        # }

    return conversations

def vis_bbox(idx, image_path, conversations, check_idx=None, save_image=False): 
    # 加载图像
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)
    
    try:
        font = ImageFont.truetype("simhei.ttf", 15)
    except IOError:
        font = ImageFont.load_default()
    
    # 找到并绘制坐标框和提问信息
    for i, conversation in enumerate(conversations):
        if conversation['from'] == 'gpt':
            coords = eval(conversation['value'])
            # import pdb;pdb.set_trace()
            if len(coords)==2:
                coords_left = [obj-5 for obj in coords]
                coords_right = [obj+5 for obj in coords]
                draw.rectangle(coords_left+coords_right, outline='red', width=2)
            else:
                draw.rectangle(coords, outline='red', width=2)
            
            # 找到对应的提问信息
            question_index = conversations.index(conversation) - 1
            if question_index >= 0 and conversations[question_index]['from'] == 'human':
                question = conversations[question_index]['value'].replace('<image>\n', '').strip()
                # text_width, text_height = draw.textsize(question, font=font)
                text_width, text_height = 50, 50
                text_x = coords[0] + 10
                text_y = coords[1] - text_height - 5 if coords[1] - text_height - 5 > 0 else coords[1] + 10
                draw.text((text_x, text_y), question, fill='red', font=font)
    if idx == check_idx:
        image.show()
        # import pdb;pdb.set_trace()        
    if save_image:
        output_path = image_path.replace('.jpg', '_annotated.jpg')
        image.save(output_path)

def xml_load(input_file, output_file, random_sort=False):
    output_data = []

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    parse_type = 'coordinates'
    for filename, bbox_dict in tqdm(data.items(), desc="Processing"):
        conversations = process_xml_annotations(bbox_dict, parse_type)
        output_data.append({
            "image": filename,
            "conversations": conversations
        })

    # 可视化
    check_idx = None
    if check_idx:
        for idx, item in enumerate(output_data):
            image_path = item['image']
            conversations = item['conversations']
            vis_bbox(idx, image_path, conversations, check_idx)

    # import pdb;pdb.set_trace()
    # 拆分子条目
    new_data = []
    for item in tqdm(output_data, desc="Split"):
        new_item_conversations = process_conversation(item['conversations'], item['image'])
        new_data.extend(new_item_conversations)

    if random_sort:
        random.shuffle(new_data)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)

    print("JSON数据已更新，每组对话都包含其对应的Grounding信息。")

def labelU_load(input_file, output_file):
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    output_data = []
    for item in data:
        assert 'result' in item, "Item missing 'result' key"
        assert 'fileName' in item, "Item missing 'fileName' key"
        
        parsed_data = json.loads(item['result'])
        assert 'annotations' in parsed_data, "Parsed data missing 'annotations' key"
        
        conversations = process_labelu_annotations(parsed_data['annotations'][0]['result'])
        output_data.append({
            "image": item['fileName'],
            "conversations": conversations
        })
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

def main():
    # labelu 标注工具 https://labelu.shlab.tech/tasks, 用于检查数据格式和预先标注是否有效
    # labelU_load(input_file, output_file)

    # input_file = '/Users/sunyue/Downloads/星巴克v3_3.json'  # 输入文件名
    # input_file = '/Users/sunyue/Downloads/星巴克v4.json'  # 输入文件名
    # input_file = '/Users/sunyue/Downloads/星巴克v5_r1.json'  # 输入文件名
    input_file = '/Users/sunyue/Downloads/星巴克v5_r1_all.json'  # 正式标注, 一个文件夹的所有截图

    # output_file = 'sft_output_v3.json'  # 输出文件名
    # output_file = 'sft_output_v4.json'  # 输出文件名
    # output_file = 'sft_output_v5_r1.json'  # 导出训练尝试
    output_file = 'sft_output_v5_r1_referring.json'  # 导出训练尝试    

    # xml
    input_file = '/Users/sunyue/workspace/0_starbucks_data/xml_anno_info.json'  # 正式标注, 一个文件夹的所有截图
    output_file = 'sft_output_xml_info.json'  # 导出训练尝试
    input_file = '/Users/sunyue/workspace/0_starbucks_data/xml_anno_info_15.json'  # 正式标注, 一个文件夹的所有截图
    output_file = 'sft_output_xml_info_15.json'  # 导出训练尝试
    input_file = '/Users/sunyue/workspace/0_starbucks_data/xml_anno_info_15.json'  # 正式标注, 一个文件夹的所有截图
    output_file = 'sft_output_xml_info_15_only_grounding.json'  # 导出训练尝试

    # 20241106
    input_file = r"D:\workspace\MobileAgent\xml_anno_info_single_folder_20241106.json"
    # output_file = 'sft_20241106_output_xml_info_only_grounding.json'  # 导出训练尝试
    # output_file = 'sft_20241106_output_xml_info_only_grounding_norm.json'  # 导出训练尝试

    # 20241107 导出坐标，而不是bbox
    output_file = 'sft_20241106_output_xml_info_only_grounding_coordinates.json'  # 导出训练尝试

    # 20241112 坐标信息
    input_file = r"D:\workspace\OmniParser\omni_xml_anno_info_single_folder_1728_fix.json"
    output_file = 'sft_20241112_output_xml_info_only_grounding_coordinates_1728_fix.json'  # 导出训练尝试

    # 20241114 完整的轨迹 坐标信息
    input_file = r"D:\workspace\OmniParser\omni_xml_anno_info_single_folder_v2.json"
    output_file = 'sft_20241114_output_xml_info_only_grounding_coordinates.json'  # 导出训练尝试

    # Parse XML File
    xml_load(input_file, output_file)

if __name__ == "__main__":
    main()

