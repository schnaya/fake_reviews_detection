import random
import nltk
import nltk
nltk.download('averaged_perceptron_tagger_eng')

from typing import List, Optional

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    print("NLTK data 'wordnet' not found. Downloading...")
    nltk.download('wordnet')
except Exception as e:
    print(f"Error checking/downloading NLTK 'wordnet': {e}")

try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    print("NLTK data 'averaged_perceptron_tagger' not found. Downloading...")
    nltk.download('averaged_perceptron_tagger')
except Exception as e:
    print(f"Error checking/downloading NLTK 'averaged_perceptron_tagger': {e}")

try:
    nltk.data.find('corpora/omw-1.4')  # Open Multilingual WordNet - sometimes needed
except LookupError:
    print("NLTK data 'omw-1.4' not found. Downloading...")
    nltk.download('omw-1.4')
except Exception as e:
    print(f"Error checking/downloading NLTK 'omw-1.4': {e}")

from nltk.corpus import wordnet as wn
from nltk.tag import pos_tag


def get_wordnet_pos(tag):
    """Map NLTK POS tags to WordNet POS tags"""
    if tag.startswith('J'):
        return wn.ADJ
    elif tag.startswith('V'):
        return wn.VERB
    elif tag.startswith('N'):
        return wn.NOUN
    elif tag.startswith('R'):
        return wn.ADV
    else:
        return None


def synonym_replacement(words: List[str], n: int = 1) -> List[str]:
    """Replace n random words in a sentence with synonyms"""
    new_words = list(words)
    random_word_list = list(set([word for word in words if word.isalpha()]))
    random.shuffle(random_word_list)
    num_replaced = 0
    for random_word in random_word_list:
        synonyms = []
        pos_tags = pos_tag([random_word])
        if pos_tags:
            pos = pos_tags[0][1]
            wn_pos = get_wordnet_pos(pos)
            if wn_pos:
                for syn in wn.synsets(random_word, pos=wn_pos):
                    for lemma in syn.lemmas():
                        synonym = lemma.name().replace('_', ' ')
                        if synonym != random_word:
                            synonyms.append(synonym)
            else:
                for syn in wn.synsets(random_word):
                    for lemma in syn.lemmas():
                        synonym = lemma.name().replace('_', ' ')
                        if synonym != random_word:
                            synonyms.append(synonym)
        if len(synonyms) > 0:
            synonym = random.choice(synonyms)
            for i, w in enumerate(new_words):
                if w == random_word:
                    new_words[i] = synonym
            num_replaced += 1

        if num_replaced >= n:
            break

    return new_words


def random_deletion(words: List[str], p: float = 0.1) -> List[str]:
    """Randomly delete words from a sentence with probability p"""
    if words is None or not words:
        return []
    if len(words) == 1:
        return words

    new_words = []
    for word in words:
        r = random.uniform(0, 1)
        if r > p:
            new_words.append(word)
    if len(new_words) == 0:
        return [random.choice(words)]
    return new_words


def random_swap(words: List[str], n: int = 1) -> Optional[List[str]]:
    """Randomly swap n pairs of words in a sentence"""
    if words is None or len(words) < 2:
        return words

    new_words = list(words)
    n = min(n, len(words) // 2)
    for _ in range(n):
        try:
            idx1, idx2 = random.sample(range(len(words)), 2)
            new_words[idx1], new_words[idx2] = new_words[idx2], new_words[idx1]
        except ValueError:
            break

    return new_words


def random_insertion(words: List[str], n: int = 1) -> List[str]:
    """Randomly insert n synonyms into the sentence"""
    if words is None:
        return []
    new_words = list(words)
    for _ in range(n):
        add_word(new_words)
    return new_words


def add_word(new_words: List[str]):
    """Helper function for random_insertion: finds a random synonym and inserts it."""
    synonyms = []
    counter = 0
    words_to_choose_from = [w for w in new_words if w.isalpha()]
    if not words_to_choose_from:
        return

    while len(synonyms) < 1 and counter < 10:
        random_word = random.choice(words_to_choose_from)
        pos_tags = pos_tag([random_word])
        if pos_tags:
            pos = pos_tags[0][1]
            wn_pos = get_wordnet_pos(pos)
            if wn_pos:
                for syn in wn.synsets(random_word, pos=wn_pos):
                    for lemma in syn.lemmas():
                        synonym = lemma.name().replace('_', ' ')
                        if synonym != random_word:
                            synonyms.append(synonym)
            else:
                for syn in wn.synsets(random_word):
                    for lemma in syn.lemmas():
                        synonym = lemma.name().replace('_', ' ')
                        if synonym != random_word:
                            synonyms.append(synonym)
        counter += 1

    if len(synonyms) > 0:
        random_synonym = random.choice(synonyms)
        random_idx = random.randint(0, len(new_words))
        new_words.insert(random_idx, random_synonym)


class TextAugmenter:
    """
    Class to apply various text augmentation techniques to a single text.
    The core logic works on lists of words.
    """

    def __init__(self, methods: Optional[List[str]] = None):
        default_methods = ['synonym_replacement', 'random_deletion', 'random_swap', 'random_insertion']
        self.methods = methods if methods is not None else default_methods
        self._augmentation_functions = {
            'synonym_replacement': synonym_replacement,
            'random_deletion': random_deletion,
            'random_swap': random_swap,
            'random_insertion': random_insertion,
        }
        self.methods = [m for m in self.methods if m in self._augmentation_functions]
        if not self.methods:
            print("Warning: No valid augmentation methods specified or found. Augmenter will do nothing.")

    def augment_text(self, text: str, num_aug: int = 1) -> List[str]:
        if not isinstance(text, str) or not text.strip():
            return []

        words = text.split()

        augmented_texts = []
        attempt_count = 0
        max_attempts = num_aug * 5
        while len(augmented_texts) < num_aug and attempt_count < max_attempts:
            method_name = random.choice(self.methods)
            augmentation_function = self._augmentation_functions[method_name]
            try:
                aug_words = augmentation_function(words.copy())
                augmented_text = ' '.join(aug_words).strip()
                if augmented_text and augmented_text != text.strip() and augmented_text not in augmented_texts:
                    augmented_texts.append(augmented_text)

            except Exception as e:
                print(f"Error applying augmentation method '{method_name}' to text '{text[:50]}...': {e}")

            attempt_count += 1

        return augmented_texts
