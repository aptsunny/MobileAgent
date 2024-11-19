# Load model directly
from transformers import AutoProcessor, AutoModelForImageTextToText

# processor = AutoProcessor.from_pretrained("OS-Copilot/OS-Atlas-Base-7B")
# model = AutoModelForImageTextToText.from_pretrained("OS-Copilot/OS-Atlas-Base-7B")

processor = AutoProcessor.from_pretrained("OS-Copilot/OS-Atlas-Base-4B")
model = AutoModelForImageTextToText.from_pretrained("OS-Copilot/OS-Atlas-Base-4B")