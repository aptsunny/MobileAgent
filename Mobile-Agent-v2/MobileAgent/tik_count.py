import re
import json
import tiktoken
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
from matplotlib.ticker import MaxNLocator

def generate_filename(input_string):
    # 删除字符串中的所有空格
    no_spaces = input_string.replace(" ", "")
    
    # 确保文件名符合文件系统规则，移除非法字符
    # 这里我们只允许字母、数字和下划线
    safe_filename = re.sub(r'[^a-zA-Z0-9_]', '', no_spaces)
    
    # 确保文件名不以点或下划线开头或结尾
    if safe_filename.startswith(('_', '.')):
        safe_filename = 'n' + safe_filename  # 以'n'作为前缀，避免以点或下划线开头
    if safe_filename.endswith(('_', '.')):
        safe_filename = safe_filename + 'n'  # 以'n'作为后缀，避免以点或下划线结尾
    
    return safe_filename


def visualize_list_of_dicts(data_list, filename='output.png'):
    """
    可视化一个包含字典的列表。
    
    参数:
    data_list (list): 包含字典的列表
    filename (str): 输出图像的文件名
    """
    # 创建一个新的图像
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # 设置图像标题和轴标签
    ax.set_title('List of Dictionaries')
    ax.set_xlabel('Key')
    ax.set_ylabel('Value')
    
    # 设置图像的边界
    ax.set_xlim(0, len(data_list))
    ax.set_ylim(0, max([len(d.values()) for d in data_list]))
    
    # 遍历列表中的每个字典
    for i, d in enumerate(data_list):
        # 遍历字典中的每个键值对
        for j, (key, value) in enumerate(d.items()):
            # 在图像上绘制键值对
            ax.text(i+1, j, f"{key}: {value}", ha='center', va='center')
    
    # 设置图像的刻度和网格
    ax.set_xticks(range(1, len(data_list)+1))
    ax.set_xticklabels([f"Dict {i+1}" for i in range(len(data_list))], rotation=45, ha='right')
    ax.grid(True)
    
    # 保存图像到文件
    plt.savefig(filename)
    plt.close()


def save_list_of_dicts_as_json(data_list, filename='output.json'):
    """
    将包含字典的列表规范化为JSON格式并保存为文件。
    
    参数:
    data_list (list): 包含字典的列表
    filename (str): 输出JSON文件的文件名
    """
    # 确保输入是一个列表
    if not isinstance(data_list, list):
        raise ValueError("输入必须是一个列表。")
    
    # 确保列表中的每个元素都是字典
    for item in data_list:
        if not isinstance(item, dict):
            raise ValueError("列表中的每个元素必须是字典。")
    
    # 将数据写入JSON文件
    with open(filename, 'w', encoding='utf-8') as json_file:
        json.dump(data_list, json_file, ensure_ascii=False, indent=4)
    
    print(f"数据已成功保存为 {filename}")


def plot_values(data_list):
    # 初始化一个字典来存储每个key的所有值
    values_dict = {}
    
    # 遍历列表，收集每个字典的值
    for item in data_list:
        key = list(item.keys())[0]  # 获取字典的键
        value = item[key]  # 获取字典的值
        if key in values_dict:
            values_dict[key].append(value)
        else:
            values_dict[key] = [value]
    
    # 准备数据用于绘图
    keys = list(values_dict.keys())
    values = [values_dict[key] for key in keys]
    
    # 绘制柱状图
    x = np.arange(len(keys))  # 标签位置
    width = 0.35  # 柱子的宽度
    
    fig, ax = plt.subplots()
    rects = ax.bar(x, [sum(values[i]) for i in range(len(values))], width, label='Total Value')

    # 添加文本标签、标题和自定义x轴刻度标签等
    ax.set_xlabel('Step')
    ax.set_ylabel('Numbers of Prompt')
    ax.set_title('Sum of Values for Each Key')
    ax.set_xticks(x)
    ax.set_xticklabels(keys, rotation=45)
    ax.legend()

    # 填充柱状图的值
    for i in range(len(values)):
        ax.text(i, sum(values[i]), f'{sum(values[i])}', ha='center', va='bottom')

    plt.tight_layout()
    plt.show()


def plot_grouped_distribution(data_list, M=4):
    # 初始化一个字典来存储每个组的数据
    groups = {i: [] for i in range(M)}
    
    # 遍历列表，将数据分配到对应的组
    for item in data_list:
        key = list(item.keys())[0]  # 获取字典的键
        value = item[key]  # 获取字典的值
        # 将键映射到一个数字，然后根据这个数字分组
        group_index = int(key.split('->')[-1].split(':')[0][-1]) - 1
        groups[group_index].append(value)
    
    # 计算每行应该显示的子图数量
    num_per_row = int(np.ceil(np.sqrt(M)))
    
    # 创建子图
    fig, axs = plt.subplots(num_per_row, num_per_row, figsize=(10 * num_per_row, 4 * num_per_row), constrained_layout=True)
    
    # 使axs成为一个一维数组，方便迭代
    axs = axs.flatten()
    
    # 定义一个颜色列表，用于区分不同的组
    colors = plt.cm.tab10(np.linspace(0, 1, M))
    
    # 绘制每个组的统计分布图
    for i, (group_key, values) in enumerate(groups.items()):
        axs[i].hist(values, bins=20, color=colors[i], edgecolor='black', alpha=0.7)
        axs[i].set_title(f'Step {group_key + 1}')
        axs[i].set_xlabel('Value')
        axs[i].set_ylabel('Frequency')
        axs[i].tick_params(axis='x', labelsize=10)
        axs[i].tick_params(axis='y', labelsize=10)
        axs[i].xaxis.set_major_locator(MaxNLocator(integer=True))  # 确保x轴标签为整数
        
        # 添加网格线
        axs[i].grid(True, linestyle='--', alpha=0.5)
    
    # 隐藏多余的子图
    for j in range(i + 1, len(axs)):
        axs[j].axis('off')
    
    # 调整布局
    fig.suptitle('Distribution of Values by Decision Step', fontsize=16)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()


def num_tokens_from_messages(messages, step, model="gpt-4"):
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")

    tokens_per_message = 3  # 每条消息的基础Token数
    tokens_per_name = 1  # 如果有名字则增加的Token数

    num_tokens = 0
    normal_tokens = 0
    current_tokens = 0
    current_image_tokens = 0
    status = None

    print("#" * 50 + step + "#" * 50)

    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():

            try:
                if isinstance(value, str):
                    normal_tokens = len(encoding.encode(value))
                    num_tokens += normal_tokens
                    status = 'normal_str_input'
                elif isinstance(value, list):
                    for item in value:
                        if 'text' in item:
                            current_tokens = len(encoding.encode(item['text']))
                            num_tokens += current_tokens
                        # elif 'image_url' in item:
                        #     current_image_tokens = len(encoding.encode(item['image_url']['url']))
                        #     num_tokens += current_image_tokens
                    status = 'list'
            except tiktoken.exceptions.EncodingError as e:
                print(f"Encoding error: {e}")

            if key == "name":
                num_tokens += tokens_per_name
            
            """
            if isinstance(value[0], list):
                print(f"{status:<10} | key: {key:<15} | num_tokens: {normal_tokens}, {current_tokens}, {current_image_tokens}, {value[0][0]}")
            else:
                print(f"{status:<10} | key: {key:<15} | num_tokens: {normal_tokens}, {current_tokens}, {current_image_tokens}, {value[:100]}")
            """
    print(f"{step}, 总Token数量: {num_tokens}")
    return step, num_tokens