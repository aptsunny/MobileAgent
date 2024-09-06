import argparse
import os
import time
import copy
import torch
import shutil
from PIL import Image

from MobileAgent.api import inference_chat, generate_local, generate_api
from MobileAgent.chat import add_response, add_response_two_image, print_status_func
from MobileAgent.crop import draw_coordinates_on_image, crop_save_tmp, merge_text_blocks
from MobileAgent.text_localization import ocr
from MobileAgent.icon_localization import det
from MobileAgent.controller import get_screenshot, tap, slide, type, back, home
from MobileAgent.prompt import get_action_prompt, get_reflect_prompt, get_memory_prompt, get_process_prompt
from MobileAgent.tik_count import plot_values, plot_grouped_distribution

torch.manual_seed(1234)

def parse_args():
    parser = argparse.ArgumentParser(description='MobileAgent Test')
    parser.add_argument('instruction', help='Path to the training configuration file')
    parser.add_argument('token', help='Authentication token for API access')
    parser.add_argument('qwen_api', help='API endpoint for Qwen')
    parser.add_argument('--adb-path',
                        default=os.getenv('ADB_PATH', '/Users/sunyue/Downloads/platform-tools/adb'),
                        help='Path to the adb executable')
    parser.add_argument('--api-url',
                        default=os.getenv('API_URL', 'https://api.openai.com/v1/chat/completions'),
                        help='API endpoint URL')
    parser.add_argument('--caption-call-method',
                        choices=['api', 'local'],
                        default='api',
                        help='Method to call captioning service')
    parser.add_argument('--caption-model',
                        choices=['qwen-vl-plus', 'qwen-vl-max', 'qwen-vl-chat-int4', 'qwen-vl-chat'],
                        default='qwen-vl-plus',
                        help='Caption model to use')
    parser.add_argument('--reflection-switch',
                        action='store_true',
                        default=False,
                        help='Enable reflection switch')
    parser.add_argument('--memory-switch',
                        action='store_true',
                        default=False,
                        help='Enable memory switch')
    try:
        args = parser.parse_args()
    except SystemExit as e:
        print("Error parsing arguments:", e)
        exit(1)

    return args


def get_perception_infos(temp_file, adb_path, screenshot_file, qwen_api, caption_call_method, caption_model, tokenizer, model, ocr_detection, ocr_recognition, groundingdino_model):
    get_screenshot(adb_path)
    
    width, height = Image.open(screenshot_file).size
    
    text, coordinates = ocr(screenshot_file, ocr_detection, ocr_recognition)
    text, coordinates = merge_text_blocks(text, coordinates)
    
    center_list = [[(coordinate[0]+coordinate[2])/2, (coordinate[1]+coordinate[3])/2] for coordinate in coordinates]
    draw_coordinates_on_image(screenshot_file, center_list)
    
    perception_infos = []
    for i in range(len(coordinates)):
        perception_info = {"text": "text: " + text[i], "coordinates": coordinates[i]}
        perception_infos.append(perception_info)
        
    coordinates = det(screenshot_file, "icon", groundingdino_model)
    
    for i in range(len(coordinates)):
        perception_info = {"text": "icon", "coordinates": coordinates[i]}
        perception_infos.append(perception_info)
        
    image_box = []
    image_id = []
    for i in range(len(perception_infos)):
        if perception_infos[i]['text'] == 'icon':
            image_box.append(perception_infos[i]['coordinates'])
            image_id.append(i)

    for i in range(len(image_box)):
        crop_save_tmp(screenshot_file, image_box[i], image_id[i])

    images = []
    for file_name in os.listdir(temp_file):
        images.append(file_name)

    if len(images) > 0:
        images = sorted(images, key=lambda x: int(x.split('/')[-1].split('.')[0]))
        image_id = [int(image.split('/')[-1].split('.')[0]) for image in images]
        icon_map = {}
        prompt = 'This image is an icon from a phone screen. Please briefly describe the shape and color of this icon in one sentence.'
        if caption_call_method == "local":
            for i in range(len(images)):
                image_path = os.path.join(temp_file, images[i])
                icon_width, icon_height = Image.open(image_path).size
                if icon_height > 0.8 * height or icon_width * icon_height > 0.2 * width * height:
                    des = "None"
                else:
                    des = generate_local(tokenizer, model, image_path, prompt)
                icon_map[i+1] = des
        else:
            for i in range(len(images)):
                images[i] = os.path.join(temp_file, images[i])
            icon_map = generate_api(images, prompt, qwen_api, caption_model)
        for i, j in zip(image_id, range(1, len(image_id)+1)):
            if icon_map.get(j):
                perception_infos[i]['text'] = "icon: " + icon_map[j]

    for i in range(len(perception_infos)):
        perception_infos[i]['coordinates'] = [int((perception_infos[i]['coordinates'][0]+perception_infos[i]['coordinates'][2])/2), int((perception_infos[i]['coordinates'][1]+perception_infos[i]['coordinates'][3])/2)]
        
    return perception_infos, width, height


def load_caption_model(caption_call_method, caption_model):
    device = torch.device("mps" if torch.backends.mps.is_available() else "cuda")

    from modelscope import snapshot_download
    from modelscope import AutoModelForCausalLM, AutoTokenizer, GenerationConfig
    from modelscope.pipelines import pipeline
    model, tokenizer = None, None
    groundingdino_dir = snapshot_download('AI-ModelScope/GroundingDINO', revision='v1.0.0')
    groundingdino_model = pipeline('grounding-dino-task', model=groundingdino_dir)

    if caption_call_method == "local":
        if caption_model == "qwen-vl-chat":
            qwen_dir = snapshot_download('qwen/Qwen-VL-Chat', revision='v1.1.0')
            model = AutoModelForCausalLM.from_pretrained(qwen_dir, device_map=device, trust_remote_code=True).eval()
            model.generation_config = GenerationConfig.from_pretrained(qwen_dir, trust_remote_code=True)
        elif caption_model == "qwen-vl-chat-int4":
            qwen_dir = snapshot_download("qwen/Qwen-VL-Chat-Int4", revision='v1.0.0')
            model = AutoModelForCausalLM.from_pretrained(qwen_dir, device_map=device, trust_remote_code=True,use_safetensors=True).eval()
            model.generation_config = GenerationConfig.from_pretrained(qwen_dir, trust_remote_code=True, do_sample=False)
        else:
            print("If you choose local caption method, you must choose the caption model from \"Qwen-vl-chat\" and \"Qwen-vl-chat-int4\"")
            exit(0)
        tokenizer = AutoTokenizer.from_pretrained(qwen_dir, trust_remote_code=True)
    elif caption_call_method == "api":
        pass
    else:
        print("You must choose the caption model call function from \"local\" and \"api\"")
        exit(0)
    return model, tokenizer, groundingdino_model


def load_ocr_model():
    from modelscope.pipelines import pipeline
    from modelscope.utils.constant import Tasks
    ocr_detection = pipeline(Tasks.ocr_detection, model='damo/cv_resnet18_ocr-detection-line-level_damo')
    ocr_recognition = pipeline(Tasks.ocr_recognition, model='damo/cv_convnextTiny_ocr-recognition-document_damo')
    return ocr_detection, ocr_recognition


def main():
    args = parse_args()
    instruction = args.instruction
    token = args.token
    qwen_api = args.qwen_api
    adb_path = args.adb_path
    API_url = args.api_url
    caption_call_method = args.caption_call_method
    caption_model = args.caption_model
    reflection_switch = args.reflection_switch
    memory_switch = args.memory_switch
    chat_mode = 'openai' if 'internlm' in API_url else 'requests'
    add_info = "If you want to tap an icon of an app, use the action \"Open app\". If you want to exit an app, use the action \"Home\""

    ### Load caption model ###
    model, tokenizer, groundingdino_model = load_caption_model(caption_call_method, caption_model)

    ### Load ocr and icon detection model ###
    ocr_detection, ocr_recognition = load_ocr_model()

    ### Init History ###
    stat_info_history = []
    thought_history = []
    summary_history = []
    action_history = []
    summary = ""
    action = ""
    completed_requirements = ""
    memory = ""
    insight = ""
    temp_file = "temp"
    screenshot = "screenshot"
    memory_record = "memory_record"
    if not os.path.exists(temp_file):
        os.mkdir(temp_file)
    else:
        shutil.rmtree(temp_file)
        os.mkdir(temp_file)
    if not os.path.exists(screenshot):
        os.mkdir(screenshot)
    if not os.path.exists(memory_record):
        os.mkdir(memory_record)
    error_flag = False

    ### Loop ###
    iter = 0
    while True:
        iter += 1
        if iter == 1:
            screenshot_file = "./screenshot/screenshot.jpg"
            perception_infos, width, height = get_perception_infos(temp_file, adb_path, screenshot_file, qwen_api, caption_call_method, caption_model, tokenizer, model, ocr_detection, ocr_recognition, groundingdino_model)
            shutil.rmtree(temp_file)
            os.mkdir(temp_file)
            
            keyboard = False
            keyboard_height_limit = 0.9 * height
            for perception_info in perception_infos:
                if perception_info['coordinates'][1] < keyboard_height_limit:
                    continue
                if 'ADB Keyboard' in perception_info['text']:
                    keyboard = True
                    break

        prompt_action = get_action_prompt(instruction, perception_infos, width, height, keyboard, summary_history, action_history, summary, action, add_info, error_flag, completed_requirements, memory)
        chat_action = add_response("user", prompt_action, chat_system_init_type='action', image=screenshot_file)
        output_action, stat_info = inference_chat(API_url, token, chat=chat_action, model='gpt-4o', mode=chat_mode, step=' Iter{} -> 1: Action '.format(iter), record_file=memory_record)
        stat_info_history.append(stat_info)

        thought = output_action.split("### Thought")[-1].split("### Action")[0].replace("\n", " ").replace(":", "").replace("  ", " ").strip()
        summary = output_action.split("### Operation")[-1].replace("\n", " ").replace("  ", " ").strip()
        action = output_action.split("### Action")[-1].split("### Operation")[0].replace("\n", " ").replace("  ", " ").strip()
        # check perception_infos and action
        # import pdb;pdb.set_trace()

        chat_action = add_response("assistant", output_action, chat_action)
        print_status_func(output_action, " Decision ")


        if memory_switch:
            prompt_memory = get_memory_prompt(insight)
            chat_action = add_response("user", prompt_memory, chat_action)
            output_memory, stat_info = inference_chat(API_url, token, chat=chat_action, model='gpt-4o', mode=chat_mode, step=' Iter{} -> 2: Memory '.format(iter), record_file=memory_record)
            stat_info_history.append(stat_info)
            chat_action = add_response("assistant", output_memory, chat_action)
            print_status_func(output_memory, " Memory ")

            output_memory = output_memory.split("### Important content ###")[-1].split("\n\n")[0].strip() + "\n"
            if "None" not in output_memory and output_memory not in memory:
                memory += output_memory
        
        if "Open app" in action:
            app_name = action.split("(")[-1].split(")")[0]
            text, coordinate = ocr(screenshot_file, ocr_detection, ocr_recognition)
            tap_coordinate = [0, 0]
            for ti in range(len(text)):
                if app_name == text[ti]:
                    name_coordinate = [int((coordinate[ti][0] + coordinate[ti][2])/2), int((coordinate[ti][1] + coordinate[ti][3])/2)]
                    tap(adb_path, name_coordinate[0], name_coordinate[1]- int(coordinate[ti][3] - coordinate[ti][1] + 30))
                    # tap(adb_path, name_coordinate[0], name_coordinate[1]- int(coordinate[ti][3] - coordinate[ti][1]))
        
        elif "Tap" in action:
            coordinate = action.split("(")[-1].split(")")[0].split(", ")
            x, y = int(coordinate[0]), int(coordinate[1])
            tap(adb_path, x, y)
        
        elif "Swipe" in action:
            coordinate1 = action.split("Swipe (")[-1].split("), (")[0].split(", ")
            coordinate2 = action.split("), (")[-1].split(")")[0].split(", ")
            x1, y1 = int(coordinate1[0]), int(coordinate1[1])
            x2, y2 = int(coordinate2[0]), int(coordinate2[1])
            slide(adb_path, x1, y1, x2, y2)
            
        elif "Type" in action:
            if "(text)" not in action:
                text = action.split("(")[-1].split(")")[0]
            else:
                text = action.split(" \"")[-1].split("\"")[0]
            type(adb_path, text)
        
        elif "Back" in action:
            back(adb_path)
        
        elif "Home" in action:
            home(adb_path)
            
        elif "Stop" in action:
            break
        
        time.sleep(5)
        
        ### Last Screenshot and Update the perception_infos ###
        last_perception_infos = copy.deepcopy(perception_infos)
        last_screenshot_file = "./screenshot/last_screenshot.jpg"
        last_keyboard = keyboard
        if os.path.exists(last_screenshot_file):
            os.remove(last_screenshot_file)
        os.rename(screenshot_file, last_screenshot_file)
        
        perception_infos, width, height = get_perception_infos(temp_file, adb_path, screenshot_file, qwen_api, caption_call_method, caption_model, tokenizer, model, ocr_detection, ocr_recognition, groundingdino_model)
        shutil.rmtree(temp_file)
        os.mkdir(temp_file)
        
        keyboard = False
        for perception_info in perception_infos:
            if perception_info['coordinates'][1] < keyboard_height_limit:
                continue
            if 'ADB Keyboard' in perception_info['text']:
                keyboard = True
                break
        
        if reflection_switch:
            prompt_reflect = get_reflect_prompt(instruction, last_perception_infos, perception_infos, width, height, last_keyboard, keyboard, summary, action, add_info)
            chat_reflect = add_response_two_image("user", prompt_reflect, chat_system_init_type='reflect', image=[last_screenshot_file, screenshot_file])
            output_reflect, stat_info = inference_chat(API_url, token, chat=chat_reflect, model='gpt-4o', mode=chat_mode, step=' Iter{} -> 3: Reflect '.format(iter), record_file=memory_record)
            stat_info_history.append(stat_info)
            reflect = output_reflect.split("### Answer ###")[-1].replace("\n", " ").strip()
            chat_reflect = add_response("assistant", output_reflect, chat_reflect)
            print_status_func(output_reflect, " Reflcetion ")
        
            if 'A' in reflect:
                thought_history.append(thought)
                summary_history.append(summary)
                action_history.append(action)
                
                prompt_planning = get_process_prompt(instruction, thought_history, summary_history, action_history, completed_requirements, add_info)
                chat_planning = add_response("user", prompt_planning, chat_system_init_type='memory')
                output_planning, stat_info = inference_chat(API_url, token, chat=chat_planning, model='gpt-4-turbo', mode=chat_mode, step=' Iter{} -> 4: Memory '.format(iter), record_file=memory_record)
                stat_info_history.append(stat_info)
                chat_planning = add_response("assistant", output_planning, chat_planning)
                print_status_func(output_planning, " Planning ")
                completed_requirements = output_planning.split("### Completed contents ###")[-1].replace("\n", " ").strip()
                
                error_flag = False
            
            elif 'B' in reflect:
                error_flag = True
                back(adb_path)
                
            elif 'C' in reflect:
                error_flag = True
        
        else:
            # same to `if 'A' in reflect`
            thought_history.append(thought)
            summary_history.append(summary)
            action_history.append(action)
            
            prompt_planning = get_process_prompt(instruction, thought_history, summary_history, action_history, completed_requirements, add_info)
            chat_planning = add_response("user", prompt_planning, chat_system_init_type='memory')
            output_planning, stat_info = inference_chat(API_url, token, chat_planning, 'gpt-4-turbo', mode=chat_mode, step=' Iter{} -> 4: Memory '.format(iter), record_file=memory_record)
            stat_info_history.append(stat_info)
            chat_planning = add_response("assistant", output_planning, chat_planning)
            print_status_func(output_planning, " Planning ")
            completed_requirements = output_planning.split("### Completed contents ###")[-1].replace("\n", " ").strip()
            
        os.remove(last_screenshot_file)

        # if 'Iter4' in [k for k, _  in stat_info_history[-1].items()][0]:
        #     import pdb;pdb.set_trace()
        #     plot_grouped_distribution(stat_info_history)
        # plot_values(stat_info_history)
        # print(stat_info_history)


if __name__ == '__main__':
    main()