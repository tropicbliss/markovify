from .chain import Chain
from .text_stitcher import WordSticher


class Output:
    def __init__(self, path, stitcher=WordSticher()):
        self.chain = Chain.from_db(path, stitcher)

    def make_sentence(self):
        words = self.chain.walk()
        return self.chain.word_stitcher.word_join(words)


class Input:
    def __init__(self, input_path, output_path, state_size, append=False, stitcher=WordSticher()):
        self.chain = Chain(state_size, output_path, stitcher)
        self.chain.build(path=input_path, append=append)
