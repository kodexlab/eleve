from memory import MemoryStorage

class Eleve:
    def __init__(self, order, path, storage_class=MemoryStorage):
        assert order > 1
        assert isinstance(path, str)
        self.order = order

        self.bwd = storage_class(order + 1, path + '_bwd')
        self.fwd = storage_class(order + 1, path + '_fwd')

    # SENTENCE LEVEL

    def clear(self):
        self.bwd.clear()
        self.fwd.clear()
        return self

    def add_sentence(self, sentence, docid, freq=1):
        token_list = [None] + sentence + [None]
        for i in range(len(token_list) - 1):
            self.fwd.add_ngram(token_list[i:i+self.order+1], docid, freq)
        token_list = token_list[::-1]
        for i in range(len(token_list) - 1):
            self.bwd.add_ngram(token_list[i:i+self.order+1], docid, freq)

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
                score = best_score[i-j] + self.query_autonomy(sentence[i-j:i]) * j
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
        assert 0 < len(ngram) <= self.order
        result_fwd = self.fwd.query_autonomy(ngram)
        result_bwd = self.bwd.query_autonomy(ngram[::-1])
        return (result_fwd + result_bwd) / 2
     
    def query_ev(self, ngram):
        result_fwd = self.fwd.query_ev(ngram)
        result_bwd = self.bwd.query_ev(ngram[::-1])
        return (result_fwd + result_bwd) / 2

    def query_node(self, ngram):
        result_fwd = self.fwd.query_node(ngram)
        result_bwd = self.bwd.query_node(ngram[::-1])
        return tuple((i + j) / 2 for i, j in zip(result_fwd, result_bwd))

    def update_stats(self):
        self.fwd.update_stats()
        self.bwd.update_stats()

