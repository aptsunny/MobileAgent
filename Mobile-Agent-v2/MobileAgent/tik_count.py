import re
import json
import tiktoken
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator

def generate_filename(input_string):
    # Delete all the spaces in the string
    no_spaces = input_string.replace(" ", "")
    
    # Make sure the file name meets the file system rules, remove illegal characters
    # Here we only allow letters, numbers and lines
    safe_filename = re.sub(r'[^a-zA-Z0-9_]', '', no_spaces)
    
    # Make sure that the file name does not start or start or end the line
    if safe_filename.startswith(('_', '.')):
        # With 'n' as a prefix, avoid starting with a point or down line
        safe_filename = 'n' + safe_filename
    if safe_filename.endswith(('_', '.')):
        # With 'n' as a suffix, avoid ending or drawing lines
        safe_filename = safe_filename + 'n'
    
    return safe_filename


def update_value_in_dict_single_key(d, new_value, index=1):
    key = next(iter(d))
    if index >= len(d[key]):
        print(f"Index {index} out of range for list associated with the single key '{key}'.")
        return False
    d[key][index] = new_value
    if any(element is None for element in d[key]):
        print(f"Warning: The list associated with the single key '{key}' contains None values.")
        return False
    return True


def visualize_list_of_dicts(data_list, filename='output.png'):
    # Create a new image
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Set image title and axis tag
    ax.set_title('List of Dictionaries')
    ax.set_xlabel('Key')
    ax.set_ylabel('Value')
    
    # Set the boundary of the image
    ax.set_xlim(0, len(data_list))
    ax.set_ylim(0, max([len(d.values()) for d in data_list]))
    
    # Each dictionary in the list of traversal list
    for i, d in enumerate(data_list):
        # Each key value pair in the dictionary
        for j, (key, value) in enumerate(d.items()):
            # Draw a key value pair on the image
            ax.text(i+1, j, f"{key}: {value}", ha='center', va='center')
    
    # Set the scale and grid of the image
    ax.set_xticks(range(1, len(data_list)+1))
    ax.set_xticklabels([f"Dict {i+1}" for i in range(len(data_list))], rotation=45, ha='right')
    ax.grid(True)
    
    # Save the image to the file
    plt.savefig(filename)
    plt.close()


def save_list_of_dicts_as_json(data_list, filename='output.json'):
    # Make sure that input is a list
    if not isinstance(data_list, list):
        raise ValueError("输入必须是一个列表。")
    
    # Make sure that each element in the list is a dictionary
    for item in data_list:
        if not isinstance(item, dict):
            raise ValueError("列表中的每个元素必须是字典。")
    
    # Write the data into the json file
    with open(filename, 'w', encoding='utf-8') as json_file:
        json.dump(data_list, json_file, ensure_ascii=False, indent=4)
    
    print(f"数据已成功保存为 {filename}")


def plot_values(data_list):
    # Initialize a dictionary to store all the values ​​of each key
    values_dict = {}
    
    # Traversing a list, collect the value of each dictionary
    for item in data_list:
        key = list(item.keys())[0]  # Get the key to the dictionary
        value = item[key]  # Get the value of the dictionary
        if key in values_dict:
            values_dict[key].append(value)
        else:
            values_dict[key] = [value]
    
    # Preparation data is used for drawing
    keys = list(values_dict.keys())
    values = [values_dict[key] for key in keys]
    
    # Draw the column
    x = np.arange(len(keys))  # Label
    width = 0.35  # Pillar width
    
    fig, ax = plt.subplots()
    rects = ax.bar(x, [sum(values[i]) for i in range(len(values))], width, label='Total Value')

    # Add text tags, title, and custom X -axis scale tags, etc.
    ax.set_xlabel('Step')
    ax.set_ylabel('Token Counts')
    ax.set_title('Num_Tokens_from_String')
    ax.set_xticks(x)
    ax.set_xticklabels(keys, rotation=45)
    ax.legend()

    # The value of filling the pillar diagram
    for i in range(len(values)):
        ax.text(i, sum(values[i]), f'{sum(values[i])}', ha='center', va='bottom')

    plt.tight_layout()
    plt.show()


def plot_values_entire(data_list):
    # Initialize a dictionary to store all the values of each key
    values_dict = {}
    
    # Traversing a list, collect the value of each dictionary
    for item in data_list:
        for key, value_list in item.items():
            if key not in values_dict:
                values_dict[key] = []
            values_dict[key].extend(value_list)
    
    # Preparation data is used for drawing
    keys = list(values_dict.keys())
    values = [values_dict[key] for key in keys]
    
    # Number of bars per key
    num_values_per_key = [len(values[i]) for i in range(len(values))]
    total_keys = len(keys)
    
    # Set the width of the bars
    width = 0.2
    
    # Position of the bars
    x = np.arange(total_keys)
    
    # Plotting the bars
    fig, ax = plt.subplots()
    for i, key in enumerate(keys):
        value_list = values[i]
        for j, value in enumerate(value_list):
            position = x[i] + j * width
            ax.bar(position, value, width, label=f'{key} Value {j+1}' if j == 0 else "")
    
    # Add text tags, title, and custom X-axis scale tags, etc.
    ax.set_xlabel('Key')
    ax.set_ylabel('Token Counts')
    ax.set_title('Num_Tokens_from_String')
    ax.set_xticks(x)
    ax.set_xticklabels(keys, rotation=45)
    ax.legend()

    # The value of filling the pillar diagram
    for i, key in enumerate(keys):
        for j, value in enumerate(values[i]):
            ax.text(i + j * width, value, f'{value}', ha='center', va='bottom')

    plt.tight_layout()
    plt.show()


def plot_grouped_distribution(data_list, M=4):
    # Initialize a dictionary to store the data of each group
    groups = {i: [] for i in range(M)}
    
    # Traversing the list, distribute the data to the corresponding group
    for item in data_list:
        key = list(item.keys())[0]  # Get the key to the dictionary
        value = item[key]  # Get the value of the dictionary
        # Map the key to a number, and then group according to this number
        group_index = int(key.split('->')[-1].split(':')[0][-1]) - 1
        groups[group_index].append(value)
    
    # Calculate the number of sub -diagrams that should be displayed in each line
    num_per_row = int(np.ceil(np.sqrt(M)))
    
    # Create a subgraph
    fig, axs = plt.subplots(num_per_row, num_per_row, figsize=(10 * num_per_row, 4 * num_per_row), constrained_layout=True)
    
    # Make Axs a one -dimensional array, which is convenient for iteration
    axs = axs.flatten()
    
    # Define a color list to distinguish different groups
    colors = plt.cm.tab10(np.linspace(0, 1, M))
    
    # Draw the statistical distribution map of each group
    for i, (group_key, values) in enumerate(groups.items()):
        axs[i].hist(values, bins=20, color=colors[i], edgecolor='black', alpha=0.7)
        axs[i].set_title(f'Step {group_key + 1}')
        axs[i].set_xlabel('Value')
        axs[i].set_ylabel('Frequency')
        axs[i].tick_params(axis='x', labelsize=10)
        axs[i].tick_params(axis='y', labelsize=10)
        axs[i].xaxis.set_major_locator(MaxNLocator(integer=True))  # Make sure the X -axis tag is an integer
        
        # Add grid line
        axs[i].grid(True, linestyle='--', alpha=0.5)
    
    # Hidden extra sub -map
    for j in range(i + 1, len(axs)):
        axs[j].axis('off')
    
    # Adjust the layout
    fig.suptitle('Distribution of Values by Decision Step', fontsize=16)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()


def plot_grouped_distribution_entire(data_list, M=4):
    # Initialize a dictionary to store the data of each group
    grouped_data = {step: {} for step in range(1, M+1)}
    
    # Traversing the list, distribute the data to the corresponding group
    for item in data_list:
        for key, value in item.items():
            # Extract the iteration number and step from the key
            iteration, step_info = key.split(' -> ')
            step = int(step_info.split(':')[0])
            iteration = iteration.strip()  # Remove any leading whitespace
            
            if step not in grouped_data:
                grouped_data[step] = {}
            
            if iteration not in grouped_data[step]:
                grouped_data[step][iteration] = {'input token': [], 'output token': []}
            
            # Assign the values to the corresponding group and type
            grouped_data[step][iteration]['input token'].append(value[0])
            grouped_data[step][iteration]['output token'].append(value[1])
    
    # Create a figure for all subgraphs
    fig, axs = plt.subplots(2, 2, figsize=(10, 8))
    axs = axs.flatten()  # Flatten the array for easier indexing
    
    # Create a subgraph for each step
    for step, ax in enumerate(axs):
        if step+1 in grouped_data:
            iterations_data = grouped_data[step+1]
            positions = np.arange(len(iterations_data))
            width = 0.2  # Bar width
            
            for i, (iteration, values) in enumerate(iterations_data.items()):
                nums1 = values['input token']
                nums2 = values['output token']
                rects1 = ax.bar(positions[i], nums1, width, label=f'Input Token', alpha=0.7, edgecolor='black')
                rects2 = ax.bar(positions[i], nums2, width, bottom=nums1, label=f'Output Token', alpha=0.7, edgecolor='black')
            
                # Add text labels for nums1
                for rect, num in zip(rects1, nums1):
                    ax.text(rect.get_x() + rect.get_width() / 2, rect.get_height(), f'{num}', ha='center', va='bottom')
                
                # Add text labels for nums2
                for rect, num in zip(rects2, nums2):
                    ax.text(rect.get_x() + rect.get_width() / 2, num + rects1[0].get_height(), f'{num}', ha='center', va='bottom')
            
            ax.set_title(f'Step {step+1}', fontsize=7)
            # ax.set_xlabel('Iteration', fontsize=6)
            ax.set_ylabel('Value', fontsize=6)
            ax.set_xticks(positions, list(iterations_data.keys()))
            ax.set_xticklabels(list(iterations_data.keys()), fontsize=5)
            ax.legend(fontsize=6)
            ax.grid(True, linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.show()


def num_tokens_from_messages(messages, step, model="gpt-4"):
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")

    tokens_per_message = 3  # The basics of each message token
    tokens_per_name = 1  # If there is a name, the number of token is increased

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