import pandas as pd


class Vizualizator:
    def __init__(self, model, vectorizer, label_map, fake_label_key='CG', real_label_key='OR'):
        self.model = model
        self.vectorizer = vectorizer
        self.label_map = label_map
        self.fake_label = label_map.get(fake_label_key)
        self.real_label = label_map.get(real_label_key)
        self.feature_names = vectorizer.get_feature_names_out()
        self.word_coefficients = pd.Series(model.coef_[0], index=self.feature_names)

    def print_top_words(self, top_n=30):
        classes = self.model.classes_

        if self.fake_label not in classes or self.real_label not in classes:
            raise ValueError("Ошибка: Метки классов отсутствуют в модели. "
                             f"classes_: {classes}, label_map: {self.label_map}")

        if classes[1] == self.fake_label:
            coef_direction = 1
        elif classes[0] == self.fake_label:
            coef_direction = -1
        else:
            raise KeyError("Ошибка: Не удалось сопоставить fake_label с классами модели.")

        top_fake_words = self.word_coefficients.sort_values(ascending=(coef_direction < 0)).head(top_n)
        top_real_words = self.word_coefficients.sort_values(ascending=(coef_direction > 0)).head(top_n)

        print("\n--- Слова, наиболее связанные с классом 'fake' ---")
        print(top_fake_words)
        print("\n--- Слова, наиболее связанные с классом 'real' ---")
        print(top_real_words)
