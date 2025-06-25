import logging
import os
import shutil
import pandas as pd
import kagglehub


class DataLoader:
    """
    Class for loading data from open sources
    """

    def __init__(self):
        self.__data_path = "../data"

    @property
    def data_path(self):
        return self.__data_path

    @data_path.setter
    def data_path(self, value):
        self.__data_path = value

    def __download_kaggle_dataset(self, link):
        try:
            dataset_path = kagglehub.dataset_download(link, force_download=True)
            os.makedirs(self.__data_path, exist_ok=True)
            for filename in os.listdir(dataset_path):
                src = os.path.join(dataset_path, filename)
                dst = os.path.join(self.__data_path, filename)
                shutil.copy2(src, dst)
        except Exception as e:
            logging.error(e)

    def __load_data(self, filename) -> pd.DataFrame:
        return pd.read_csv(os.path.join(self.__data_path, filename))

    def load_from_kaggle(self, link, filename) -> pd.DataFrame:
        self.__download_kaggle_dataset(link)
        return self.__load_data(filename)

