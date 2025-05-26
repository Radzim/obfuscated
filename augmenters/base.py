class BaseAugmenter:
    def __init__(self, name, rate):
        self.name = name
        self.rate = rate

    def augment(self, text):
        raise NotImplementedError()
