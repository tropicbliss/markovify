import re
from chain import Chain
from .util import word_join, word_split


class Output:
    def __init__(self, path):
        self.chain = Chain.from_db(path)

    def make_sentence(self):
        words = self.chain.walk()
        return word_join(words)


class Input:
    def __init__(self, text, state_size, path):
        parsed = self.generate_corpus(text)
        self.chain = Chain(state_size, path)
        self.chain.build(corpus=parsed)

    def sentence_split(self, text):
        return re.split(r"\s*\n\s*", text)

    def generate_corpus(self, text):
        sentences = self.sentence_split(text)
        runs = map(word_split, sentences)
        return runs
