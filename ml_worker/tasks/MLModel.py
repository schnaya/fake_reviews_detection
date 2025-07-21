import json
import logging
import os
import pickle
import random
from pathlib import Path
from typing import List

import joblib
import pandas as pd

from source.data import PreprocessingPipelineBuilder

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MLModel:
    def __init__(self, model_path: str, pipeline: PreprocessingPipelineBuilder):
        """
        model_path: путь к .pkl файлу с моделью
        pipeline: уже собранный pipeline для очистки текста
        """
        model_dir = os.getenv("MODEL_DIR", "/app/model")
        model_path = os.path.join(model_dir, "model.pkl")
        self.pipeline = pipeline

        logger.info(f"Загрузка модели из {model_path}")
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)

    def predict_label(self, text: str) -> int:
        """
        Предсказывает бинарную метку для входного текста: 0 или 1
        """
        logger.debug(f"Входной текст: {text}")

        # Оборачиваем в DataFrame (если pipeline требует таблицу)
        df = pd.DataFrame({'text': [text]})
        X_vectorized = self.pipeline.transform(df)

        prediction = self.model.predict(X_vectorized)[0]
        logger.debug(f"Предсказанная метка: {prediction}")
        return int(prediction)
