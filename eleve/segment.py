""" :mod:`eleve.segment`
==========================

The segmenter is available by importing ``eleve.Segmenter``.  It is used to
segment sentences (regroup tokens that goes together).

"""
import logging
from math import isnan

logger = logging.getLogger(__name__)


class Segmenter:
    def __init__(self, storage, max_ngram_length=None):
        """ Create a segmenter.

        :param storage: A storage object that has been trained on a corpus (should have a ``query_autonomy`` method).
        :param max_ngram_length: The maximum length of n-gram that can be "merged".
            It should be strictly smaller to the storage's n-gram length.
        """
        assert hasattr(
            storage, "query_autonomy"
        ), "The storage object should have a query_autonomy method."
        self.storage = storage
        if max_ngram_length is None:
            assert hasattr(
                storage, "default_ngram_length"
            ), "The storage should have a default_ngram_length attribute."
            self.max_ngram_length = storage.default_ngram_length - 1
        else:
            assert (
                isinstance(max_ngram_length, int) and max_ngram_length > 1
            ), "max_ngram_length should be an integer bigger than one"
            if max_ngram_length >= storage.default_ngram_length:
                logger.warning(
                    "consider n-grams of size %d at max, BUT storage backend has a default ngram length of %s."
                    % (max_ngram_length, storage.default_ngram_length)
                )
            self.max_ngram_length = max_ngram_length

    def segment(self, sentence):
        """ Segment a sentence.

        :param sentence: A list of tokens.
        :returns: A list of sentence fragments. A sentence fragment is a list of tokens.
        """
        if len(sentence) > 1000:
            logger.warning(
                "The sentence you want to segment is HUGE. This will take a lot of memory."
            )

        # sentence = (
        #     [self.storage.sentence_start] + sentence + [self.storage.sentence_end]
        # )

        # dynamic programming to segment the sentence
        best_segmentation = [[]] * (len(sentence) + 1)
        best_score = [0] + [float("-inf")] * len(sentence)

        # best_score[1] -> autonomy of the first word
        # best_score[2] -> sum of autonomy of the first two words, or autonomy of the first two
        # ...
        order = self.max_ngram_length
        query_autonomy = self.storage.query_autonomy
        for i in range(1, len(sentence) + 1):
            for j in range(1, order + 1):
                if i - j < 0:
                    break
                a = query_autonomy(sentence[i - j : i])
                if isnan(a):
                    a = -100.0
                score = best_score[i - j] + a * j
                if score > best_score[i]:
                    best_score[i] = score
                    best_segmentation[i] = best_segmentation[i - j] + [
                        sentence[i - j : i]
                    ]

        # keep the best segmentation and remove the None
        best_segmentation = best_segmentation[len(sentence)]
        best_segmentation = list(filter(None, best_segmentation))
        # best_segmentation.pop(0)
        # best_segmentation.pop()

        return best_segmentation

    def segment_nbest(self, sentence, nbest=3):
        """ Segment a sentence.

        :param sentence: A list of tokens.
        :returns: A list of sentence fragments. A sentence fragment is a list of tokens.
        """

        from collections import namedtuple

        SegResult = namedtuple("SegResult", "score words")

        if len(sentence) > 1000:
            logger.warning(
                "The sentence you want to segment is HUGE. This will take a lot of memory."
            )

        sentence = (
            [self.storage.sentence_start] + sentence + [self.storage.sentence_end]
        )

        # dynamic programming to segment the sentence
        # list of lists of SegResult
        best_segmentations = [[SegResult(0.0, [])]] * (len(sentence) + 1)
        best_score = [0] + [float("-inf")] * len(sentence)

        # best_score[1] -> autonomy of the first word
        # best_score[2] -> sum of autonomy of the first two words, or autonomy of the first two
        # ...
        order = self.max_ngram_length
        query_autonomy = self.storage.query_autonomy
        for i in range(1, len(sentence) + 1):
            segmentations_at_i = []
            for j in range(1, order + 1):
                if i - j < 0:
                    break
                a = query_autonomy(sentence[i - j : i])
                if isnan(a):
                    a = -100.0
                else:
                    a = a*j
                segmentations_at_i.extend([SegResult(previous_best.score + a, previous_best.words + [sentence[i-j: i]]) for previous_best in best_segmentations[i-j] ])
            best_segmentations[i] = sorted(segmentations_at_i, key=lambda x:x.score)[-nbest:]

        #return [seg.words for seg in best_segmentations[-1][-nbest:]]
        return [seg.words[1:-1] for seg in best_segmentations[-1][-nbest:]]

    @staticmethod
    def tokenInWord(w):
        for i,c in enumerate(w):
            yield "{}-{}_{}".format(c, "".join(w[0:max(i,0)]),"".join(w[i+1:]))


    @staticmethod
    def formatSentenceTokenInWord(sent):
        return " ".join([c for w in sent for c in Segmenter.tokenInWord(w)])


    def segmentSentenceTIW(self, sent: str) -> str:
        return Segmenter.formatSentenceTokenInWord(self.segment(tuple(sent.split(" "))))


    def segmentSentenceTIWBIES(self, sent:str) -> str:
        tokens = tuple(sent.split(" "))
        words = self.segment(tokens)
        bies = []
        for w in words:
            chartoks = list(self.tokenInWord(w))
            if len(w) == 1:
                bies.append(chartoks[0] + "-S")
            else:
                bies.append(chartoks[0] + "-B")
                for i in chartoks[1:-1]:
                    bies.append(i + "-I")
                bies.append(chartoks[-1] + "-E")
        return " ".join(bies)


    def segmentSentenceBIES(self, sent: str) -> str:
        tokens = tuple(sent.split(" "))
        words = self.segment(tokens)
        bies = []
        for w in words:
            if len(w) == 1:
                bies.append(w[0] + "-S")
            else:
                bies.append(w[0] + "-B")
                for i in w[1:-1]:
                    bies.append(i + "-I")
                bies.append(w[-1] + "-E")
        return " ".join(bies)

