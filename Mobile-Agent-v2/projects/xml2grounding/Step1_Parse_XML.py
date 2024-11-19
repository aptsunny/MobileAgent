import xmltodict
import re, argparse, json, os, copy
import tkinter as tk
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw, ImageFont
from tkinter import simpledialog

from .mify_model import MifyModel

max_level = 0
anno_info = dict()
anno_info_collect = dict()

colors = [
    (0, 0, 0),          # 黑色
    (0, 255, 0),        # 绿色
    (0, 0, 255),        # 蓝色
    (255, 255, 0),      # 黄色
    (255, 165, 0),      # 橙色
    (128, 0, 128),      # 紫色
    (75, 0, 130),        # 靛蓝色
    (255, 215, 0),      # 金色
    (255, 105, 180),    # 粉色
    (0, 255, 255),      # 青色
    (173, 255, 47),     # 鲜绿色
    (255, 255, 255)     # 白色
]

def extract_content(text):
    # 使用正则表达式匹配方括号内的内容
    match = re.search(r'\[(.*?)\]', text)
    if match:
        return match.group(1)  # 返回匹配的第一个组的内容
    else:
        return None  # 如果没有匹配到任何内容，返回None


def get_user_input(initial_value):
    # 创建一个新窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口

    # 弹出一个对话框，让用户输入新的值
    new_value = simpledialog.askstring("输入", "请输入新的值：", initialvalue=initial_value)

    # 如果用户点击了取消或者关闭了窗口，new_value将会是None
    if new_value is None:
        return initial_value  # 返回初始值
    else:
        return new_value


def draw_rect(draw, x, y, x2, y2, outline, content=None, width=2, level=0, font=None):
    global anno_info
    
    if not content.strip():
        # print("字符串为空或仅包含空白字符")
        pass
    elif 'ScrollableGroup' in content:
        # 没意义
        pass
    # elif 'eid' in content:
    #     # 一些小框 其实有意义
    #     pass
    # elif 'ebh' in content:
    #     # 一些小框 其实有意义
    #     pass
    # elif (x2-x <30 or y2-y<30): # 看起来ok
    #     # 框筛选
    #     # elif (x2-x <50 or y2-y<50):
    #     # elif (x2-x <40 or y2-y<40): # 看起来ok
    #     pass
    # elif 'e6h' in content or 'ebr' in content:
    #     # 多余的描述省略
    #     pass
    # ## 星巴克规则 自己设定
    # elif 'icon_title' in content:
    #     # 多余的描述省略
    #     pass
    
    elif len(content)>10:
        pass
    else:
        # 框描述修改
        # content = '搜索框' if '搜索' in content else content
        
        # 星巴克修改描述
        # content = '地址' if 'location_layout' in content else content
        # content = '好礼劵' if 'coupon_button' in content else content
        # content = '啡快' if 'pickup_entry,pickup_entry_title,pickup_intro' in content else content
        # content = '返回' if 'ivBack' in content else content
        # content = '购物车' if 'ivShoppingBag' in content else content
        # content = '优惠加购' if 'addToCartButton' in content else content
        # content = '搜索框' if 'tvSearch' in content else content
        # content = '帮TA带' if 'groupOrderEntrance' in content else content
        # content = '去结算' if 'tvSubmit' in content else content
        
        # 不一定是content 也可能是 text
        
        # if 'ScrollableGroup' in content:
        #     import pdb;pdb.set_trace()
        # 打印级别
        # if level == 6:
        print(level, "  " * level, (x, y, x2, y2), content)
        # import pdb;pdb.set_trace()
        anno_info.update({content: (x, y, x2, y2)})
        
        draw_text(draw, content, x, y, font)
        
        try:
            draw.rectangle((x, y, x2, y2), outline=colors[level], width=width)
        except:
            pass
            print((x, y, x2, y2))
            # import pdb;pdb.set_trace()
        # draw.rectangle((x, y, x2, y2), outline=outline, width=width)
        # draw.rectangle((x, y, x2, y2), outline=outline, width=8-level) # 从粗到细，级别越高，越深的框


def draw_text(draw, text, x, y, font, fill='red'):
    draw.text((x+10, y-30), text, font=font, fill=fill)


def child_in_root(root_bbox, child_bbox):
    root_bbox = [int(p) for p in root_bbox.split(' ')]
    child_bbox = [int(p) for p in child_bbox.split(' ')]
    return root_bbox[0] <= child_bbox[0] and \
           root_bbox[1] <= child_bbox[1] and \
           root_bbox[2] >= child_bbox[2] and \
           root_bbox[3] >= child_bbox[3]


def parse_item(item):
    # print(item.attrib)
    tag = item.tag.split('.')[-1]
    
    if tag == 'TextView':
        tag = tag[:-4]
        content = item.attrib['text']
    elif tag in ['ImageView']:
        tag = tag[:-4]
        if 'content-desc' in item.attrib:
            content = item.attrib['content-desc']
        # elif 'resource-id' in item.attrib:
        #     content = item.attrib['resource-id'].split('/')[-1]
        elif 'text' in item.attrib:
            content = item.attrib['text']
            # import pdb;pdb.set_trace()
        else:
            import pdb;pdb.set_trace()
            content = ''
    else:
        # import pdb;pdb.set_trace()
        if 'content-desc' in item.attrib and item.attrib['content-desc'] != '':
            content = item.attrib['content-desc']
        elif 'text' in item.attrib and item.attrib['text'] != '':
            content = item.attrib['text']
        else:
            content = ''
            # content = item.attrib['resource-id']
            # import pdb;pdb.set_trace()

        # 额外针对 text 的 补丁
        # print(item.attrib)
        # if 'text' in item.attrib:
        #     if item.attrib['text'] != '':
        #         # import pdb;pdb.set_trace()
        #         content = item.attrib['text']

    if len(item) == 0 and content == '':
        # 使用 resource-id
        # if 'resource-id' in item.attrib:
        #     content = item.attrib['resource-id'].split('/')[-1]
        # 使用 text 
        if 'text' in item.attrib:
            if item.attrib['text'] != '':
                content = item.attrib['text']    
                import pdb;pdb.set_trace()

    print(content, tag, item.attrib['bounds'])
    
    return {
        'content': content,
        'position': item.attrib['bounds'].replace(',', ' ').replace('][', ' ').replace('[', '').replace(']', ''),
        'selected': item.attrib['selected'],
        'clickable': item.attrib['clickable'],
        # 'scrollable': item.attrib['scrollable'],
        'long-clickable': item.attrib['long-clickable']
    }


def annotate_root_by_child(root):
    # print('-----------------------annotate_root_by_child') 如果有子项，子项
    content = []
    for child in root:
        if len(child) == 0:
            if child.attrib['focusable'] == 'false':
                child_node = parse_item(child)
                content.append(child_node['content'])
            else:
                continue
        else:
            if child.attrib['focusable'] == 'false':
                child_node = parse_item(child)
                content.append(child_node['content'])
            else:
                continue
            child_annotation = annotate_root_by_child(child)
            content += child_annotation
    # print(f'{content}')
    # print('-----------------------')
    return content


def parse_single_item(item):
    # label = 0
    if 'focusable' not in item.attrib:
        # print(f'[warning] {item.tag} has no atrribute "focusable"')
        return None

    elif item.attrib['focusable'] == 'false' and item.attrib['clickable'] == 'false' \
        and item.attrib['long-clickable'] == 'false'and item.attrib['scrollable'] == 'false':
        return None
    
    elif item.attrib['scrollable'] == 'true' and item.attrib['clickable'] == 'false'and item.attrib['long-clickable'] == 'false':
        res = parse_item(item)
        if res['content'] == '':
            res['content'] = 'ScrollableGroup'
        # label = 1
    else:
        # label = 2
        res = parse_item(item)
        
        if res['content'] == '':
            # label = 2.5 子项关系输出
            content = annotate_root_by_child(item)
            content = [x for x in content if x != '']
            res['content'] = ','.join(content) if res['content'] == '' else res['content']
        
        # label = 2.6
        # if res['content'] == '' and 'resource-id' in item.attrib:
        #     res['content'] = item.attrib['resource-id'].split('/')[-1]
        # 使用 text 
        if res['content'] == '' and 'text' in item.attrib:
            if item.attrib['text'] != '':
                content = item.attrib['text']    
                import pdb;pdb.set_trace()

        # if res['content'] == '' and 'text' in item.attrib:
        #     if item.attrib['text'] != '':
        #         res['content'] = item.attrib['text']
        # elif res['content'] == '' and 'resource-id' in item.attrib:
        #     res['content'] = item.attrib['resource-id'].split('/')[-1]
        
        # import pdb;pdb.set_trace()
    # print('[INFO] Valiad infomation')

    # print(label, res['content'])
    return res


def parse_root(root):
    root_node = parse_single_item(root)

    if len(root) == 0:
        if root_node is not None:
            return root_node
        else:
            return None
    elif len(root) == 1 and root_node is None:
        return parse_root(root[0])
    else:
        child_nodes = []
        for child in root:
            child_node = parse_root(child)
            if 'bounds' in root.attrib and 'bounds' in child.attrib:
                # pass
                assert child_in_root(
                    root.attrib['bounds'].replace(',', ' ').replace('][', ' ').replace('[', '').replace(']', ''), 
                    child.attrib['bounds'].replace(',', ' ').replace('][', ' ').replace('[', '').replace(']', '')
                ), f'{child.attrib["bounds"]} is not in {root.attrib["bounds"]}'
            if child_node is not None:
                if isinstance(child_node, list):
                    child_nodes +=child_node
                else:
                    child_nodes.append(child_node)
        if len(child_nodes) != 0:
            if root_node is None:
            #     root_node = parse_item(root)
                root_node = child_nodes if len(child_nodes) > 1 else child_nodes[0]
            else:
                root_node['children'] = child_nodes if len(child_nodes) > 1 else child_nodes[0]
        return root_node


def parse_ui_xml(xml_file):
    tree = ET.ElementTree(file=xml_file)
    root = tree.getroot()
    # tree = ET.parse(xml_file)
    # root = tree.getroot()
    # print(root)
    # print(root.tag, root.attrib)

    return parse_root(root)


def simplify_single(dict_data):
    res = [dict_data['position']]
    if dict_data['clickable'] == 'true':
        res.append('clickable')
    if dict_data['long-clickable'] == 'true':
        res.append('long-clickable')
    if dict_data['selected'] == 'true':
        res.append('selected')
    return {dict_data['content']: res}


def simplify_json(dict_data):
    if 'children' in dict_data:
        child_data = simplify_json(dict_data['children'])
        res = simplify_single(dict_data)
        res[dict_data['content']].append(child_data)
    else:
        if isinstance(dict_data, list):
            res = []
            for item in dict_data:
                res.append(simplify_json(item))
        else:
            res = simplify_single(dict_data)
    return res


def draw_elements(draw, data, font, level=0):
    # 层级全局变量
    global max_level
    max_level = max(max_level, level)
    
    if isinstance(data, dict) and 'position' in data:
        try:
            x, y, w, h = map(int, data['position'].split())
            content = data['content']
        except:
            import pdb;pdb.set_trace()
        if data['clickable'] == 'true':
            draw_rect(draw, x, y, w, h, 'blue', content, width=4, level=level, font=font)
        else:
            draw_rect(draw, x, y, w, h, 'red', content, width=2, level=level, font=font)

        # if 'content' in data:
        #     draw_text(draw, data['content'], x, y, font)
        
        if 'children' in data:
            # list or dict
            if isinstance(data['children'], list):
                for idx, child in enumerate(data['children']):
                    draw_elements(draw, child, font, level + 1)
            elif isinstance(data['children'], dict):
                draw_elements(draw, data['children'], font, level + 1)
            else:
                import pdb;pdb.set_trace()
                
    elif isinstance(data, list):
        # import pdb;pdb.set_trace()
        pass
    else:
        # import pdb;pdb.set_trace()
        pass


def load_json_data(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data


def visualize_graph(json_file_path, png_file_path, output_file_path, font_path):
    data = load_json_data(json_file_path)
    background_image = Image.open(png_file_path)
    draw = ImageDraw.Draw(background_image)
    font = ImageFont.truetype(font_path, 30)
    
    for idx, item in enumerate(data):
        draw_elements(draw, item, font)
    
    # background_image.show()
    background_image.save(output_file_path)


def plan_v1_parse_ui_xml(xml_file, target_prefix, png_file_path, font_path):
    save_json, save_txt = xml_file.replace(target_prefix, '-vh.json'), \
        xml_file.replace(target_prefix, '-vh.txt')
    output_file_path = png_file_path.replace('.png', '_visualization.png')
    # 解析ui信息主函数 来自 yueyue
    dict_data = parse_ui_xml(xml_file)
    with open(save_json, 'w', encoding='utf8') as f:
        json.dump(dict_data, f, ensure_ascii=False, indent=4, separators=(',', ':'))
    with open(save_txt, 'w', encoding='utf8') as f:
        json.dump(simplify_json(dict_data), f, ensure_ascii=False, indent=4, separators=(',', ':'))

    # vis bbox
    if os.path.exists(png_file_path):
        visualize_graph(save_json, png_file_path, output_file_path, font_path)
    else:
        print(f"No matching PNG file found for {save_json}")
    return


def extract_bounds_and_info(node, info_list=[], level=0):
    # 获取当前节点的信息
    bounds = node.get('@bounds', None)
    if bounds:
        # 解析bounds字符串
        coords = bounds.strip('[]').split('][')
        top_left = tuple(map(int, coords[0].split(',')))
        bottom_right = tuple(map(int, coords[1].split(',')))

        info_list.append({
            'class': node.get('@class'),
            'bounds': (top_left, bottom_right),
            'text': node.get('@text', ''),
            'index': node.get('@index', ''),
            'resource-id': node.get('@resource-id', ''),
            'clickable': node.get('@clickable', 'false'),
            'level': level
        })
    
    # 递归处理子节点
    children = node.get('node')
    if isinstance(children, list):
        for child in children:
            extract_bounds_and_info(child, info_list, level=level+1)
    elif isinstance(children, dict):
        extract_bounds_and_info(children, info_list, level=level+1)

    return info_list


def longest_strictly_increasing_subsequence(lst, equal=False):
    # 初始化最大长度和当前长度
    max_length = 0
    current_length = 1

    # 遍历列表，比较每个元素和它前面的元素
    for i in range(1, len(lst)):
        if equal:
            # 如果当前元素大于前一个元素，递增当前长度
            if lst[i] >= lst[i-1]:
                current_length += 1
            else:
                # 如果当前元素不大于前一个元素，比较当前长度和最大长度，然后重置当前长度为1
                max_length = max(max_length, current_length)
                current_length = 1
        else:
            # 如果当前元素大于前一个元素，递增当前长度
            if lst[i] > lst[i-1]:
                current_length += 1
            else:
                # 如果当前元素不大于前一个元素，比较当前长度和最大长度，然后重置当前长度为1
                max_length = max(max_length, current_length)
                current_length = 1
        

    # 最后比较一次，因为递增序列可能在列表的末尾
    max_length = max(max_length, current_length)

    # 如果最大长度大于1，返回最大长度
    if max_length > 1:
        return max_length
    else:
        return 0


def merge_from_view_group_idx(elements):
    # 找到ViewGroup的索引
    view_group_index_list = []
    for i, element in enumerate(elements):
        if element["class"] in ["android.widget.LinearLayout", "android.view.ViewGroup"]:
            view_group_index_list.append(i)

    # 如果找到了ViewGroup，并且它的index 与 子idex递增，则更新它的text
    find_view_group_index = []
    find_view_group_length = []
    for view_group_index in view_group_index_list:
        sub_increasing = []
        sub_elements_index_range = 5 # 最长看4个
        for i in range(view_group_index + 1, view_group_index+sub_elements_index_range):
            if i >= len(elements):
                break
            # print(view_group_index, elements[i]["index"])
            sub_increasing.append(elements[i]["index"])

            # 检查子元素的index是否与ViewGroup的index相同
            # if elements[i]["index"] == view_group["index"] + 1:
            #     if elements[i]["text"]:
            #         child_texts.append(elements[i]["text"])
            # else:
            #     break
        # 将子元素的text连接起来
        # view_group["text"] = " - ".join(child_texts)

        # if view_group_index == 136:
        #     import pdb;pdb.set_trace()
        if longest_strictly_increasing_subsequence(sub_increasing) !=0:
            find_view_group_index.append(view_group_index)
            find_view_group_length.append(longest_strictly_increasing_subsequence(sub_increasing))

    # import pdb;pdb.set_trace()
    for i, view_group_index in enumerate(find_view_group_index):
        child_texts = []
        view_group = elements[view_group_index]

        for j in range(view_group_index + 1, view_group_index+find_view_group_length[i]+1):
            if elements[j]["text"]:
                child_texts.append(elements[j]["text"])
        
        # 将子元素的text连接起来
        cancat_result = ",".join(child_texts)
        view_group["text"] = cancat_result if cancat_result != '' else view_group["text"]

        elements[view_group_index] = view_group
        # print(i, ",".join(child_texts))
        # import pdb;pdb.set_trace()

    # 打印更新后的元素列表
    # for element in elements:
    #     print(f"Clickable: {element['clickable']}, Class: {element['class']}, Bounds: {element['bounds']}, Text: {element['text']}, Index: {element['index']}, Resource ID: {element['resource_id']}")
    
    # for i in find_view_group_index:
    #     print(i, elements[i]["text"])
    # import pdb;pdb.set_trace()
    return elements


def plan_v2_parse_ui_xml(xml_file, check_xml_list=False):
    step1_data_info=[]
    # xml2json
    with open(xml_file, encoding='utf-8') as file:
        xml_data = file.read()
    data_dict = xmltodict.parse(xml_data)

    # 通过递归得到 bounds 和 text 的 list 信息
    result = extract_bounds_and_info(data_dict['hierarchy']['node'], info_list=[])

    # 打印 检查基础JSON信息, level 是层级关系
    if check_xml_list:
        for idx, item in enumerate(result):
            # if item['clickable'] == 'true':
            print(f"{idx}: {item['level']}, Clickable: {item['clickable']}, Class: {item['class']}, Bounds: {item['bounds']}, Text: {item['text']}, Index: {item['index']}, Resource ID: {item['resource-id']}")

    # 复杂的筛选逻辑 根据 android.view.ViewGroup 以及后续序号是 Index 0、1、2等，将后续的信息 结合到当前 text
    result_1 = merge_from_view_group_idx(result)

    for idx, info_dict in enumerate(result_1):
        # 默认不显示
        box_color = 'red'
        font_color = 'red'
        vis_flag = False
        top_left, bottom_right = info_dict['bounds']
        text, resource_id, clickable, index = info_dict['text'], info_dict['resource-id'], info_dict['clickable'], info_dict['index']
        class_name = info_dict['class']

        # debug text
        label_text = f"Idx: {idx}\nText: {text}\nResource ID: {resource_id}\nClickable: {clickable}\nIndex: {index}"
        
        # 1. 可点击 优先级最高，但是缺少详细准确的描述
        # - resource_id 的信息优先 因为是明确的信息
        # - 有框，但是信息缺失
        knowledge_base = [
            'ivBackButton',
            'ivIngredientButton',
            'ivStepperReduce',
            'ivStepperAdd',
            'location_layout',
            'inboxMessageBlurView',
            'avatarView',
            'starLayout',
            'pickup_entry_layout',
            'delivery_entry_layout',
            'groupOrderEntrance',
            'tvStoreName',
            'ivReservation',
            'closeImage',
            'tvSearch',
            'ivShoppingBag',
            'nowOrderContainer',
            'preOrderContainer',
            'ivClose',
            'ivClearHistory',
            'etInput',
            'ivBack',
            'ivBackButton',
            'addToCart',
            'lyToPurchase',
            'ivCouponImage',
            'catalogLayout',
            
            'function_arrow',
        ]

        # if idx==64:
        #     import pdb;pdb.set_trace()
        if clickable == 'false' and class_name == 'android.widget.TextView' and text != '':
            label_text = text
            vis_flag = True

        elif clickable == 'true' and resource_id.split('/')[-1] in knowledge_base:
            if resource_id.split('/')[-1] == 'ivBackButton':
                label_text = '返回'
            elif resource_id.split('/')[-1] == 'ivIngredientButton':
                label_text = '详细信息'
            elif resource_id.split('/')[-1] == 'ivStepperReduce':
                label_text = '减去一杯'
            elif resource_id.split('/')[-1] == 'ivStepperAdd':
                label_text = '增加一杯'
            elif resource_id.split('/')[-1] == 'location_layout':
                label_text = '目前定位'
            elif resource_id.split('/')[-1] == 'inboxMessageBlurView':
                label_text = '应用消息'
            elif resource_id.split('/')[-1] == 'avatarView':
                label_text = '标志'
            elif resource_id.split('/')[-1] == 'starLayout':
                label_text = '星标'
            elif resource_id.split('/')[-1] == 'pickup_entry_layout':
                label_text = '咖快'
            elif resource_id.split('/')[-1] == 'delivery_entry_layout':
                label_text = '专星送'
            elif resource_id.split('/')[-1] == 'groupOrderEntrance':
                label_text = '帮TA带'
            elif resource_id.split('/')[-1] == 'tvStoreName':
                label_text = '门店名'
            elif resource_id.split('/')[-1] == 'ivReservation':
                label_text = '预约'
            elif resource_id.split('/')[-1] == 'closeImage':
                label_text = '返回'
            elif resource_id.split('/')[-1] == 'tvSearch':
                label_text = '搜索框'
            elif resource_id.split('/')[-1] == 'ivShoppingBag':
                label_text = '购物车'
            elif resource_id.split('/')[-1] == 'nowOrderContainer':
                label_text = '即刻取单'
            elif resource_id.split('/')[-1] == 'preOrderContainer':
                label_text = '预约取单'
            elif resource_id.split('/')[-1] == 'ivClose':
                label_text = '关闭'
            elif resource_id.split('/')[-1] == 'ivClearHistory':
                label_text = '清除历史'
            elif resource_id.split('/')[-1] == 'etInput':
                label_text = '输入文字'
            elif resource_id.split('/')[-1] == 'ivBack':
                label_text = '返回'
            elif resource_id.split('/')[-1] == 'ivBackButton':
                label_text = '返回按钮'
            elif resource_id.split('/')[-1] == 'addToCart':
                label_text = '添加至购物车'
            elif resource_id.split('/')[-1] == 'lyToPurchase':
                label_text = '去加购'
            elif resource_id.split('/')[-1] == 'ivCouponImage':
                label_text = '优惠券'
            elif resource_id.split('/')[-1] == 'catalogLayout':
                label_text = '浏览星礼卡'

            elif resource_id.split('/')[-1] == 'function_arrow':
                label_text = '详细查看'

            vis_flag = True

        elif clickable == 'true' and resource_id.split('/')[-1] not in knowledge_base:
            if text != '':
                label_text = text
            else:
                label_text = idx
                # label_text = str(idx)
                # label_text = label_text
                # 如果是数字，这个时候再调用gpt4o去 refer

                # pass
                # continue

            # elif text == '' and resource_id == '':
            #     label_text = 'Maybe 大框'
            #     # 这类可以用模型给到信息
            
            # elif clickable == 'false':
            #     pass
            
            vis_flag = True

        # anchor 统计
        if vis_flag:
            # 框筛选 按照 1.长宽比例 2.面积 3.h_diff 至少大200
            h_diff = bottom_right[1] - top_left[1]
            w_diff = bottom_right[0] - top_left[0]
            # print(h_diff * w_diff)
            # h_diff/w_diff > 0.13 有些字体45
            if h_diff > 44 and h_diff * w_diff < 3000000:
                step1_data_info.append((top_left, bottom_right, box_color, label_text, font_color))

    # import pdb;pdb.set_trace()
    return step1_data_info


def parse_args():
    parser = argparse.ArgumentParser(description='XML Parse')
    parser.add_argument('dump_bbox_output', help='xml_anno_info_single_folder.json')
    parser.add_argument('--trajectory-xml-folder',
                        default=r"D:\workspace\feikuai\2024-10-23_20-17-28",
                        help='Method to call captioning service')
    parser.add_argument('--target-prefix',
                        default='.xml',
                        help='x')
    parser.add_argument('--font-path',
                        default='Mobile-Agent-v2/projects/ttf_file/SimSun.ttf',
                        help='Path to the adb executable')
    parser.add_argument('--need-modify',
                        action='store_true',
                        default=False,
                        help='need to modify by handcode')
    parser.add_argument('--check-xml-list',
                        action='store_true',
                        default=False,
                        help='Enable memory switch')
    try:
        args = parser.parse_args()
    except SystemExit as e:
        print("Error parsing arguments:", e)
        exit(1)

    return args


def main():
    global anno_info, anno_info_collect

    args = parse_args()
    trajectory_xml_folder = args.trajectory_xml_folder # 完整数据路径，包含XML数据
    target_prefix = args.target_prefix
    font_path = args.font_path
    dump_bbox_output = args.dump_bbox_output
    need_modify = args.need_modify # 如果需要人工检查, 弹出窗口让用户修改结果
    check_xml_list = args.check_xml_list

    # parse2 的结果
    referring_prompt = "请以'[显示内容]'的格式，用10个字以内简述手机截图中红框区域的具体显示内容, 如果空白或者无意义，则填写[空]"
    # parse3 omniparse

    # gpt4o referring 
    model = MifyModel()

    # parse xml
    for subdir, dirs, files in os.walk(trajectory_xml_folder):
        for file in files:
            # print(subdir, dirs, files)
            # import pdb;pdb.set_trace()
            # if True:
            try:
                if file.endswith(target_prefix):
                    xml_file = os.path.join(subdir, file)
                    png_file_path = xml_file.replace(target_prefix, '.png').replace('ui_dump', 'screenshot')
                    output_file_path_plan2 = png_file_path.replace('.png', '_visualization_plan2.png')
                    save_anchor_dir = png_file_path.replace('.png', '_bbox')
                    
                    # unit test
                    # if file != 'ui_dump_1729648264.xml':

                    # if file != 'ui_dump_1729685850.xml':
                    # if file != 'ui_dump_1729685865.xml':
                    # if file != 'ui_dump_1729685884.xml':
                    # if file != 'ui_dump_1729685901.xml':
                    # if file != 'ui_dump_1729685924.xml':
                    # if file != 'ui_dump_1729685934.xml':
                    # if file != 'ui_dump_1729685959.xml':
                    # if file != 'ui_dump_1729685975.xml':
                    # if file != 'ui_dump_1729685999.xml':
                    # if file != 'ui_dump_1729686009.xml':
                    # if file != 'ui_dump_1729686039.xml':
                    # if file != 'ui_dump_1729686054.xml':
                    # if file != 'ui_dump_1729686070.xml':
                    if file != 'ui_dump_1729686079.xml':
                        continue
                    
                    # parse1 的结果
                    # plan_v1_parse_ui_xml(xml_file, target_prefix, png_file_path, font_path)
                    
                    # parse2 的结果
                    step1_data_info = plan_v2_parse_ui_xml(xml_file, check_xml_list)
                    print('\n{} bbox: {}\n'.format(xml_file, len(step1_data_info)))
                    # import pdb;pdb.set_trace()
                    # ((77, 1074), (1200, 1143), 'red', '选择支付方式', 'red')
                    # ((1085, 2133), (1149, 2197), 'red', 34, 'red')

                    # parse3 omniparse
                    # plan_v3_omniparse

                    # vis and record
                    image = Image.open(png_file_path)
                    font = ImageFont.truetype(font_path, 36)
                    draw = ImageDraw.Draw(image)
                    for anchor_idx, info in enumerate(step1_data_info):
                        top_left, bottom_right, box_color, label_text, font_color = info
                        
                        # if label_text is integer, need referring.
                        if isinstance(label_text, str):
                            draw.rectangle([top_left, bottom_right], outline=box_color, width=5)
                            draw.text((top_left[0] + 5, top_left[1]), label_text, fill=font_color, font=font)
                        else:
                            if not os.path.exists(save_anchor_dir):
                                os.makedirs(save_anchor_dir)

                            # gpt4o referring
                            need_image = Image.open(png_file_path)
                            single_anchor_draw = ImageDraw.Draw(need_image)
                            single_anchor_draw.rectangle([top_left, bottom_right], outline=box_color, width=10)
                            # need_image.show()
                            save_bbox_path = os.path.join(save_anchor_dir, 'bbox_{}.png'.format(anchor_idx))
                            need_image.save(save_bbox_path)

                            status, answer = model.get_model_response(referring_prompt, [save_bbox_path])
                            if status:
                                gpt4o_result = answer

                            if need_modify:
                                gpt4o_result = get_user_input(gpt4o_result)
                            label_text = extract_content(gpt4o_result)

                            draw.rectangle([top_left, bottom_right], outline=box_color, width=5)
                            draw.text((top_left[0] + 5, top_left[1]), label_text, fill=font_color, font=font)

                        if label_text != '空':
                            anno_info.update({label_text: (top_left[0], top_left[1], bottom_right[0], bottom_right[1])})
                            print(anchor_idx, label_text, top_left, bottom_right)

                    image.save(output_file_path_plan2)
                    anno_info_collect.update({png_file_path: copy.deepcopy(anno_info)})
                    anno_info.clear()
                
                    # single image vis
                    # import pdb;pdb.set_trace()
                    with open('{}.json'.format(save_anchor_dir), 'w', encoding='utf-8') as f:
                        json.dump(anno_info_collect, f, ensure_ascii=False, indent=4)
            except:
                # import pdb;pdb.set_trace()
                print('error in {}'.format(file))

    # dump trajectory_xml_folder bbox
    with open(dump_bbox_output, 'w', encoding='utf-8') as f:
        json.dump(anno_info_collect, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    main()