# Qwen Image Lab

This workspace is ready for interactive editing with
[`Qwen/Qwen-Image-Edit-2511`](https://huggingface.co/Qwen/Qwen-Image-Edit-2511).

1. Put one or more reference images in `inputs/`.
2. Open `qwen_image_edit.py` in Zed.
3. Run **REPL: Refresh Kernelspecs** from Zed's command palette.
4. Select the **Qwen Image Lab** kernel.
5. Run each `# %%` cell with `Ctrl-Shift-Enter`.

The first model load downloads roughly 58 GB and can take a while without a
warm Hugging Face cache. Later cells reuse the loaded pipeline.

## Optional LoRA

Set the repository or local path before running the pipeline-loading cell:

```python
LORA_REPO = "owner/qwen-image-edit-lora"
LORA_WEIGHT_NAME = None  # Set this when the repository has multiple weights.
LORA_SCALE = 1.0
```

Leave `LORA_REPO` empty to use the base model. The starter calls Diffusers'
native Qwen Image LoRA loader and lets you control its adapter weight.

Generated images are written to `outputs/`, which is intentionally ignored by
Git along with local reference images.
