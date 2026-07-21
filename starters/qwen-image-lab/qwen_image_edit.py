"""Interactive Qwen Image Edit lab for Zed's Jupyter-backed REPL."""

# %% Environment and imports
import os
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("HF_HOME", "/root/.cache/huggingface")
os.environ.setdefault("HF_XET_HIGH_PERFORMANCE", "1")

import torch
from diffusers import QwenImageEditPlusPipeline
from IPython.display import display
from PIL import Image

MODEL_ID = "Qwen/Qwen-Image-Edit-2511"
INPUT_DIR = Path("inputs")
OUTPUT_DIR = Path("outputs")

# Optional Hugging Face repository or local directory containing a compatible
# Qwen Image LoRA. Set LORA_WEIGHT_NAME when the repository has multiple files.
LORA_REPO = ""
LORA_WEIGHT_NAME = None
LORA_SCALE = 1.0

SEED = 0
NUM_INFERENCE_STEPS = 40
TRUE_CFG_SCALE = 4.0
GUIDANCE_SCALE = 1.0
NEGATIVE_PROMPT = " "

INPUT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# %% Load the base pipeline once
pipeline = QwenImageEditPlusPipeline.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.bfloat16,
)
pipeline.to("cuda")
pipeline.set_progress_bar_config(disable=None)
print(f"Loaded {MODEL_ID} on {torch.cuda.get_device_name(0)}")

# %% Optionally load a LoRA
if LORA_REPO:
    lora_kwargs = {"adapter_name": "lab"}
    if LORA_WEIGHT_NAME:
        lora_kwargs["weight_name"] = LORA_WEIGHT_NAME
    pipeline.load_lora_weights(LORA_REPO, **lora_kwargs)
    pipeline.set_adapters("lab", adapter_weights=LORA_SCALE)
    print(f"Loaded LoRA {LORA_REPO} at scale {LORA_SCALE}")
else:
    print("Using the base model without an additional LoRA")

# %% Load and inspect reference images
image_paths = sorted(
    path
    for path in INPUT_DIR.iterdir()
    if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
)
if not image_paths:
    raise FileNotFoundError(
        "Add at least one .jpg, .jpeg, .png, or .webp reference image to inputs/"
    )

reference_images = [Image.open(path).convert("RGB") for path in image_paths]
print("Reference images:", ", ".join(path.name for path in image_paths))
for image in reference_images:
    display(image)

# %% Describe the edit
PROMPT = (
    "Preserve the subject and composition of the reference image while "
    "transforming it into a cinematic editorial photograph with natural light."
)

# %% Generate and display the result
generator = torch.Generator(device="cuda").manual_seed(SEED)
with torch.inference_mode():
    result = pipeline(
        image=reference_images,
        prompt=PROMPT,
        generator=generator,
        true_cfg_scale=TRUE_CFG_SCALE,
        negative_prompt=NEGATIVE_PROMPT,
        num_inference_steps=NUM_INFERENCE_STEPS,
        guidance_scale=GUIDANCE_SCALE,
        num_images_per_prompt=1,
    ).images[0]

timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
output_path = OUTPUT_DIR / f"qwen-edit-{timestamp}.png"
result.save(output_path)
display(result)
print(f"Saved {output_path.resolve()}")
