from typing import Dict, List, Any

import numpy as np
import pandas as pd

from source.classes.data_processor import DataProcessor
from source.data import DataLoader



class DataExplorer(DataProcessor):
    """
    Class for comprehensive data exploration and analysis.

    Provides methods to inspect data structure, distributions, missing values,
    and perform basic analysis relevant to review data.
    """
    def __init__(self, df: pd.DataFrame):
        super().__init__(df)

    def _validate_numeric_column(self, column_name: str) -> None:
        self._validate_column_exists(column_name)
        if not pd.api.types.is_numeric_dtype(self._df[column_name]):
            raise ValueError(f"Column '{column_name}' is not numeric")

    def columns_info(self) -> np.ndarray:
        return self._df.columns.values

    def label_distribution(self, label_name: str = "label") -> pd.Series:
        self._validate_column_exists(label_name)
        return self._df[label_name].value_counts()

    def show_head(self, n: int = 10) -> pd.DataFrame:
        return self._df.head(n)

    def data_shape(self) -> tuple:
        return self._df.shape

    def data_types(self) -> pd.Series:
        return self._df.dtypes

    def missing_values(self) -> pd.Series:
        return self._df.isnull().sum()

    def missing_values_percentage(self) -> pd.Series:
        return (self._df.isnull().sum() / len(self._df) * 100).round(2)

    def text_length_stats(self, text_column="text_") -> Dict[str, float]:
        self._validate_column_exists(text_column)
        lengths = self._df[text_column].dropna().apply(len)
        return {
            "min": lengths.min(),
            "max": lengths.max(),
            "mean": round(lengths.mean(), 2),
            "median": lengths.median(),
            "std": round(lengths.std(), 2)
        }

    def most_common_words(self, text_column="text_", n=10) -> List[tuple]:
        self._validate_column_exists(text_column)
        words = dict()
        for word_list in self._df[text_column].dropna().str.split():
            for word in word_list:
                word = word.lower().strip('.,!?;:"()[]{}')
                if word in words:
                    words[word] += 1
                else:
                    words[word] = 1
        return sorted(words.items(), key=lambda x: x[1], reverse=True)[:n]

    def rating_distribution(self, rating_col='rating') -> pd.Series:
        return self.label_distribution(rating_col).sort_index()

    def rating_distribution_by_labels(self,
                                      rating_column: str = 'rating',
                                      label_column: str = 'label') -> tuple[pd.DataFrame, pd.DataFrame]:
        self._validate_column_exists(rating_column)
        self._validate_column_exists(label_column)
        crosstab_absolute = pd.crosstab(
            self._df[rating_column],
            self._df[label_column],
            margins=True,
            margins_name='Всего'
        )
        crosstab_percentage = crosstab_absolute.div(crosstab_absolute.loc['Всего'], axis=1) * 100
        crosstab_percentage = crosstab_percentage.drop('Всего', axis=0)
        crosstab_percentage = crosstab_percentage.round(2)
        return crosstab_absolute, crosstab_percentage

    def rating_label_summary(self,
                             rating_column: str = 'rating',
                             label_column: str = 'label') -> Dict[str, Any]:
        self._validate_column_exists(rating_column)
        self._validate_column_exists(label_column)
        absolute, percentage = self.rating_distribution_by_labels(rating_column, label_column)
        return {
            'absolute_counts': absolute,
            'percentage_distribution': percentage
        }

    def generate_report(self,
                        text_column: str = "text_",
                        label_column: str = "label",
                        rating_column: str = None) -> Dict[str, Any]:
        report = {
            "basic_info": {
                "shape": self.data_shape(),
                "columns": self.columns_info().tolist(),
                "data_types": self.data_types().to_dict()
            },
            "missing_values": {
                "count": self.missing_values().to_dict(),
                "percentage": self.missing_values_percentage().to_dict()
            },
            "text_analysis": {
                "length_stats": self.text_length_stats(text_column),
                "most_common_words": self.most_common_words(text_column, 15)
            },
            "label_analysis": {
                "distribution": self.label_distribution(label_column).to_dict()
            }
        }
        if rating_column:
            report["rating_analysis"] = {
                "distribution": self.rating_distribution(rating_column).to_dict(),
                "by_labels": self.rating_label_summary(rating_column, label_column)
            }
        return report

    def print_summary(self,
                      text_column: str = "text_",
                      label_column: str = "label",
                      rating_column: str = None) -> None:
        report = self.generate_report(text_column, label_column, rating_column)
        print("=" * 50)
        print("СВОДКА ПО ДАННЫМ")
        print("=" * 50)
        basic_info = report["basic_info"]
        print(f"Размерность данных: {basic_info['shape']}")
        print(f"Количество колонок: {len(basic_info['columns'])}")
        print(f"Колонки: {', '.join(basic_info['columns'])}")
        print()
        missing_count = report["missing_values"]["count"]
        missing_percentage = report["missing_values"]["percentage"]
        if any(count > 0 for count in missing_count.values()):
            print("ПРОПУЩЕННЫЕ ЗНАЧЕНИЯ:")
            for col, count in missing_count.items():
                if count > 0:
                    print(f"  {col}: {count} ({missing_percentage[col]:.1f}%)")
        else:
            print("Пропущенные значения отсутствуют")
        print()
        if "text_analysis" in report:
            print("АНАЛИЗ ТЕКСТА:")
            stats = report["text_analysis"]["length_stats"]
            print(f"  Длина текста - мин: {stats['min']}, макс: {stats['max']}, среднее: {stats['mean']}")
            common_words = report["text_analysis"]["most_common_words"][:5]
            print("  Топ-5 слов:", ", ".join([f"{word}({count})" for word, count in common_words]))
            print()
        if "rating_analysis" in report:
            print("РАСПРЕДЕЛЕНИЕ РЕЙТИНГОВ:")
            dist = report["rating_analysis"]["distribution"]
            total_count = sum(dist.values())
            for rating, count in dist.items():
                percentage = (count / total_count) * 100
                print(f"  {rating}: {count} ({percentage:.1f}%)")
            print()
            print("РЕЙТИНГИ ПО МЕТКАМ (%):")
            rating_by_labels = report["rating_analysis"]["by_labels"]["percentage_distribution"]
            print(rating_by_labels.to_string())
            print()
        if "label_analysis" in report and label_column != rating_column:
            print("РАСПРЕДЕЛЕНИЕ МЕТОК:")
            dist = report["label_analysis"]["distribution"]
            total_count = sum(dist.values())
            for label, count in dist.items():
                percentage = (count / total_count) * 100
                print(f"  {label}: {count} ({percentage:.1f}%)")
            print()


if __name__ == "__main__":
    loader = DataLoader()
    loader.data_path = "../../data"
    yelp_set = {"link": "thedevastator/yelp-reviews-sentiment-dataset", "filename": "train.csv"}
    yelp = loader.load_from_kaggle(**yelp_set)
    explorer = DataExplorer(yelp)
    explorer.print_summary(text_column="text", label_column="label")
