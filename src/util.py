import re

word_split_pattern = re.compile(r"\s+")


def word_split(sentence):
    return re.split(word_split_pattern, sentence)


def word_join(words):
    return " ".join(words)
