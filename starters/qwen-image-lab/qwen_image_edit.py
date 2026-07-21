"""Interactive Qwen Image Edit lab for Zed's Jupyter-backed REPL."""
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false

# %% Environment and imports
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Final, cast

_ = os.environ.setdefault("HF_HOME", "/root/.cache/huggingface")
_ = os.environ.setdefault("HF_XET_HIGH_PERFORMANCE", "1")

import torch
from diffusers.pipelines.qwenimage.pipeline_qwenimage_edit_plus import (
    QwenImageEditPlusPipeline,
)
from diffusers.pipelines.qwenimage.pipeline_output import QwenImagePipelineOutput
from IPython.display import display
from PIL import Image

MODEL_ID = "Qwen/Qwen-Image-Edit-2511"
INPUT_DIR = Path("inputs")
OUTPUT_DIR = Path("outputs")

# Optional Hugging Face repository or local directory containing a compatible
# Qwen Image LoRA. Set LORA_WEIGHT_NAME when the repository has multiple files.
LORA_REPO = os.environ.get("QWEN_LORA_REPO", "")
LORA_WEIGHT_NAME = os.environ.get("QWEN_LORA_WEIGHT_NAME") or None
LORA_SCALE = float(os.environ.get("QWEN_LORA_SCALE", "1.0"))
LORA_ADAPTER_NAME: Final = "lab"

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
_ = pipeline.to("cuda")
pipeline.set_progress_bar_config(disable=None)
print(f"Loaded {MODEL_ID} on {torch.cuda.get_device_name(0)}")

# %% Optionally load a LoRA
if LORA_REPO:
    if LORA_WEIGHT_NAME:
        pipeline.load_lora_weights(
            LORA_REPO,
            adapter_name=LORA_ADAPTER_NAME,
            weight_name=LORA_WEIGHT_NAME,
        )
    else:
        pipeline.load_lora_weights(
            LORA_REPO,
            adapter_name=LORA_ADAPTER_NAME,
        )
    pipeline.set_adapters(LORA_ADAPTER_NAME, adapter_weights=LORA_SCALE)
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
    _ = display(image)

# %% Describe the edit
PROMPT = (
    "Preserve the subject and composition of the reference image while "
    "transforming it into a cinematic editorial photograph with natural light."
)

# %% Generate and display the result
generator = torch.Generator(device="cuda").manual_seed(SEED)
with torch.inference_mode():
    pipeline_output = cast(
        QwenImagePipelineOutput,
        pipeline(
            image=reference_images,
            prompt=PROMPT,
            generator=generator,
            true_cfg_scale=TRUE_CFG_SCALE,
            negative_prompt=NEGATIVE_PROMPT,
            num_inference_steps=NUM_INFERENCE_STEPS,
            guidance_scale=GUIDANCE_SCALE,
            num_images_per_prompt=1,
            return_dict=True,
        ),
    )
images = pipeline_output.images
if not isinstance(images, list):
    raise TypeError("Expected the pipeline to return a list of PIL images")
result: Image.Image = images[0]

timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
output_path = OUTPUT_DIR / f"qwen-edit-{timestamp}.png"
_ = result.save(output_path)
_ = display(result)
print(f"Saved {output_path.resolve()}")
