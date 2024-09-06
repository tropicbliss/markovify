import re
from .chain import Chain
from .util import word_join


class Output:
    def __init__(self, path):
        self.chain = Chain.from_db(path)

    def make_sentence(self):
        words = self.chain.walk()
        return word_join(words)


class Input:
    def __init__(self, input_path, output_path, state_size):
        self.chain = Chain(state_size, output_path)
        self.chain.build(path=input_path)

    def sentence_split(self, text):
        return re.split(r"\s*\n\s*", text)
