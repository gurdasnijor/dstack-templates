ARG BASE_IMAGE=diffusers/diffusers-pytorch-cuda@sha256:d0051164c734080c19279a1f57f9b5601641ed84c4b925e1a360d2f25adc6c5b
FROM ${BASE_IMAGE}

COPY images/qwen-image-lab/requirements.lock /tmp/qwen-image-lab-requirements.txt

# Keep the editor/runtime layer separate from model weights. The latter belong
# in Hugging Face's cache so a dstack network volume can preserve them without
# forcing a multi-gigabyte image rebuild for every checkpoint change.
RUN /opt/venv/bin/python -m pip install --no-cache-dir \
      -r /tmp/qwen-image-lab-requirements.txt \
    && /opt/venv/bin/python -m ipykernel install \
      --prefix=/usr/local \
      --name=qwen-image-lab \
      --display-name="Qwen Image Lab" \
    && rm /tmp/qwen-image-lab-requirements.txt

COPY starters/qwen-image-lab/ /opt/zinnia/starters/qwen-image-lab/

ENV PATH="/opt/venv/bin:${PATH}" \
    HF_ENABLE_PARALLEL_LOADING=1 \
    HF_XET_HIGH_PERFORMANCE=1

WORKDIR /dstack/run
