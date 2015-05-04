from storage import MemoryStorage

class LM(object):
    def __init__(self, order):
        assert order > 1
        self.storage = MemoryStorage(order + 1)
        self.order = order

    def add_sentence(self, sentence):
        self.storage.add_sentence(sentence)

    def autonomy(self, ngram):
        assert 0 < len(ngram) <= self.order
        return self.storage.query_autonomy(ngram)

    def segment(self, sentence): 
        sentence = [None] + sentence + [None]

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
                score = best_score[i-j] + self.autonomy(sentence[i-j:i]) * j
                if score > best_score[i]:
                    best_score[i] = score
                    best_segmentation[i] = best_segmentation[i-j] + [sentence[i-j:i]]

        # keep the best segmentation and remove the None

        best_segmentation = best_segmentation[len(sentence)]
        best_segmentation[0].pop(0)
        best_segmentation[-1].pop()
        best_segmentation = list(filter(None, best_segmentation))

        return best_segmentation
