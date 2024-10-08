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
        # 20B：internlm2.5-latest，7B：internlm2.5-7b-0627
        model_name = 'internlm2.5-latest' if mode == 'openai' else model_name
        # 13B xiaomi
        # model_name = 'MiLM2.1-13B-Chat' if mode == 'xiaomi' else model_name

        data = {
            "model": model_name,
            "messages": [],
            "max_tokens": 2048,
            'temperature': 0.0,
            "seed": 1234
        }

        # mi_requests 不需要传入model字段
        if mode == 'mi_requests':
            del data["model"]

        try:
            for role, content in chat_info:
                # content_inside = content[0] if isinstance(content, list) and len(content) ==1 else content
                content_inside = content
                # import pdb;pdb.set_trace()
                data["messages"].append({"role": role, "content": content_inside})
        except Exception as e:
            print(f"处理聊天信息时出错: {e}")
            return None

        # save_list_of_dicts_as_json([data], filename='{}/{}_before_process.json'.format(record_file, generate_filename(step)))

        if mode in ['openai', 'xiaomi']: # only chat model
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
        if mode == 'mi_requests':
            try:
                # action_input
                if len(data['messages']) == 2:
                    data['messages'][0]['content'] = data['messages'][0]['content'][0].get('text', '')
                    # data['messages'][1]['content'] = data['messages'][1]['content'][0].get('text', '')
                    if len(data['messages'][1]['content']) == 1:
                        data['messages'][1]['content'] = data['messages'][1]['content'][0].get('text', '')
                elif len(data['messages']) == 4:
                    data['messages'][0]['content'] = data['messages'][0]['content'][0].get('text', '')
                    # data['messages'][1]['content'] = data['messages'][1]['content'][0].get('text', '')
                    data['messages'][2]['content'] = data['messages'][2]['content'][0].get('text', '')
                    data['messages'][3]['content'] = data['messages'][3]['content'][0].get('text', '')
            except IndexError:
                print("数据格式不符合预期")
                return None
            except Exception as e:
                print(f"处理 openai 模式时出错: {e}")
                return None

        save_list_of_dicts_as_json([data], filename='{}/{}_input.json'.format(record_file, generate_filename(step)))
        kwargs['data'] = data
        try:
            step, num_tokens = num_tokens_from_messages(data["messages"], step)
            kwargs['num_tokens'] = num_tokens
        except Exception as e:
            print(f"计算 Token 数量时出错: {e}")
            return None

        output = func(*args, **kwargs)

        output_info = [dict(result=output[0])]
        save_list_of_dicts_as_json(output_info, filename='{}/{}_output.json'.format(record_file, generate_filename(step)))
        output_step = '{} output'.format(step)
        num_tokens_from_messages(output_info, output_step)
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
    elif mode == 'mi_requests':
        api_urls = []
        api_urls = [item for item in api_urls for _ in range(50)]
        import random;random.shuffle(api_urls)

        attempt_count = 0
        successful_api_url = None
        response_data = None
        for api_url in api_urls:
            try:
                attempt_count += 1
                print(f"请求第{attempt_count}次，第{attempt_count}次使用的API是：{api_url}")
                response = requests.post(api_url, json=data)
                # 如果响应状态码不是200，将抛出HTTPError异常
                # response.raise_for_status() 
                response_data = response.json()
                
                if 'response' in response_data:
                    res_content = response_data['response']
                    if 'ERROR' not in res_content:
                        successful_api_url = api_url
                        break
                else:
                    print(f"请求状态码不是200，状态码：{response.status_code}, 实际上429: {api_url}")
            except requests.exceptions.RequestException as e:
                print(f"请求失败：{e}")
                continue
        if successful_api_url:
            print(f"总共尝试了{attempt_count}次，第{attempt_count}次使用的API是：{successful_api_url}")
        else:
            print("所有API尝试均失败。")
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