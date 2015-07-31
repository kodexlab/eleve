import logging

from storage import Storage

logger = logging.getLogger(__name__)

class Eleve:
    def __init__(self, order, path, storage_class=Storage, *args, **kwargs):
        self.order = order
        self.storage = storage_class(order, path, *args, **kwargs)

    # SENTENCE LEVEL

    def clear(self):
        self.storage.clear()
        return self

    def add_sentence(self, sentence, freq=1):
        self.storage.add_sentence(sentence, freq)

    def segment(self, sentence): 
        if len(sentence) > 1000:
            logger.warning("The sentence you want to segment is HUGE. This will take a lot of memory.")

        sentence = ['^'] + sentence + ['$']

        # dynamic programming to segment the sentence
       
        best_segmentation = [[]]*(len(sentence) + 1)
        best_score = [0] + [float('-inf')]*len(sentence)

        # best_score[1] -> autonomy of the first word
        # best_score[2] -> sum of autonomy of the first two words, or autonomy of the first two
        # ...

        for i in range(1, len(sentence) + 1):
            for j in range(1, self.order + 1):
                if i - j < 0:
                    break
                a = self.query_autonomy(sentence[i-j:i])
                if a != a:
                    a = -100.
                score = best_score[i-j] + a * j
                if score > best_score[i]:
                    best_score[i] = score
                    best_segmentation[i] = best_segmentation[i-j] + [sentence[i-j:i]]

        # keep the best segmentation and remove the None

        best_segmentation = best_segmentation[len(sentence)]
        best_segmentation[0].pop(0)
        best_segmentation[-1].pop()
        best_segmentation = list(filter(None, best_segmentation))

        return best_segmentation

    # NGRAM LEVEL

    def query_autonomy(self, ngram):
        return self.storage.query_autonomy(ngram)

    def query_ev(self, ngram):
        return self.storage.query_ev(ngram)

    def query_count(self, ngram):
        return self.storage.query_count(ngram)

    def query_entropy(self, ngram):
        return self.storage.query_entropy(ngram)
