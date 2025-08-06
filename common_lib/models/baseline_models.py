from typing import Dict, Any, Tuple, List, Union

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC


class BaselineModelTrainer:

    def __init__(self):
        self.model: Any = None
        self.model_name: str = ""
        self._models: Dict[str, Any] = {
            'logistic_regression': LogisticRegression,
            'naive_bayes': MultinomialNB,
            'linear_svc': LinearSVC
        }

    def get_supported_models(self) -> List[str]:
        return list(self._models.keys())

    def _get_default_params(self, model_name: str) -> Dict[str, Any]:
        if model_name == 'logistic_regression':
            return {'class_weight': 'balanced', 'random_state': 42, 'max_iter': 1000, 'solver': 'liblinear'}
        if model_name == 'linear_svc':
            return {'class_weight': 'balanced', 'random_state': 42, 'max_iter': 2000, 'dual': False}
        if model_name == 'naive_bayes':
            return {'alpha': 1.0}
        return {}

    def train_and_predict(self,
                          model_name: str,
                          X_train: Union[np.ndarray, csr_matrix],
                          y_train: Union[np.ndarray, pd.Series],
                          X_test: Union[np.ndarray, csr_matrix],
                          **kwargs: Any) -> Tuple[np.ndarray, Any]:

        if model_name not in self._models:
            raise ValueError(f"Model '{model_name}' is not supported. "
                             f"Supported models are: {self.get_supported_models()}")

        self.model_name = model_name
        print(f"--- Training {self.model_name} ---")
        model_params = self._get_default_params(self.model_name)
        model_params.update(kwargs)
        print(f"Using model parameters: {model_params}")
        self.model = self._models[self.model_name](**model_params)
        self.model.fit(X_train, y_train)
        print("Training complete.")
        print("Making predictions on the test set...")
        y_pred = self.model.predict(X_test)

        return y_pred, self.model

