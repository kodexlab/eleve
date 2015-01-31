#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import json
import logging
import tempfile
import os

from flask import Flask, Response
from flask import abort, request, jsonify
from flask import g

import eleve.LM as LM
import eleve.tokenisation as tokenisation

# loading language model
CONFIG = json.load(open("eleve-webservice.cfg"))
#{"dbpath": "pku_8g_zscore", "nmax": 8}


# create our little application :)
app = Flask(__name__)
app.debug = True
# app.jinja_env.add_extension('pyjade.ext.jinja.PyJadeExtension')

def get_lm():
    lm = getattr(g, "_lm", None)
    if lm is None:
        lm = LM.LanguageModel(nmax=CONFIG['nmax'], dbpath=CONFIG['dbpath'])
        g._lm = lm
    return lm


@app.teardown_appcontext
def close_lm(exception):
    lm = get_lm()
    if lm is not None:
        lm.DT.storage.close_connexion()
        

@app.route('/segment/', methods=['POST'])
def segment():
    if request.headers['Content-Type'] == 'application/json': 
        #data = json.loads(request.data)
        data = request.get_json()
        text = data['text']
    else:
        text = request.get_data().decode("utf8")
    print "input", text
    lm = get_lm()
    result = []
    for line in text.strip().split("\n"):
        segmented = lm.segment_corpus_with_preprocessing(line, engine=tokenisation.engine_default, returnType='text').next()
        result.append(segmented)
    text = "\n".join(result)
    return jsonify(result=text)
    #return Response(text, mimetype="text/plain")


# RUN
def main():
    app.run("0.0.0.0")

if __name__ == '__main__':
    sys.exit(main())
