import nlpaug.augmenter.char as nac

from .base import BaseAugmenter


class KeyboardAugmenter(BaseAugmenter):
    def __init__(self, rate, text_len=None):
        super().__init__("Keyboard", rate)

        # TODO: work out a proper way to calculate these rates
        # aug_char_p and aug_word_p in combination should give aug_rate
        self.augmenter = nac.KeyboardAug(
            aug_char_p=rate,
            aug_word_p=rate,
            aug_char_min=0,
            aug_char_max=None,
            aug_word_max=text_len,
        )

    def augment(self, text):
        return self.augmenter.augment(text, n=1)[0]
