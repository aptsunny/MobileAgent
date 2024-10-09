import base64
import requests
from .tik_count import num_tokens_from_messages, save_list_of_dicts_as_json, generate_filename, update_value_in_dict_single_key

def get_chat_mode(API_url, chat_mode='requests'):
    # MiLM2.1-13B-Chat
    MILM_URL = "http://preview-general-llm.api.ai.srv/v1/"

    if not API_url:
        raise ValueError("API_url cannot be empty")

    if 'internlm' in API_url:
        chat_mode = 'openai'
    elif API_url == MILM_URL:
        chat_mode = 'xiaomi'
    elif 'huiwen' in API_url or 'yashan' in API_url:
        chat_mode = 'mi_requests'

    return chat_mode


def get_chat_data(model_name, chat_mode='requests'):
    model_mapping = {
        'openai': 'internlm2.5-latest',
        'xiaomi': 'MiLM2.1-13B-Chat',
        'mi_requests': 'gpt4o/gpt4v',
        'requests': model_name,
    }

    if chat_mode in model_mapping:
        model_name = model_mapping[chat_mode]
    else:
        raise ValueError(f"Invalid chat_mode: {chat_mode}. Expected one of: {list(model_mapping.keys())}")

    data = {
        "model": model_name,
        "messages": [],
        "max_tokens": 2048,
        'temperature': 0.0,
        "seed": 1234
    }

    # mi_requests del model
    if chat_mode == 'mi_requests':
        if "model" in data:
            del data["model"]

    return data


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
        data = get_chat_data(model_name, mode)

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

        # only chat model
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
        if mode == 'mi_requests':
            try:
                # action_input stage1/2/3/4
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
            # data['messages'][1]['content']
            # import pdb;pdb.set_trace()
            step, num_input_tokens = num_tokens_from_messages(data["messages"], step)
            kwargs['num_input_tokens'] = num_input_tokens
        except Exception as e:
            print(f"计算 Input Token 数量时出错: {e}")
            return None

        output = func(*args, **kwargs)

        output_info = [dict(result=output[0])]
        save_list_of_dicts_as_json(output_info, filename='{}/{}_output.json'.format(record_file, generate_filename(step)))
        try:
            _, num_output_tokens = num_tokens_from_messages(output_info, '{} output'.format(step))
            update_value_in_dict_single_key(output[1], num_output_tokens)
        except Exception as e:
            print(f"计算 Output Token 数量时出错: {e}")
            return None

        return output
    return wrapper

@normalize_gpt4_input
def inference_chat(api_url, token, chat=None, model=None, data=None, mode='requests', step=None, record_file=None, num_input_tokens=None, num_output_tokens=None):
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
        api_urls = [
            # gpt4o
            'http://preview-general-llm.api.ai.srv/api/gpt-4o/liuhuiwen',
            'http://preview-general-llm.api.ai.srv/api/gpt-4o/luyashan1',
            'http://preview-general-llm.api.ai.srv/api/gpt-4o/weilai8',
            'http://preview-general-llm.api.ai.srv/api/gpt-4o/liuwei40',
            # gpt4v
            # 'http://preview-general-llm.api.ai.srv/api/gpt-4v/liuhuiwen',
            # 'http://preview-general-llm.api.ai.srv/api/gpt-4v/luyashan1',
        ]
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
                response_data = response.json()
                
                if 'response' in response_data:
                    # 如果响应状态码不是200，将抛出HTTPError异常
                    # response.raise_for_status()
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

    return res_content, {step: [num_input_tokens, num_output_tokens]}


def generate_local(tokenizer, model, image_file, query):
    query = tokenizer.from_list_format([
        {'image': image_file},
        {'text': query},
    ])
    response, _ = model.chat(tokenizer, query=query, history=None)
    return response


def process_image(image, query, qwen_token, caption_model):
    import dashscope
    from dashscope import MultiModalConversation
    dashscope.api_key = qwen_token

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


def generate_api(images, query, qwen_token, caption_model):
    import concurrent
    icon_map = {}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(process_image, image, query, qwen_token, caption_model): i for i, image in enumerate(images)}
        
        for future in concurrent.futures.as_completed(futures):
            i = futures[future]
            response = future.result()
            icon_map[i + 1] = response
    
    return icon_map