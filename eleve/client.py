# -*- coding: utf8 -*-

import requests


URL = "http://localhost:5000/segment/"


class NetworkError(Exception):
    def __str__(self):
        return "error while connecting to the webservice"


def segment_plaintext(text):
    r = requests.post(URL, text.encode("utf8"), headers={"Content-Type": "text/plain"})
    if r.status_code != 200:
        raise NetworkError()
    return r.json()["result"]

