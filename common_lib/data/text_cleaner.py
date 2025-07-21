import re
import string
from typing import Optional, List

import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer, PorterStemmer

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


class TextCleaner:
    def __init__(self, methods: Optional[List[str]] = None,
                 stop_words_lang: Optional[str] = 'english',
                 lemmatize: bool = False, stem: bool = False):
        self.methods = methods if methods is not None else []
        self.stop_words_lang = stop_words_lang
        self.lemmatize = lemmatize
        self.stem = stem

        self._lemmatizer = WordNetLemmatizer()
        self._stemmer = PorterStemmer()
        self._stop_words = self._load_stop_words()

    def _load_stop_words(self) -> set:
        if not self.stop_words_lang:
            return set()
        try:
            return set(stopwords.words(self.stop_words_lang))
        except OSError:
            print(
                f"Warning: Stop words language '{self.stop_words_lang}' not supported or data not downloaded. "
                f"Using empty stop word list.")
            return set()

    def clean_text(self, text: str) -> str:
        if not isinstance(text, str) or pd.isna(text):
            return ""

        cleaned_text = text

        if 'lower' in self.methods:
            cleaned_text = cleaned_text.lower()

        if 'remove_punctuation' in self.methods:
            cleaned_text = cleaned_text.translate(str.maketrans('', '', string.punctuation))

        if 'remove_numbers' in self.methods:
            cleaned_text = re.sub(r'\d+', '', cleaned_text)

        if 'remove_whitespace' in self.methods:
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()

        words = cleaned_text.split()

        if 'remove_stopwords' in self.methods:
            words = [word for word in words if word not in self._stop_words]

        if self.lemmatize:
            words = [self._lemmatizer.lemmatize(word) for word in words]

        if self.stem:
            words = [self._stemmer.stem(word) for word in words]

        return ' '.join(words)

    def clean_series(self, series: pd.Series) -> pd.Series:
        return series.apply(self.clean_text)
