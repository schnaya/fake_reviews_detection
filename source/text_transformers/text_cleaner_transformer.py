from typing import Optional, List

import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

from source.data.text_cleaner import TextCleaner


class TextCleanerTransformer(BaseEstimator, TransformerMixin):
    """
    A custom scikit-learn transformer for cleaning text using the centralized TextCleaner.
    """

    def __init__(self, text_column: str, methods: Optional[List[str]] = None,
                 stop_words_lang: Optional[str] = 'english', lemmatize: bool = False,
                 stem: bool = False):
        self.text_column = text_column
        self.methods = methods
        self.stop_words_lang = stop_words_lang
        self.lemmatize = lemmatize
        self.stem = stem

        self._text_cleaner = TextCleaner(
            methods=methods,
            stop_words_lang=stop_words_lang,
            lemmatize=lemmatize,
            stem=stem
        )

    def fit(self, X, y=None):
        if self.text_column not in X.columns:
            raise ValueError(f"Column '{self.text_column}' not found in the DataFrame X.")
        return self

    def transform(self, X) -> pd.Series:
        if self.text_column not in X.columns:
            raise ValueError(f"Column '{self.text_column}' not found in the DataFrame X.")
        return self._text_cleaner.clean_series(X[self.text_column])
