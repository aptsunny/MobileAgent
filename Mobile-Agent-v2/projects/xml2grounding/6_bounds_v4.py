# 从xml中构造框选信息 6_bounds_v4
import os, json
from PIL import Image, ImageDraw, ImageFont
import xmltodict

####
from abc import abstractmethod
from typing import List
from http import HTTPStatus
import requests
import time

class BaseModel:
    def __init__(self):
        pass

    @abstractmethod
    def get_model_response(self, prompt: str, images: List[str]) -> (bool, str):
        pass


class MifyModel(BaseModel):
    def __init__(self):
        super().__init__()
        self.chat_url = "https://mify-be.pt.xiaomi.com/api/v1/chat-messages"
        self.upload_url = "https://mify-be.pt.xiaomi.com/api/v1/files/upload"
        self.api_key = "app-yduZZpkQa8iwbdOcY1nVe4hd"

    def upload_image(self, image_path):
        headers = {
            'Authorization': f'Bearer {self.api_key}'
        }
        
        # 获取文件类型
        file_extension = os.path.splitext(image_path)[1].lower()
        content_type = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.webp': 'image/webp',
            '.gif': 'image/gif'
        }.get(file_extension)

        # 准备文件和表单数据
        with open(image_path, 'rb') as file:
            files = {
                'file': (os.path.basename(image_path), file, content_type)
            }
            data = {'user': "abc-123"}
            
            try_cnt = 0
            while try_cnt < 5:
                try_cnt += 1
                try:
                    # 发送POST请求
                    response = requests.post(self.upload_url,headers=headers,files=files,data=data)
                    # 检查响应状态
                    response.raise_for_status()
                    return True, response.json()["id"]
                    
                except Exception as e:
                    print("[API ERROR]!!!  Json Decode Error!!!", "red")
                    print(response.text, "red")
                    time.sleep(10)
                    continue
        return False, "API ERROR"

    def get_model_response(self, prompt: str, images: List[str]=[]) -> (bool, str):
        images_id = []
        if images is not None and len(images) > 0:
            for i in range(len(images)):
                status, image_id = self.upload_image(images[i])
                if status:
                    print(f'Upload image({images[i]}) succed!')
                    images_id.append(image_id)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "inputs": {},
            "query": prompt,
            "response_mode": "blocking",
            "conversation_id": "",
            "user": "abc-123",
            "files": []
        }
        for img_id in images_id:
            payload["files"].append({
                "type": "image",
                "transfer_method": "local_file",
                "upload_file_id": img_id
            })
        try_cnt = 0
        while try_cnt < 5:
            try_cnt += 1
            try:
                # 发送POST请求
                response = requests.post(self.chat_url, headers=headers, json=payload)
                # 检查响应状态
                response.raise_for_status()
                return True, response.json()["answer"]
                
            except Exception as e:
                print("[API ERROR]!!!  Json Decode Error!!!", "red")
                print(response.text, "red")
                time.sleep(10)
                continue
        
        return False, "API ERROR"


####

def xml2json(xml_file, target_json_info):
    with open(xml_file, encoding='utf-8') as xml_file:
        xml_data = xml_file.read()
    data_dict = xmltodict.parse(xml_data)
    json_data = json.dumps(data_dict, indent=2, ensure_ascii=False)
    with open(target_json_info, 'w', encoding='utf-8') as json_file:
        json_file.write(json_data)
    return

def extract_bounds_and_info(node, info_list=[]):
    # 获取当前节点的信息
    bounds = node.get('@bounds', None)
    text = node.get('@text', '')
    resource_id = node.get('@resource-id', '')
    clickable = node.get('@clickable', 'false')
    index = node.get('@index', '')

    if bounds:
        # 解析bounds字符串
        coords = bounds.strip('[]').split('][')
        top_left = tuple(map(int, coords[0].split(',')))
        bottom_right = tuple(map(int, coords[1].split(',')))
        info_list.append((top_left, bottom_right, text, resource_id, clickable, index))
    
    # 递归处理子节点
    children = node.get('node')
    if isinstance(children, list):
        for child in children:
            extract_bounds_and_info(child, info_list)
    elif isinstance(children, dict):
        extract_bounds_and_info(children, info_list)

    return info_list

def main():
    # base_dir = '/Users/sunyue/workspace/0_starbucks_data/screenshots/2024-10-23_11-09-47'
    base_dir = r"D:\download\2024-10-22_20-17-54\2024-10-22_20-17-54"
    target_prefix = '.xml' # -xml.txt
    
    model = MifyModel()

    for subdir, dirs, files in os.walk(base_dir):
        # import pdb;pdb.set_trace()

        for file in files:

            # xml
            if file.endswith(target_prefix):

                if file not in ['ui_dump_1729599555.xml']:
                    continue

                target_json_info = os.path.join(subdir, file.replace(target_prefix, '.json'))
                target_xml_file = os.path.join(subdir, file.replace('.json', target_prefix))
                if not os.path.exists(target_json_info):
                    xml2json(target_xml_file, target_json_info)
                target_image = target_json_info.replace('.json', '.png').replace('ui_dump_', 'screenshot_')
                save_dir = target_json_info.replace('.json', '_bbox')
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)
                # print(save_dir)
                # import pdb;pdb.set_trace()

                # 读取JSON文件
                # with open(target_json_info, 'r', encoding='utf-8') as file:
                #     data = json.load(file)
                try:
                    with open(target_json_info, 'r') as file:
                        data = json.load(file)
                except:
                    print(target_json_info)
                    with open(target_json_info, 'r', encoding='utf-8') as file:
                        data = json.load(file)


                # 提取所有节点的bounds和信息
                info_data = extract_bounds_and_info(data['hierarchy']['node'])

                # 加载图像
                # image_path = '/Users/sunyue/workspace/0_starbucks_data/screenshots/2024-10-23_11-09-47/screenshot_1729653038.png'
                # image_path = '/Users/sunyue/workspace/0_starbucks_data/screenshots/2024-10-23_11-09-47/screenshot_1729653285.png'
                # save_dir = '/Users/sunyue/workspace/0_starbucks_data/target_image'

                # 设置字体（可选）
                font_size = 12
                # font = ImageFont.load_default()  # 使用默认字体
                # font = ImageFont.truetype('/Users/sunyue/workspace/0_starbucks_data/SimSun.ttf', 12)
                font = ImageFont.truetype(r"D:\workspace\MobileAgent\Mobile-Agent-v2\SimSun.ttf", 12)

                # 绘制框和标注信息
                # 保存每一个可点击的标注信息
                for idx, (top_left, bottom_right, text, resource_id, clickable, index) in enumerate(info_data):

                    image = Image.open(target_image)
                    draw = ImageDraw.Draw(image)
                    # 确定颜色
                    box_color = 'red'
                    # box_color = 'red' if not text or not resource_id else 'black'
                    font_color = 'red' if clickable == 'false' else 'black'
                    

                    # 绘制矩形框
                    # if clickable == 'true' and (text != '' or resource_id != ''):
                    # if (text != '' or resource_id != ''):

                    # 可点击 或者 不可点击但是有文字内容
                    # if clickable == 'true' or (text != '' and clickable == 'false'):

                    if clickable == 'true':
                        try:
                            draw.rectangle([top_left, bottom_right], outline=box_color, width=10)

                            # 计算文本位置（框的左上角右侧）
                            # text_position = (top_left[0] + 5, top_left[1])
                            
                            # 构建标注文本
                            # label_text = f"Text: {text}\nResource ID: {resource_id}\nClickable: {clickable}\nIndex: {index}"
                            
                            # 绘制文本
                            # draw.text(text_position, label_text, fill=font_color, font=font)
                        except:
                            print(idx, 'err')

                        # 显示或保存结果图像
                        # image.show()  # 显示图像

                        save_bbox_path = os.path.join(save_dir, 'bbox_{}.png'.format(idx))
                        image.save(save_bbox_path)  # 保存图像到文件

                        # 绘制矩形框
                        # print(idx, (index, top_left, bottom_right, text, resource_id, clickable))

                        # print(save_bbox_path)
                        # import pdb;pdb.set_trace()
                        # 可点击区域 的 referring, 并且看看
                        # 描述是否需要修正，如果需要修正 给一个正确的？
                        # status, answer = model.get_model_response("手机屏幕中红框是什么含义?", [os.path.join(save_dir, 'bbox_{}.png'.format(idx))])
                        # status, answer = model.get_model_response("请分析手机截图中红框标记的可点击区域，并简述其功能。", [os.path.join(save_dir, 'bbox_{}.png'.format(idx))])
                        # status, answer = model.get_model_response("请以'功能：[具体描述]'的格式，简述手机截图中红框区域的作用。", [os.path.join(save_dir, 'bbox_{}.png'.format(idx))])
                        # status, answer = model.get_model_response(
                        # """
                        # 简述手机截图中红框区域的作用, 请按照以下格式回答：

                        # 1. 类型：[具体类型]
                        # 2. 描述：[具体描述]

                        # - 具体类型只能为 图标、文字、控件、其他。
                        # - 对于图标和文字，分别提供类型和描述。如果是控件，请在提供类型和描述后，额外给出其功能。
                        # """
                        # , [os.path.join(save_dir, 'bbox_{}.png'.format(idx))])

                        # 保存客制化？
                        status, answer = model.get_model_response("请以'功能：[具体描述]'的格式，用10个字以内简述手机截图中红框区域的作用。", [save_bbox_path])
                        # status, answer = model.get_model_response(
                        # """
                        # 请以'功能：[具体描述]'的格式，用10个字以内简述手机截图中红框区域的作用。
                        # - 注意“心型形状”保存客制化是保留当前选配的作用。 
                        # """
                        # , [save_bbox_path])
                        if status:
                            print(answer)

                        import pdb;pdb.set_trace()
                        # 


if __name__ == '__main__':
    main()