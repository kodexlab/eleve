import logging
import math

logger = logging.getLogger(__name__)

class Segmenter:
    def __init__(self, storage, order):
        """
        Create a segmenter.

        :param storage: A storage object that has been trained on a corpus (should have a ``query_autonomy`` method).
        :param order: The maximum length of n-gram you can query the autonomy of.
                      Generally, it should be the number you passed to the storage minus one.
        """
        assert hasattr(storage, 'query_autonomy'), "The storage object should have a query_autonomy method."
        assert isinstance(order, int) and order > 1, "The order should be an integer bigger than one"
        self.storage = storage
        self.order = order

    def segment(self, sentence): 
        """
        Segment a sentence.

        :param sentence: A list of tokens.
        :returns: A list of sentence fragments. A sentence fragment is a list of tokens.
        """

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
                a = self.storage.query_autonomy(sentence[i-j:i])
                if math.isnan(a):
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
