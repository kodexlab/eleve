# -*- coding: utf-8 -*

"""
Segmenteur simple, à utiliser comme une lib
"""
import codecs
import shutil
import tempfile

import numpy as np

import kenleve
import LM
import tokenisation_pl as tokenisation

class Segmenteur(object):
    def __init__(self, order=6, tmpdir=None):
        """Segmenteur "boite noire"
        argument optionel:
        order -- longueur maximale de n-grammes considérés (6)
        tmpdir -- dossier à utiliser pour les fichiers temporaires 
        de préférence vers un SSD
        """
        self.order = order
        self.lm = None
        self.db = None
        self.training_preproc = tokenisation.engine_nothing
        self.tmpdir = tmpdir

    def train(self, training_data, inMemory=False, preproc=None):
        """
        Lance l'entrainement du segmenteur
        training_data -- peut être un chemin vers un fichier ou
        un iterable de chaines de caractères
        inMemory -- tout faire en RAM (sinon dans un SQLite)
        preproc -- choix du tokeniseur
        """
        self.inMemory = inMemory
        if inMemory:
            self.lm = LM.LanguageModel(self.order)
        else:
            self.db = tempfile.NamedTemporaryFile(dir=self.tmpdir)
            self.basename = self.db.name
            self.lm = LM.LanguageModel(self.order, self.basename)
        if preproc is not None:
            self.training_preproc = preproc
        if type(training_data) == str or type(training_data) == unicode:
            self.lm.read_corpus(training_data, preproc=preproc)
        else:
            self.lm.read_iterator(training_data, engine=preproc)
        self.lm.compute_entropy_variation()
        self.lm.normalise_types(np.mean, np.std)

    def train_arpa(self, path, inMemory=True, engine=None, nmax=6, target = "unsegmented", nonorm=False):
        """
        Entraine un segmenteur à partir d'un modèle de langue entrainé par KenLM
        (expérimental)
        """
        self.inMemory = inMemory
        if inMemory:
            self.lm = LM.LanguageModel(nmax)
        else:
            # TODO: rendre DTrie_sqlite compatible
            raise NotImplemented()
            self.db = tempfile.NamedTemporaryFile(dir=self.tmpdir)
            self.basename = self.db.name
            self.lm = LM.LanguageModel(nmax, self.basename)
        if engine is not None:
            self.training_preproc = engine
        def iter_corpus_biread(p):
            f = codecs.open(p,"r","utf8")
            for tokseq in engine.apply(f):
                for tok in tokseq:
                    if tok.category == target:
                        tokens = tok.form
                        fwd = "\t".join(tokens).encode("utf8")
                        bwd = "\t".join(reversed(tokens)).encode("utf8")
                        yield (fwd, bwd)
        i_proba_fwd, i_proba_bwd = kenleve.bidir_lmplz(iter_corpus_biread(path), nmax+1)
        self.lm.load_arpa(i_proba_fwd, i_proba_bwd)
        self.lm.compute_entropy_variation_from_arpa()
        if not nonorm:
            self.lm.normalise_types(np.mean, np.std)

    def segment_iter(self, text, preproc=None, returnType="text", sep=""):
        u"""
        segmente un fichier ou une liste de chaines
        retourne un iterateur sur les résultats
        """
        if preproc is None and self.training_preproc is not None:
            preproc = self.training_preproc
        if type(text) == str or type(text) == unicode:
            with codecs.open(text, "r", "utf8") as stream:
                return self.lm.segment_corpus_with_preprocessing(stream, engine=preproc, returnType=returnType, sep=sep)
        else:
            return self.lm.segment_corpus_with_preprocessing(text, engine=preproc, returnType=returnType, sep=sep)


    def segment_one(self, text, preproc=None, returnType="text", sep=""):
        u"""
        segmente une unique chaine de caractères
        """
        return self.lm.segment_corpus_with_preprocessing(text, engine=preproc, returnType=returnType, sep=sep).next()

    def extractMultiTokens(self, text, preproc=None, threshold=0., sep="", target='unsegmented'):
        """
        Retourne une liste de «multi-mots» contenus dans un text avec leur score d'autonomie associé.
        """
        results = []
        for tokseq in preproc.apply([text]):
            for tok in tokseq:
                if tok.category == target:
                    for debut in xrange(len(tok.form)-1):
                        for fin in xrange(min(len(tok.form), debut + self.order+1), debut,  -1):
                            a = self.lm.autonomie(tok.form[debut:fin])
                            if a >= threshold:
                                results.append((sep.join(tok.form[debut:fin]),a))
        return results
            

    def getWordList(self, threshold=0., sep="\t"):
        """
        retourne la liste du vocabulaire considéré «autonome» par le segmenteur
        threshold -- seuil sur l'autonomie (0.)
        sep -- chaine de séparation entre les tokens pour les expressions multi-mots ("\t")
        """
        result = []
        for ng in sorted(self.lm.iter_model(threshold, sep=sep),key=lambda x:x['autonomie']):
            result.append(ng['forme'])
        return result

    def save(self, path):
        """sauvegarde une copie modèle
        /!\ les modèles crées avec inMemory=True ne sont pas sauvegardables en l'état (mais picklable p'tet, à voir)
        """
        if not self.inMemory:
            shutil.copy(self.basename + ".sqlite", path + ".sqlite")
            self.lm.save(path + ".lm")
            # shutil.copy(self.basename + ".lm", path + ".lm")
        else:
            raise NotImplementedError

    def load(self, path):
        """charge un modèle à partir d'un fichier sqlite et d'un .lm
        path -- base du chemin commune au .lm et .sqlite
        """
        self.basename = path
        self.lm = LM.LanguageModel(self.order, dbpath=path)
