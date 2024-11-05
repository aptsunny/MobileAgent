from abc import abstractmethod
from typing import List
from http import HTTPStatus
import os
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
    
if __name__ == '__main__':
    model = MifyModel()
    # model.upload_image("icon_vis_image.png")
    status, answer = model.get_model_response("图中框都是什么含义?", ["icon_vis_image.jpg"])
    print(status, answer)