import base64
import requests
from .tik_count import num_tokens_from_messages, save_list_of_dicts_as_json, generate_filename

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def normalize_gpt4_input(func):
    def wrapper(*args, **kwargs):
        mode = kwargs.get('mode', '')
        model_name = kwargs.get('model', '')
        chat_info = kwargs.get('chat', '')
        step = kwargs.get('step', '')
        record_file = kwargs.get('record_file', '')
        # 20B
        model_name = 'internlm2.5-latest' if mode == 'openai' else model_name
        # 7B
        # model_name = 'internlm2.5-7b-0627' if mode == 'openai' else model_name
        # 6B xiaomi fail
        model_name = 'MiLM2.1-6B-Chat' if mode == 'xiaomi' else model_name
        # 13B xiaomi
        # model_name = 'MiLM2.1-13B-Chat' if mode == 'xiaomi' else model_name

        data = {
            "model": model_name,
            "messages": [],
            "max_tokens": 2048,
            'temperature': 0.0,
            "seed": 1234
        }

        try:
            for role, content in chat_info:
                data["messages"].append({"role": role, "content": content})
        except Exception as e:
            print(f"处理聊天信息时出错: {e}")
            return None
        # import pdb;pdb.set_trace()

        if mode in ['openai', 'xiaomi']:
            try:
                # ignore assistant
                # image_url = data['messages'][1]['content'][1]['≈']['url']
                # data['messages'].append({"role": 'user', "content": 'image_url: {}'.format(image_url)})
                if len(data['messages']) == 1:
                    data['messages'][0]['content'] = data['messages'][0]['content'][0].get('text', '')
                elif len(data['messages']) == 2:
                    data['messages'][0]['content'] = data['messages'][0]['content'][0].get('text', '')
                    data['messages'][1]['content'] = data['messages'][1]['content'][0].get('text', '')
                elif len(data['messages']) == 4:
                    data['messages'][0]['content'] = data['messages'][0]['content'][0].get('text', '')
                    data['messages'][1]['content'] = data['messages'][1]['content'][0].get('text', '')
                    data['messages'][2]['content'] = data['messages'][2]['content'][0].get('text', '')
                    data['messages'][3]['content'] = data['messages'][3]['content'][0].get('text', '')
                # Memory 4
                # 加了Thought 、Action、 Response
                # data['messages'][0]
                # data['messages'][3]
                # data['messages'][2]
                # data['messages'][1]['content'][0]
                # data['messages'][1]['content'][1] -> image
            except IndexError:
                print("数据格式不符合预期")
                return None
            except Exception as e:
                print(f"处理 openai 模式时出错: {e}")
                return None

        save_list_of_dicts_as_json([data], filename='{}/{}_output.json'.format(record_file, generate_filename(step)))

        kwargs['data'] = data
        try:
            step, num_tokens = num_tokens_from_messages(data["messages"], step)
            kwargs['num_tokens'] = num_tokens
        except Exception as e:
            print(f"计算 Token 数量时出错: {e}")
            return None

        output = func(*args, **kwargs)
        return output
    return wrapper

@normalize_gpt4_input
def inference_chat(api_url, token, chat=None, model=None, data=None, mode='requests', step=None, record_file=None, num_tokens=None):
    if mode == 'requests':
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
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
    elif mode in ['openai', 'xiaomi']:
        from openai import OpenAI
        client = OpenAI(api_key=token, base_url=api_url)
        while True:
            try:
                chat_rsp = client.chat.completions.create(**data)
                res_content = chat_rsp.choices[0].message.content
            except:
                print("Network Error:")
                try:
                    print(chat_rsp)
                except:
                    print("Request Failed")
            else:
                break
    # return res_content, dict(step=num_tokens)
    return res_content, {step: num_tokens}


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