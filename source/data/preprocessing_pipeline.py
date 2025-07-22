from typing import Optional, List, Any

import pandas as pd
from sklearn.pipeline import Pipeline

from source.data import DataPreparer
from source.text_transformers.text_cleaner_transformer import TextCleanerTransformer


class PreprocessingPipelineBuilder(DataPreparer):
    """
    A DataPreparer extension that includes functionality to build scikit-learn
    preprocessing pipelines, specifically for text data.
    """
    def __init__(self, df: pd.DataFrame):
        super().__init__(df)

    def build_text_preprocessing_pipeline(self,
                                          text_column: str,
                                          vectorizer_method: str = 'tfidf',
                                          clean_text_methods: Optional[List[str]] = None,
                                          clean_text_stopwords_lang: Optional[str] = 'english',
                                          clean_text_lemmatize: bool = False,
                                          clean_text_stem: bool = False,
                                          **vectorizer_kwargs: Any
                                          ) -> Pipeline:

        self._validate_column_exists(text_column)

        print(f"\nBuilding text preprocessing pipeline for column '{text_column}'...")

        text_cleaner = TextCleanerTransformer(
            text_column=text_column,
            methods=clean_text_methods,
            stop_words_lang=clean_text_stopwords_lang,
            lemmatize=clean_text_lemmatize,
            stem=clean_text_stem
        )

        vectorizer = self._create_vectorizer(vectorizer_method, **vectorizer_kwargs)

        preprocessing_pipeline = Pipeline([
            ('text_cleaner', text_cleaner),
            ('vectorizer', vectorizer)
        ])

        self.vectorizer = vectorizer

        print("Text preprocessing pipeline built.")
        return preprocessing_pipeline
