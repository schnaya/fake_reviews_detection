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
        self.__data_path = os.path.join("../", "data")
        os.makedirs(self.__data_path, exist_ok=True)

    @property
    def data_path(self):
        return self.__data_path

    @data_path.setter
    def data_path(self, value):
        self.__data_path = value

    @staticmethod
    def __download_kaggle_dataset(link, res_dir):
        try:
            dataset_path = kagglehub.dataset_download(link, force_download=True)
            for filename in os.listdir(dataset_path):
                src = os.path.join(dataset_path, filename)
                dst = os.path.join(res_dir, filename)
                shutil.copy2(src, dst)
        except Exception as e:
            logging.error(e)

    @staticmethod
    def __download_kaggle_file(link, filename, filepath):
        try:
            dataset_path = kagglehub.dataset_download(link, path=filename, force_download=True)
            if not os.path.isfile(dataset_path):
                logging.error(f"File '{filename}' not found in '{dataset_path}'."
                              f"Directory files: {os.listdir(dataset_path)}")
                return
            shutil.copy2(dataset_path, filepath)
        except Exception as e:
            logging.error(e)

    @staticmethod
    def __load_data(filepath) -> pd.DataFrame:
        return pd.read_csv(filepath, quotechar='"', encoding='utf-8', encoding_errors='replace')

    def __prepare_paths_and_dirs(self, link, filename) -> tuple[str, str]:
        res_dir = os.path.join(self.__data_path, *link.split('/'))
        os.makedirs(res_dir, exist_ok=True)
        filepath = os.path.join(res_dir, filename)
        return res_dir, filepath

    def load_from_kaggle(self, link, filename) -> pd.DataFrame:
        res_dir, filepath = self.__prepare_paths_and_dirs(link, filename)
        print(filepath)
        if not os.path.isfile(filepath):
            self.__download_kaggle_dataset(link, res_dir)
        #    self.__download_kaggle_file(link, filename, filepath)
        return self.__load_data(filepath)


if __name__ == "__main__":
    data_loader = DataLoader()
    data_loader.data_path = "../../data"
    mexwell_set = {"link": "mexwell/fake-reviews-dataset", "filename": "fake reviews dataset.csv"}
    data_loader.load_from_kaggle(**mexwell_set)
