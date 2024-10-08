import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)

from PIL import Image, ImageDraw, ImageFont
import os, re
import json

def extract_json_iter_number(filename):
    # Use regular expressions to match the number part
    match = re.search(r'Iter(\d+)', filename)
    if match:
        # Returns the matching number part and convert it to an integer
        return int(match.group(1))
    return None

def extract_iter_number(filename):
    match = re.search(r'Iter(\d+)_vis_action', filename)
    if match:
        return int(match.group(1))
    return None

def split_elements_if_too_long(lst, max_length):
    new_lst = []
    for item in lst:
        if len(item) > max_length:
            ## Split element
            while len(item) > max_length:
                new_lst.append(item[:max_length])
                item = item[max_length:]
            new_lst.append(item)
        else:
            new_lst.append(item)
    return new_lst

def extract_info_from_json(folder_path, key_to_extract='result'):
    result = []
    # All ACTION_OUTPUT files in the folder
    json_files = [filename for filename in os.listdir(folder_path) if filename.endswith('Action_output.json')]
    sorted_files = sorted(json_files, key=extract_json_iter_number)

    for filename in sorted_files:
        file_path = os.path.join(folder_path, filename)
        with open(file_path, 'r', encoding='utf-8') as file:
            try:
                # Load JSON data
                data = json.load(file)
                # Ensure that data is a list format
                if isinstance(data, list):
                    # Extract information about specific keywords
                    extracted_info = [item[key_to_extract] for item in data if key_to_extract in item]
                    # Store the extracted information in the dictionary
                    # import pdb;pdb.set_trace()
                    thought_info = extracted_info[0].split("### Thought ###")[-1].split("### Action")[0].replace("\n", " ").replace(":", "").replace("  ", " ").strip()
                    operation_info = extracted_info[0].split("### Operation ###")[-1].split("### Operation")[0].replace("\n", " ").replace("  ", " ").strip()
                    action_info = extracted_info[0].split("### Action ###")[-1].split("### Operation")[0].replace("\n", " ").replace("  ", " ").strip()
                    result.append([thought_info, action_info])
            except json.JSONDecodeError:
                print(f"Error decoding JSON from file: {filename}")
            except Exception as e:
                print(f"An error occurred while processing file: {filename}, error: {e}")
    return result

def create_combined_image(folder_path, output_path, row_padding=350, image_padding=200, font_size=80, max_char_limit=30, font_path="simsun.ttc"):
    result_list = extract_info_from_json(folder_path)
    # Set the number of pictures per line
    num_images_per_row = 5
    
    # Get all the picture files in the folder
    images = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(('_annotated.png', '.jpg', '.jpeg'))]
    
    # Make sure the number of pictures meets the requirements
    if len(images) % num_images_per_row != 0:
        print("图片数量不是每行数量的整数倍，最后可能不完整")
    # Use the custom sort key function for sorting
    images = sorted(images, key=lambda s: extract_iter_number(s) if extract_iter_number(s) is not None else float('inf'))
    
    # Load the first picture to obtain the size of a single picture
    img = Image.open(images[0])
    img_width, img_height = img.size
    
    # Calculate the total width and height
    total_width = num_images_per_row * img_width + (num_images_per_row - 1) * image_padding
    total_height = (len(images) // num_images_per_row + (1 if len(images) % num_images_per_row != 0 else 0)) * (img_height + font_size + 20 + row_padding)
    
    # Create a new picture to save results
    combined_image = Image.new('RGB', (total_width, total_height), (255, 255, 255))
    draw = ImageDraw.Draw(combined_image)
    
    # Loading font
    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        font = ImageFont.load_default()

    step = len(result_list)
    for idx, img_path in enumerate(images):
        if idx == step:
            break
        # Open the picture
        img = Image.open(img_path)
        
        # Calculate the location of the current picture
        row = idx // num_images_per_row
        col = idx % num_images_per_row
        x = col * (img_width + image_padding)
        # 40 pixel extra space is used in the interval between text and pictures
        y = row * (img_height + font_size + 40 + row_padding)  
        
        # Paste picture
        combined_image.paste(img, (x, y))
        
        # Get the list of descriptions
        descriptions = split_elements_if_too_long(result_list[idx], max_char_limit)
        
        text_y_offset = 0
        for line in descriptions:
            width, height = draw.textsize(line, font=font)
            text_x = x + (img_width - width) / 2
            # 20 Pixel extra space for the interval between the first line of text and pictures
            text_y = y + img_height + 20 + text_y_offset  
            draw.text((text_x, text_y), line, font=font, fill=(0, 0, 255))
            text_y_offset += height
        
    ## Save the picture
    combined_image.save(output_path)


export_data = [
    # (r'D:\workspace\1_鱼香肉丝_memory_record', r'D:\workspace\1_鱼香肉丝.jpg', 350),
    # (r'D:\workspace\2_好吃的火锅_memory_record', r'D:\workspace\2_好吃的火锅.jpg', 350), 
    # (r'D:\workspace\3_浏览器小米股票_memory_record', r'D:\workspace\3_浏览器小米股票.jpg', 950),
    # (r'D:\workspace\4_屏幕使用时间_memory_record', r'D:\workspace\4_屏幕使用时间.jpg', 1200), 
    # (r'D:\workspace\6_推荐歌曲_memory_record', r'D:\workspace\6_推荐歌曲.jpg', 1200), 
    # (r'D:\workspace\7_Keep_memory_record', r'D:\workspace\7_Keep.jpg', 1200), 
    # (r'D:\workspace\8_抖音_memory_record', r'D:\workspace\8_抖音.jpg', 1200), 
    # (r'D:\workspace\9_番茄_memory_record', r'D:\workspace\9_番茄.jpg', 1200), 
    # (r'D:\workspace\10_百度地图_memory_record', r'D:\workspace\10_百度地图.jpg', 1200), 
    # (r'D:\workspace\11_支付宝_memory_record', r'D:\workspace\11_支付宝.jpg', 1200), 
    # (r'D:\workspace\12_设置_memory_record', r'D:\workspace\12_设置.jpg', 1200), 
    # (r'D:\workspace\13_知乎通知_memory_record', r'D:\workspace\13_知乎通知.jpg', 1200), 
    # (r'D:\workspace\14_小红书换乘_memory_record', r'D:\workspace\14_小红书换乘.jpg', 1200), 
    # (r'D:\workspace\15_地图青岛_memory_record', r'D:\workspace\15_地图青岛.jpg', 1200), 
    # (r'D:\workspace\16_小红书婺源_memory_record', r'D:\workspace\16_小红书婺源.jpg', 1200), 
    # (r'D:\workspace\17_携程外滩_memory_record', r'D:\workspace\17_携程外滩.jpg', 1200), 
    # (r'D:\workspace\18_B站盲盒_memory_record', r'D:\workspace\18_B站盲盒.jpg', 1200), 
    # (r'D:\workspace\19_腾讯地图公交站_memory_record', r'D:\workspace\19_腾讯地图公交站.jpg', 1200), 
    # (r'D:\workspace\20_音乐最近播放_memory_record', r'D:\workspace\20_音乐最近播放.jpg', 1200), 
    # (r'D:\workspace\21_美团酒店_memory_record', r'D:\workspace\21_美团酒店.jpg', 1200), 
    # (r'D:\workspace\.vscode\基础评测数据\D1_咖啡_memory_record', r'D:\workspace\D1_咖啡.jpg', 1200), 
    # (r'D:\workspace\.vscode\基础评测数据\D2_咖啡_memory_record', r'D:\workspace\D2_咖啡.jpg', 1200), 
    # (r'D:\workspace\.vscode\基础评测数据\D2_咖啡_Fix_memory_record', r'D:\workspace\D2_Fix_咖啡.jpg', 1200), 
    (r'D:\workspace\.vscode\基础评测数据\D3_咖啡_memory_record', r'D:\workspace\D3_咖啡.jpg', 1200), 
]

for i, j, hight in export_data:
    create_combined_image(i, j, row_padding=hight)
