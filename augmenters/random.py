import nlpaug.augmenter.word as naw

from .base import BaseAugmenter


class RandomAugmenter(BaseAugmenter):
    def __init__(self, rate, text_len=None):
        super().__init__("Random", rate)

        self.augmenter = naw.RandomWordAug(aug_p=rate, aug_min=0, aug_max=text_len)

    def augment(self, text):
        return self.augmenter.augment(text, n=1)[0]
