# import nlpaug.augmenter.word as naw

from .base import BaseAugmenter


class CutAugmenter(BaseAugmenter):
    def __init__(self, rate, text_len=None):
        super().__init__("Cut", rate)

    def augment(self, text):
        return text[:round(len(text) - len(text)*self.rate)]
