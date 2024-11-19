from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info

# Default: Load the model on the available device(s)
model = Qwen2VLForConditionalGeneration.from_pretrained(
    "OS-Copilot/OS-Atlas-Base-7B", torch_dtype="auto", device_map="auto"
)
processor = AutoProcessor.from_pretrained("OS-Copilot/OS-Atlas-Base-7B")

messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "image",
                "image": "./exmaples/images/web_6f93090a-81f6-489e-bb35-1a2838b18c01.png",
            },
            {"type": "text", "text": "In this UI screenshot, what is the position of the element corresponding to the command \"switch language of current page\" (with bbox)?"},
        ],
    }
]


# Preparation for inference
text = processor.apply_chat_template(
    messages, tokenize=False, add_generation_prompt=True
)
image_inputs, video_inputs = process_vision_info(messages)
inputs = processor(
    text=[text],
    images=image_inputs,
    videos=video_inputs,
    padding=True,
    return_tensors="pt",
)
inputs = inputs.to("cuda")

# Inference: Generation of the output
generated_ids = model.generate(**inputs, max_new_tokens=128)

generated_ids_trimmed = [
    out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
]

output_text = processor.batch_decode(
    generated_ids_trimmed, skip_special_tokens=False, clean_up_tokenization_spaces=False
)
print(output_text)
# <|object_ref_start|>language switch<|object_ref_end|><|box_start|>(576,12),(592,42)<|box_end|><|im_end|>