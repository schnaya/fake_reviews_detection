import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


class TextStatsTransformer(BaseEstimator, TransformerMixin):
    """
    A custom scikit-learn transformer to extract simple text statistics
    like text length and word count from a specified text column.
    """
    def __init__(self, text_column: str):
        self.text_column = text_column

    def fit(self, X, y=None):
        if not isinstance(X, pd.DataFrame) or self.text_column not in X.columns:
             raise ValueError(f"Input must be a DataFrame with column '{self.text_column}'.")
        return self

    def transform(self, X) -> pd.DataFrame:
        if not isinstance(X, pd.DataFrame) or self.text_column not in X.columns:
            raise ValueError(f"Input must be a DataFrame with column '{self.text_column}'.")

        text_series = X[self.text_column].fillna('').astype(str)
        text_length = text_series.apply(len)
        word_count = text_series.apply(lambda x: len(x.split()))

        stats_df = pd.DataFrame({
            f'{self.text_column}_length': text_length,
            f'{self.text_column}_word_count': word_count,
        }, index=X.index)

        return stats_df
