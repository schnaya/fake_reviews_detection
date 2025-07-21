import json
import logging
import os
import pickle

import joblib
import pandas as pd

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MLModel:
    def __init__(self, model_path: str = None):
        """
        model_path: путь к .pkl файлу с полными данными модели
        """
        if model_path is None:
            model_dir = os.getenv("MODEL_DIR", "/app/model")
            model_path = os.path.join(model_dir, "model_artifacts.pkl")

        logger.info(f"Загрузка артефактов из {model_path}")

        try:
            artifacts = joblib.load(model_path)

            self.pipeline = artifacts['full_pipeline']
            self.label_mapping = artifacts.get('label_mapping', {})
            self.reverse_label_mapping = {v: k for k, v in self.label_mapping.items()}

            logger.info("Артефакты успешно загружены.")
        except Exception as e:
            logger.error(f"Ошибка загрузки артефактов: {e}")
            raise

    def predict_label(self, text: str) -> int:
        """
        Предсказывает бинарную метку для входного текста: 0 или 1
        """
        logger.debug(f"Входной текст: {text[:100]}")

        try:
            df = pd.DataFrame({'text_': [text]})

            prediction = self.pipeline.predict(df)[0]

            logger.debug(f"Предсказанная метка: {prediction}")
            return int(prediction)

        except Exception as e:
            logger.error(f"Ошибка предсказания: {e}")
            raise

    def predict_proba(self, text: str) -> dict:
        """
        Возвращает вероятности для каждого класса
        """
        logger.debug(f"Входной текст для predict_proba: {text[:100]}...")

        try:
            df = pd.DataFrame({'text_': [text]})
            X_vectorized = self.pipeline.transform(df)

            # Получаем вероятности
            probabilities = self.model.predict_proba(X_vectorized)[0]

            # Формируем результат
            result = {}
            for idx, prob in enumerate(probabilities):
                label_name = self.reverse_label_mapping.get(idx, f"class_{idx}")
                result[label_name] = float(prob)

            logger.debug(f"Вероятности: {result}")
            return result

        except Exception as e:
            logger.error(f"Ошибка получения вероятностей: {e}")
            raise

    def predict_detailed(self, text: str) -> dict:
        """
        Возвращает подробную информацию о предсказании
        """
        try:
            label = self.predict_label(text)
            probabilities = self.predict_proba(text)

            label_name = self.reverse_label_mapping.get(label, f"class_{label}")
            confidence = max(probabilities.values())

            return {
                'predicted_label': label,
                'predicted_class': label_name,
                'confidence': confidence,
                'probabilities': probabilities
            }

        except Exception as e:
            logger.error(f"Ошибка подробного предсказания: {e}")
            raise