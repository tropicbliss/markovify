import re
from .chain import Chain

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


word_split_pattern = re.compile(r"\s+")

def word_split(sentence):
    return re.split(word_split_pattern, sentence)

def word_join(words):
    return " ".join(words)
