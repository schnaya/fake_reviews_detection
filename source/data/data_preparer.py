from typing import Any, List, Optional, Union

import pandas as pd

from source.data import DataLoader


class DataPreparer:
    """
    Class for cleaning, preprocessing, and preparing data for machine learning models.

    Includes methods for handling missing values, cleaning text, feature engineering,
    splitting data, and handling class imbalance.
    Operates on DataFrames passed to its methods, returning transformed DataFrames/arrays.
    """
    def __init__(self, df: pd.DataFrame):
        self.__df = df.copy()

    @property
    def df(self):
        return self.__df

    def __drop_missing_values(self, cols_to_process: Optional[List[str]] = None) -> None:
        self.__df.dropna(subset=cols_to_process, inplace=True)

    def __fill_missing_values(self, cols_to_process: Optional[List[str]] = None, fill_value: Any = None) -> None:
        self.__df[cols_to_process] = self.__df[cols_to_process].fillna(fill_value)

    def handle_missing_values(self,
                              strategy: str = 'drop',
                              columns: Optional[List[str]] = None,
                              fill_value: Any = None) -> None:

        cols_to_process = columns if columns is not None else self.__df.columns[self.__df.isnull().any()].tolist()
        if strategy == 'drop':
            self.__drop_missing_values(cols_to_process)
        elif strategy == 'fill':
            if fill_value:
                self.__fill_missing_values(cols_to_process, fill_value)
            else:
                raise KeyError(f'Missing value for {strategy}. Please provide a value for {cols_to_process}.')

    def drop_duplicates(self, subset: Optional[List[str]] = None) -> None:
        self.__df.drop_duplicates(subset=subset, keep='first', inplace=True)

    def clean_text_column(self, df: pd.DataFrame, text_column: str, methods: Optional[List[str]] = None,
                          stop_words_lang: Optional[str] = 'english', lemmatize: bool = False,
                          stem: bool = False) -> None:
        """
        Cleans a specified text column using a list of methods.

        Available methods: 'lower', 'remove_punctuation', 'remove_numbers',
        'remove_whitespace', 'remove_stopwords'.

        Requires nltk stopwords and wordnet (for lemmatization) if those methods are used.
        """

        pass

    def create_text_features(self, df: pd.DataFrame, text_column: str, method: str = 'tfidf', **kwargs) -> Union[pd.DataFrame, pd.DataFrame]:
        pass

    def prepare_df(self):
        self.handle_missing_values()
        self.drop_duplicates()
        self.clean_data()


if __name__ == '__main__':
    loader = DataLoader()
    loader.data_path = "../../data"
    yelp_set = {"link": "thedevastator/yelp-reviews-sentiment-dataset", "filename": "train.csv"}
    yelp = loader.load_from_kaggle(**yelp_set)
    yelp_preparer = DataPreparer(yelp)
    yelp_preparer.prepare_df()
    res = yelp_preparer.df
