import pandas as pd


class DataProcessor:
    def __init__(self, df: pd.DataFrame):
        if df is None or df.empty:
            raise ValueError("DataFrame cannot be None or empty")
        self._df = df.copy()

    def _validate_column_exists(self, column_name: str) -> None:
        if column_name not in self._df.columns:
            raise ValueError(f"Column '{column_name}' not found in dataframe")