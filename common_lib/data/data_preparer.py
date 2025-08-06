import re
import string
from typing import Optional, List, Any, Union, Dict
import pandas as pd
from pandas import DataFrame
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer

from common_lib.classes.data_processor import DataProcessor
from common_lib.data import DataLoader

from common_lib.data.text_cleaner import TextCleaner


class DataPreparer(DataProcessor):
    """
    Class for cleaning, preprocessing, and preparing data for machine learning models.

    Includes methods for handling missing values, cleaning text, feature engineering,
    splitting data, and handling class imbalance.
    Operates on DataFrames passed to its methods, returning transformed DataFrames/arrays.
    """
    def __init__(self, df: pd.DataFrame):
        super().__init__(df)
        self.__label_mapping: Optional[Dict[Any, int]] = None
        self.__original_df = df.copy()
        self._vectorizer = CountVectorizer()
        self.__text_cleaner = TextCleaner()

    @property
    def vectorizer(self):
        return self._vectorizer

    @vectorizer.setter
    def vectorizer(self, vectorizer):
        self._vectorizer = vectorizer

    def reset(self) -> 'DataPreparer':
        self._df = self.__original_df.copy()
        return self

    def __drop_missing_values(self, cols_to_process: Optional[List[str]] = None) -> None:
        if cols_to_process:
            self._df.dropna(subset=cols_to_process, inplace=True)
        else:
            self._df.dropna(inplace=True)

    def __fill_missing_values(self, cols_to_process: Optional[List[str]] = None, fill_value: Any = None) -> None:
        if cols_to_process and fill_value is not None:
            self._df[cols_to_process] = self._df[cols_to_process].fillna(fill_value)

    def handle_missing_values(self,
                              strategy: str = 'drop',
                              columns: Optional[List[str]] = None,
                              fill_value: Any = None) -> 'DataPreparer':

        cols_with_missing = self._df.columns[self._df.isnull().any()].tolist()
        cols_to_process = columns if columns is not None else cols_with_missing
        if columns is not None:
            for col in columns:
                self._validate_column_exists(col)
        if strategy == 'drop':
            self.__drop_missing_values(cols_to_process)
            return self
        elif strategy == 'fill':
            if fill_value:
                self.__fill_missing_values(cols_to_process, fill_value)
                return self
            else:
                raise ValueError(f'Missing value for {strategy}. Please provide a value for {cols_to_process}.')
        else:
            raise ValueError(f'Strategy {strategy} is not supported.')

    def drop_duplicates(self, subset: Optional[List[str]] = None) -> 'DataPreparer':
        if subset:
            for col in subset:
                self._validate_column_exists(col)

        self._df.drop_duplicates(subset=subset, keep='first', inplace=True)
        return self

    def clean_text_column(self, text_column: str, methods: Optional[List[str]] = None,
                          stop_words_lang: Optional[str] = 'english', lemmatize: bool = False,
                          stem: bool = False) -> 'DataPreparer':
        self._validate_column_exists(text_column)
        text_cleaner = TextCleaner(
            methods=methods,
            stop_words_lang=stop_words_lang,
            lemmatize=lemmatize,
            stem=stem
        )
        self._df[text_column] = text_cleaner.clean_series(self._df[text_column])
        return self

    @staticmethod
    def _create_vectorizer(method: str, **kwargs):
        """Create vectorizer using the same logic as create_text_features method."""
        if method == 'tfidf':
            return TfidfVectorizer(**kwargs)
        elif method == 'count':
            return CountVectorizer(**kwargs)
        else:
            raise ValueError(f"Vectorization method '{method}' is not supported. Choose from 'tfidf', 'count'.")

    def create_text_features(self,
                             text_column: str,
                             method: str = 'tfidf',
                             update_state: bool = True,
                             **kwargs) -> Union[pd.DataFrame, pd.DataFrame]:
        self._validate_column_exists(text_column)
        texts = self._df[text_column].fillna('').astype(str)

        vectorizer = self._create_vectorizer(method, **kwargs)
        feature_matrix = vectorizer.fit_transform(texts)
        if update_state:
            self.vectorizer = vectorizer
        return feature_matrix

    def encode_labels(self, label_column: str) -> 'DataPreparer':
        self._validate_column_exists(label_column)

        if pd.api.types.is_numeric_dtype(self._df[label_column]):
            print(f"Label column '{label_column}' is already numeric. No encoding needed.")
            return self

        unique_labels = self._df[label_column].astype('category').cat.categories
        self.__label_mapping = {label: i for i, label in enumerate(unique_labels)}

        print(f"Encoding labels in '{label_column}'. Mapping created: {self.__label_mapping}")
        self._df[label_column] = self._df[label_column].map(self.__label_mapping)
        self._df[label_column] = self._df[label_column].astype(int)

        return self

    def get_label_mapping(self) -> Optional[Dict[Any, int]]:
        return self.__label_mapping
    
    def get_features_and_labels(self,
                                text_column: str,
                                label_column: str,
                                vectorizer_method: str = 'tfidf',
                                **vectorizer_kwargs: Any) -> tuple[DataFrame, Any]:
        self._validate_column_exists(text_column)
        self._validate_column_exists(label_column)

        print(f"Vectorizing text from '{text_column}' using '{vectorizer_method}'...")
        feature_matrix = self.create_text_features(
            text_column=text_column,
            method=vectorizer_method,
            **vectorizer_kwargs
        )
        print(f"Feature matrix shape: {feature_matrix.shape}")

        labels = self._df[label_column]
        print(f"Extracted labels from '{label_column}'. Shape: {labels.shape}")

        return feature_matrix, labels

    def prepare_df(self,
                   handle_missing_strategy: str = 'drop',
                   handle_missing_columns: Optional[List[str]] = None,
                   handle_missing_fill_value: Any = None,
                   drop_duplicates_subset: Optional[List[str]] = None,
                   encode_label_col: Optional[str] = None,
                   clean_text_col: Optional[str] = None,
                   clean_text_methods: Optional[List[str]] = None,
                   clean_text_stopwords_lang: Optional[str] = 'english',
                   clean_text_lemmatize: bool = False,
                   clean_text_stem: bool = False
                   ) -> 'DataPreparer':
        print("Starting data preparation...")
        print(f"Handling missing values using strategy: '{handle_missing_strategy}'...")
        self.handle_missing_values(
            strategy=handle_missing_strategy,
            columns=handle_missing_columns,
            fill_value=handle_missing_fill_value
        )
        print(f"DataFrame shape after handling missing values: {self._df.shape}")
        if drop_duplicates_subset is not None:
            print("Dropping duplicates...")
            initial_rows = len(self._df)
            self.drop_duplicates(subset=drop_duplicates_subset)
            rows_after_duplicates = len(self._df)
            print(f"Dropped {initial_rows - rows_after_duplicates} duplicate rows.")
            print(f"DataFrame shape after dropping duplicates: {self._df.shape}")

        if encode_label_col:
            self.encode_labels(label_column=encode_label_col)

        if clean_text_col:
            print(f"Cleaning text column: '{clean_text_col}'...")
            self.clean_text_column(
                text_column=clean_text_col,
                methods=clean_text_methods,
                stop_words_lang=clean_text_stopwords_lang,
                lemmatize=clean_text_lemmatize,
                stem=clean_text_stem
            )
            print(f"Text cleaning applied to '{clean_text_col}'.")
        print("Data preparation complete.")
        return self




if __name__ == '__main__':
    loader = DataLoader()
    loader.data_path = "../../data"
    yelp_set = {"link": "thedevastator/yelp-reviews-sentiment-dataset", "filename": "train.csv"}
    yelp = loader.load_from_kaggle(**yelp_set)
    yelp_preparer = DataPreparer(yelp)
    processed_preparer = yelp_preparer.prepare_df(
        handle_missing_strategy='fill',
        handle_missing_columns=['text', 'label'],
        handle_missing_fill_value={'text': '', 'label': -1},
        drop_duplicates_subset=None,
        clean_text_col='text',
        clean_text_methods=['lower', 'remove_punctuation', 'remove_numbers', 'remove_whitespace', 'remove_stopwords'],
        clean_text_lemmatize=True
    )
    processed_df = processed_preparer.get_result()
