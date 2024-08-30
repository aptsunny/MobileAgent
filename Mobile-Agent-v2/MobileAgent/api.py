import base64
import requests

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def inference_chat(chat, model, api_url, token, mode='requests'):
    if mode == 'requests':
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }

        data = {
            "model": model,
            "messages": [],
            "max_tokens": 2048,
            'temperature': 0.0,
            "seed": 1234
        }

        for role, content in chat:
            data["messages"].append({"role": role, "content": content})

        while True:
            try:
                res = requests.post(api_url, headers=headers, json=data)
                res_content = res.json()['choices'][0]['message']['content']
            except:
                print("Network Error:")
                try:
                    print(res.json())
                except:
                    print("Request Failed")
            else:
                break
    elif mode == 'openai':
        from openai import OpenAI

        client = OpenAI(
            api_key=token,  
            base_url=api_url,
        )

        data = {
            "model": "internlm2.5-latest",
            "messages": [],
            "max_tokens": 2048,
            'temperature': 0.0,
            "seed": 1234
        }

        for role, content in chat:
            data["messages"].append({"role": role, "content": content})

        ###
        # image_url
        # image_url = data['messages'][1]['content'][1]['≈']['url']
        # import pdb;pdb.set_trace()
        data['messages'][0]['content'] = data['messages'][0]['content'][0]['text'] # 系统
        data['messages'][1]['content'] = data['messages'][1]['content'][0]['text'] # 用户,还包括截图

        # image_url not support
        # data['messages'].append({"role": 'user', "content": 'image_url: {}'.format(image_url)})

        # ignore assistant
        chat_rsp = client.chat.completions.create(**data)

        while True:
            try:
                res_content = chat_rsp.choices[0].message.content
            except:
                print("Network Error:")
                try:
                    print(chat_rsp.json())
                except:
                    print("Request Failed")
            else:
                break
    return res_content


def generate_local(tokenizer, model, image_file, query):
    query = tokenizer.from_list_format([
        {'image': image_file},
        {'text': query},
    ])
    response, _ = model.chat(tokenizer, query=query, history=None)
    return response


def process_image(image, query, qwen_api, caption_model):
    import dashscope
    from dashscope import MultiModalConversation
    dashscope.api_key = qwen_api

    messages = [{
        'role': 'user',
        'content': [
            {
                'image': image
            },
            {
                'text': query
            },
        ]
    }]
    response = MultiModalConversation.call(model=caption_model, messages=messages)
    
    try:
        response = response['output']['choices'][0]['message']['content'][0]["text"]
    except:
        response = "This is an icon."
    
    return response


def generate_api(images, query, qwen_api, caption_model):
    import concurrent
    icon_map = {}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(process_image, image, query, qwen_api, caption_model): i for i, image in enumerate(images)}
        
        for future in concurrent.futures.as_completed(futures):
            i = futures[future]
            response = future.result()
            icon_map[i + 1] = response
    
    return icon_map