import math

from eleve.memory import MemoryTrie

class MemoryStorage:
    """ In-memory storage.
    """
    order = None

    def __init__(self, order):
        """ Storage constructor.

        :param order: The maximum length of n-grams that can be stored.
        """
        assert order > 0 and isinstance(order, int)
        self.order = order

        self.bwd = MemoryTrie(order)
        self.fwd = MemoryTrie(order)

    def add_sentence(self, sentence, freq=1):
        """ Add a sentence to the model.

        :param sentence: The sentence to add. Should be a list of tokens.
        :param freq: The number of times to add this sentence. One by default. May be negative to "remove" a sentence.
        """
        if not sentence:
            return

        token_list = ['^'] + sentence + ['$']
        for i in range(len(token_list) - 1):
            self.fwd.add_ngram(token_list[i:i+self.order], freq)
        token_list = token_list[::-1]
        for i in range(len(token_list) - 1):
            self.bwd.add_ngram(token_list[i:i+self.order], freq)

    def clear(self):
        """ Clear the training data in the model, effectively resetting it.
        """
        self.bwd.clear()
        self.fwd.clear()

    def update_stats(self):
        """ Update the entropies and normalization factors. This function is called automatically when you modify the model and then query it.
        """
        self.bwd.update_stats()
        self.fwd.update_stats()

    def query_autonomy(self, ngram):
        """ Query the autonomy for a ngram.

        :param ngram: A list of tokens.
        :returns: A float, that can be NaN if it is not defined.
        """
        result_fwd = self.fwd.query_autonomy(ngram)
        result_bwd = self.bwd.query_autonomy(ngram[::-1])
        if math.isnan(result_fwd) or math.isnan(result_bwd):
            return float('nan')
        return (result_fwd + result_bwd) / 2
     
    def query_ev(self, ngram):
        """ Query the entropy variation for a ngram.

        :param ngram: A list of tokens.
        :returns: A float, that can be NaN if it is not defined.
        """
        result_fwd = self.fwd.query_ev(ngram)
        result_bwd = self.bwd.query_ev(ngram[::-1])
        if math.isnan(result_fwd) or math.isnan(result_bwd):
            return float('nan')
        return (result_fwd + result_bwd) / 2

    def query_count(self, ngram):
        """ Query the count for a ngram (the number of time it appeared in the training corpus).

        :param ngram: A list of tokens.
        :returns: A float.
        """
        count_fwd = self.fwd.query_count(ngram)
        count_bwd = self.bwd.query_count(ngram[::-1])
        return (count_fwd + count_bwd) / 2

    def query_entropy(self, ngram):
        """ Query the branching entropy for a n-gram.

        :param ngram: A list of tokens.
        :returns: A float, that can be NaN if it is not defined.
        """
        entropy_fwd = self.fwd.query_entropy(ngram)
        entropy_bwd = self.bwd.query_entropy(ngram[::-1])
        if math.isnan(entropy_fwd) or math.isnan(entropy_bwd):
            return float('nan')
        return (entropy_fwd + entropy_bwd) / 2
