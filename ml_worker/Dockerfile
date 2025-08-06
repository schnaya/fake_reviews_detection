FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONPATH="${PYTHONPATH}:/app" \
    MODEL_DIR=/app/model

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY ml_worker/requirements.txt ml_worker_requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r ml_worker_requirements.txt
RUN mkdir -p ${MODEL_DIR}
COPY trained_models/model_artifacts.pkl ${MODEL_DIR}/model_artifacts.pkl


COPY common_lib /app/common_lib
COPY ./ml_worker /app/ml_worker

WORKDIR /app/ml_worker
CMD ["python", "main.py"]