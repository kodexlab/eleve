#!/usr/bin/env python
# -*- coding: utf8 -*-

import sys
import argparse
import numpy as np
import codecs

# import MDLo as MDL
import LM as LM
import standalone

if __name__ == "__main__":
    usage = "usage: eleve.py [options] <input_file> <output_prefix>"
    parser = argparse.ArgumentParser(usage=usage)
    parser.add_argument("input", help=u"input corpus file")
    parser.add_argument("output", action="store", help=u"output files prefix")
    parser.add_argument("-p", "--preprocess", action="store", help=u"use sxpipe for preprocessing", default=None)
    parser.add_argument("-b", "--beonly", action="store_true", help=u"use BE and not VBE")
    parser.add_argument("-k", "--k", action="store", help=u"maximium size of the ngrams (6)",default=6, type=int)
    parser.add_argument("-n", "--normalisation", action="store", help=u"normalisation function (mean, z-score or none)", default=None)
    parser.add_argument("-a", "--autofun", action="store", help=u"autonomy function (sum or min)", default="sum")
    parser.add_argument("-s", "--seg", action="store", help=u"alternative segmentation algorithm (mag, jin or zhikov)",default="mag"        )
    parser.add_argument("-m", "--mdl", action="store_true", help=u"performs mdl optimisation")
    parser.add_argument("-l", "--limits", action="store", help=u"constraints the mdl (split,merge) ")
    parser.add_argument("-d", "--dump", action="store_true", help=u"dump model and mdl steps")
    parser.add_argument("-i", "--ignoreboundaries", action="store_true", help=u"ignore clues from explicit boundaries")
    parser.add_argument("--noseg", action="store_true", help=u"skip segmentation step")
    parser.add_argument("--notrain", action="store_true", help=u"skip training step")
    parser.add_argument("--dbpath", action="store", help=u"use SQLite DB for training", default=None)
    args = parser.parse_args()
    lm = LM.LanguageModel(nmax=args.k, dbpath=args.dbpath)
    print "building model from %s %s preprocessing" % (args.input, "with " if args.preprocess else "without")
    sxp = args.preprocess
    if not args.notrain:
        lm.read_corpus(args.input, sxpipe=sxp)
        bnd = "None" if args.ignoreboundaries else "unique"
        print "computing entropy " + "variation" if not args.beonly else ""
        if args.beonly:
            lm.compute_entropy(boundaryMode=bnd)
        else:
            lm.compute_entropy_variation(boundaryMode=bnd)
        print "normalisation : %s" % (args.normalisation,)
        if args.normalisation == "mean":
            lm.normalise_types(centralf=np.mean, spreadf=lambda x:1.)
        if args.normalisation == "z-score":
            lm.normalise_types(centralf=np.mean, spreadf=np.std)
    #mdl = MDL.MDL(lm,args.input)
    #print "reading"
    #if sxp:
    #    if sxp == "unitex":
    #        mdl.readCorpus_unitex()
    #    else:
    #        mdl.readCorpus_sxpipe(sxlang=sxp)
    #else:
    #    mdl.readCorpus_raw()
    if args.dump:
        lm.dump_to_file("%s_%s_%s_init.sxpipe" % (args.output, sxp, args.normalisation))
        print "dumped"
    if not args.dbpath is None:
        lm.save(args.dbpath + ".lm")
    if args.noseg:
        sys.exit(0)
    print "segmenting"
    if args.seg=="mag":
        out = codecs.open(args.output,"w","utf8")
        for tokseq in preproc.default_engine.apply_to_file(args.input):
            result = []
            for tok in tokseq:
                if tok.category == "unsegmented":
                    result.extend(lm.segmente_unitex(tok.form))
                else:
                    result.append(tok)
            #print >>out, " ".join(["{%s,.%s}" % t if t.category != "EOS" else "{S}" for t in result])
            print >>out, " ".join([ t.form if t.category != "EOS" else "{S}" for t in result])
        out.close()
        #if args.autofun == "sum":
        #    mdl.ACL12_init(af=lambda x,y:x+y)
        #else:
    elif args.seg == "nbests":
        out = codecs.open(args.output, "w", "utf8")
        for tokseq in unitex.itokseq_from_file(args.input):
            for tok in tokseq:
                if tok.category == "unsegmented":
                    results = lm.segmente_unitex_nbest(tok.form)
                else:
                    results = [tok]
                for result in results:
                    #print >>out, " ".join(["{%s,.%s}" % t if t.category != "EOS" else "{S}" for t in result])
                    print >>out, " ".join([ t.form if t.category != "EOS" else "{S}" for t in result])
        out.close()
