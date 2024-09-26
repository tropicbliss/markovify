from .util import word_join as wjoin, word_split as wsplit


class WordSticher:
    def word_split(self, sentence):
        return wsplit(sentence)

    def word_join(self, words):
        return wjoin(words)
