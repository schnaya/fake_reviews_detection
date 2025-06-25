class DataExplorer:
    """
    Class for comprehensive data exploration and analysis.

    Provides methods to inspect data structure, distributions, missing values,
    and perform basic analysis relevant to review data.
    """
    def __init__(self, df):
        self.__df = df

    def columns_info(self):
        return self.__df.columns.values

    def label_distribution(self, label_name: str = "label"):
        return self.__df[label_name].value_counts()
