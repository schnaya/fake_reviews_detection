import re
import string
from typing import Optional, List, Any, Union

import pandas as pd
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer, PorterStemmer
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from source.data import DataLoader, DataProcessor

import nltk
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')
try:
    nltk.data.find('corpora/omw-1.4')
except LookupError:
    nltk.download('omw-1.4')


class DataPreparer(DataProcessor):
    """
    Class for cleaning, preprocessing, and preparing data for machine learning models.

    Includes methods for handling missing values, cleaning text, feature engineering,
    splitting data, and handling class imbalance.
    Operates on DataFrames passed to its methods, returning transformed DataFrames/arrays.
    """
    def __init__(self, df: pd.DataFrame):
        super().__init__(df)
        self.__original_df = df.copy()
        self.__lemmatizer = WordNetLemmatizer()
        self.__stemmer = PorterStemmer()
        self.__stop_words = set(stopwords.words('english'))

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

    def __clean_text(self, text: str, methods: List[str], lemmatize: bool, stem: bool) -> str:
        if not isinstance(text, str):
            return ""

        cleaned_text = text

        if 'lower' in methods:
            cleaned_text = cleaned_text.lower()

        if 'remove_punctuation' in methods:
            cleaned_text = cleaned_text.translate(str.maketrans('', '', string.punctuation))

        if 'remove_numbers' in methods:
            cleaned_text = re.sub(r'\d+', '', cleaned_text)

        if 'remove_whitespace' in methods:
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        words = cleaned_text.split()

        if 'remove_stopwords' in methods:
            words = [word for word in words if word not in self.__stop_words]
        if lemmatize:
            words = [self.__lemmatizer.lemmatize(word) for word in words]
        if stem:
            words = [self.__stemmer.stem(word) for word in words]

        return ' '.join(words)

    def clean_text_column(self, text_column: str, methods: Optional[List[str]] = None,
                          stop_words_lang: Optional[str] = 'english', lemmatize: bool = False,
                          stem: bool = False) -> 'DataPreparer':
        self._validate_column_exists(text_column)
        if stop_words_lang and stop_words_lang != 'english':
            try:
                self.__stop_words = set(stopwords.words(stop_words_lang))
            except OSError:
                raise ValueError(
                    f"Stop words language '{stop_words_lang}' not supported by NLTK or data not downloaded.")
        methods_list = methods if methods is not None else []
        self._df[text_column] = self._df[text_column].apply(
            lambda x: self.__clean_text(x, methods_list, lemmatize, stem)
        )
        return self

    def create_text_features(self,
                             text_column: str,
                             method: str = 'tfidf',
                             **kwargs) -> Union[pd.DataFrame, pd.DataFrame]:
        self._validate_column_exists(text_column)
        texts = self._df[text_column].fillna('').astype(str)

        if method == 'tfidf':
            vectorizer = TfidfVectorizer(**kwargs)
        elif method == 'count':
            vectorizer = CountVectorizer(**kwargs)
        else:
            raise ValueError(f"Vectorization method '{method}' is not supported. Choose from 'tfidf', 'count'.")
        feature_matrix = vectorizer.fit_transform(texts)
        return feature_matrix

    def prepare_df(self,
                   handle_missing_strategy: str = 'drop',
                   handle_missing_columns: Optional[List[str]] = None,
                   handle_missing_fill_value: Any = None,
                   drop_duplicates_subset: Optional[List[str]] = None,
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
        print("Dropping duplicates...")
        initial_rows = len(self._df)
        self.drop_duplicates(subset=drop_duplicates_subset)
        rows_after_duplicates = len(self._df)
        print(f"Dropped {initial_rows - rows_after_duplicates} duplicate rows.")
        print(f"DataFrame shape after dropping duplicates: {self._df.shape}")
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

    def get_result(self) -> pd.DataFrame:
        return self._df.copy()


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
