# -*- coding: utf-8 -*-
"""
Created on Sun May 12 14:13:46 2013

@author: pierre
"""
import numpy as np
import sqlite3
import os.path


class TrieDB(object):

    def __init__(self, dbpath="./db.sqlite"):
        isNew = False if os.path.exists(dbpath) else True
        self.connexion = sqlite3.connect(dbpath)
        if isNew:
            print "creating db"
            self.__createDB()
            self.indexed = False
        else:
            print "connecting to db"
            self.indexed = True
        self.cursor = self.connexion.cursor()

    def __createDB(self):
        self.connexion.execute('''CREATE TABLE Forms
                  ( form text UNIQUE,
                    length integer NOT NULL,
                    count integer DEFAULT 1,
                    RBE real,
                    LBE real,
                    RVBE real,
                    LVBE real,
                    RNVBE real,
                    LNVBE real)''')
        self.connexion.execute('''CREATE TABLE ForwardLinks
                                ( id_pfx integer NOT NULL,
                                  id_next integer NOT NULL, UNIQUE (id_pfx, id_next))''')
        self.connexion.execute('''CREATE TABLE BackwardLinks
                                ( id_sfx integer NOT NULL,
                                  id_prev integer NOT NULL, UNIQUE (id_sfx, id_prev))''')

    def __createIndexes(self):
        self.connexion.execute("CREATE INDEX fwd ON ForwardLinks (id_pfx)")
        self.connexion.execute("CREATE INDEX fwd2 ON ForwardLinks (id_pfx, id_next)")
        self.connexion.execute("CREATE INDEX bwd ON BackwardLinks (id_sfx)")
        self.connexion.execute("CREATE INDEX bwd2 ON BackwardLinks (id_sfx, id_prev)")
        self.connexion.execute("CREATE INDEX frms ON Forms (form)")
        self.connexion.execute("CREATE INDEX len ON Forms (length)")
        self.indexed= True



    def __rec_add(self, prev_id, prefix, remaining, length=0, fwd=True):
        new = "INSERT INTO Forms(form,length) VALUES (?,?)"
        increment = "UPDATE Forms SET count= count+1 WHERE rowid=?"
        get_id = "SELECT rowid FROM Forms WHERE form=?"
        if fwd:
            create_link = "INSERT OR IGNORE INTO ForwardLinks (id_pfx, id_next) VALUES (?,?)"
        else:
            create_link = "INSERT OR IGNORE INTO BackwardLinks (id_sfx, id_prev) VALUES (?,?)"
        if fwd:
            next_ngram = ".".join([prefix, str(remaining[0])]) if prefix != "" else str(remaining[0])
        else:
            next_ngram = ".".join([str(remaining[-1]), prefix]) if prefix != "" else str(remaining[-1])
        next_id = self.cursor.execute(get_id,(next_ngram,)).fetchone()
        if (not next_id):
            cursor = self.cursor # connexion.cursor()
            cursor.execute(new, (next_ngram, length))
            next_id = cursor.lastrowid
        else:
            next_id = next_id[0]
            if fwd:
                self.cursor.execute(increment,(next_id,))
        self.cursor.execute(create_link,(prev_id,next_id))
        if len(remaining) > 1:
            if fwd:
                self.__rec_add(next_id, next_ngram, remaining[1:], length+1, fwd)
            else:
                self.__rec_add(next_id, next_ngram, remaining[:-1], length+1, fwd)





    def add_with_substring(self, ngram, fwd=True):
        get_id0 = "SELECT rowid FROM Forms WHERE length=0"
        new = "INSERT INTO Forms(form,length) VALUES ('',0)"
        increment = "UPDATE Forms SET count = (count+1) WHERE rowid=?"
        id0 = self.cursor.execute(get_id0).fetchone()
        if id0:
            id0 = id0[0]
            if fwd:
                self.cursor.execute(increment, (id0,))
        else:
            c = self.cursor #connexion.cursor()
            c.execute(new)
            id0 = c.lastrowid
        self.__rec_add(id0, "", ngram, 1, fwd)
        if not self.indexed:
            self.__createIndexes()
        #self.connexion.commit()
        #self.cursor = self.connexion.cursor()


    def find(self, ngram, what):
        ngram = ".".join([str(x) for x in ngram])
        #ngram = ngram.replace(" ", ".")
        r = self.cursor.execute("SELECT count,LBE,RBE,LVBE,RVBE,LNVBE,RNVBE FROM Forms WHERE form = ?", (ngram,))
        data = r.fetchone()
        if not data:
            raise NameError(ngram)
        v = None
        if what == "count":
            v = data[0]
        elif what == "LBE":
            v = data[1]
        elif what == "RBE":
            v = data[2]
        elif what == "LVBE":
            v = data[3]
        elif what == "RVBE":
            v = data[4]
        elif what == "LNVBE":
            v = data[5]
        elif what == "RNVBE":
            v = data[6]
        if v is None:
            raise NameError(what + "is not available")
        else:
            return v

    def entropie(self, ngram_id, Fwd=True, boundaryMode="None", last_punct=0):
        if Fwd:
            stmt = "SELECT count FROM Forms,ForwardLinks WHERE ForwardLinks.id_pfx=? AND ForwardLinks.id_next=Forms.rowid"
        else:
            stmt = "SELECT count FROM Forms,BackwardLinks WHERE BackwardLinks.id_sfx=? AND BackwardLinks.id_prev=Forms.rowid"
        values = self.connexion.execute(stmt, (ngram_id,)).fetchall()
        # print "v",ngram_id, values
        if len(values) == 0:
            return None
        if len(values) == 1:
            return 0.
        values = [x[0] for x in values]
        tot = 1. * np.sum(values)
        h = 0.
        for v in values:
            p = v / tot
            h -= p * np.log2(p)
        return h

    def rec_entropy_variation(self, rid, prevBE, fwd=True):
        (BE, VBE) = ("RBE", "RVBE") if fwd else ("LBE", "LVBE")
        stmt_select_data = "SELECT %s FROM Forms WHERE rowid=?" % (BE,)
        stmt_update = "UPDATE Forms SET %s=? WHERE rowid=?" % (VBE,)
        if fwd:
            stmt_select_next = "SELECT id_next FROM ForwardLinks WHERE id_pfx=?"
        else:
            stmt_select_next = "SELECT id_prev FROM BackwardLinks WHERE id_sfx=?"
        BE = self.connexion.execute(stmt_select_data, (rid,)).fetchone()[0]
        if BE is None or prevBE is None:
            VBE = None
        else:
            if BE == 0. and prevBE == 0.:
                VBE = None
            else:
                VBE = BE - prevBE 
            # print stmt_update, VBE, rid
            self.connexion.execute(stmt_update, (VBE, rid))
        for nextid in self.connexion.execute(stmt_select_next,(rid,)):
            self.rec_entropy_variation(nextid[0], BE, fwd)

    def compute_entropy_variation(self, boundaryMode="unique", last_punct=0):
        self.compute_entropy(boundaryMode, last_punct)
        stmt = "SELECT rowid,LBE,RBE FROM Forms WHERE length=0"
        stmt_next_fwd = "SELECT id_next FROM ForwardLinks WHERE id_pfx=?"
        stmt_next_bwd = "SELECT id_prev FROM BackwardLinks WHERE id_sfx=?"
        stmt_next = "SELECT rowid FROM Forms WHERE length=1"
        (idnull, LBE, RBE) = self.connexion.execute(stmt).fetchone()
        print LBE
        print RBE
        for nextid in self.connexion.execute(stmt_next): #self.connexion.execute(stmt_next_fwd, (idnull,)):
            self.rec_entropy_variation(nextid[0], RBE, True)
            # for nextid in self.connexion.execute(stmt_next_bwd, (idnull,)):
            self.rec_entropy_variation(nextid[0], LBE, False)

    def compute_entropy(self, boundaryMode="unique", last_punct=0):
        stmt = "SELECT rowid FROM Forms"
        update_stmt = "UPDATE Forms SET LBE=?,RBE=? WHERE rowid=?"
        for rowid in self.connexion.execute(stmt):
            RBE = self.entropie(rowid[0], Fwd=True)
            LBE = self.entropie(rowid[0], Fwd=False)
            # print rowid, RBE, LBE
            self.cursor.execute(update_stmt, (LBE, RBE, rowid[0]))

    def normalise_types(self, nmax, centralf=np.mean, spreadf=lambda x: 1.):
        print "normalize"
        stmt_fwd = "SELECT rowid,RVBE FROM Forms WHERE length=?"
        stmt_bwd = "SELECT rowid,LVBE FROM Forms WHERE length=?"
        update_fwd = "UPDATE Forms SET RNVBE=? WHERE rowid=?"
        update_bwd = "UPDATE Forms SET LNVBE=? WHERE rowid=?"
        for k in range(1, nmax + 1):
            for doFwd in (True, False):
                stmt = stmt_fwd if doFwd else stmt_bwd
                update = update_fwd if doFwd else update_bwd
                data = [x for x in self.cursor.execute(stmt, (k,)).fetchall() if x[1]]
                values = [x[1] for x in data]
                if len(values) > 0:
                    m = centralf(values)
                    sd = spreadf(values)
                    print k, m, sd
                    for rowid, VBE in data:
                        NVBE = (VBE - m) / sd
                        self.cursor.execute(update, (NVBE, rowid))
                    # TODO: set default for k-grams
                else:
                    print "pas de val pour k=", k
        self.connexion.commit()

    def iterate(self):
        stmt = "SELECT form,count,LNVBE,RNVBE FROM Forms"
        for row in self.connexion.execute(stmt):
            if not row[0] == '':
                yield ([int(x) for x in row[0].split(".")], row[1], row[2], row[3])

    def close_connexion(self):
        self.cursor.close()

class DTrie(object):

    def __init__(self, nmax, dbpath=None):
        self.nmax = nmax
        self.storage = TrieDB(dbpath=dbpath)

    def add(self, ngram, doBackward=False):
        self.storage.add_with_substring(ngram, not doBackward)

    def query_forward(self, ngram, failwith=None):
        try:
            return self.storage.find(ngram, "RNVBE")
        except:
            return failwith

    def query_count_forward(self, ngram, failwith=0):
        try:
            return self.storage.find(ngram, "count")
        except:
            return failwith

    def query_backward(self, ngram, failwith=None):
        try:
            return self.storage.find(ngram, "LNVBE")
        except:
            return failwith

    def query_count_backward(self, ngram, failwith=0):
        try:
            return self.storage.find(ngram, "count")
        except:
            return failwith

    def iterate_on(self, t):
        # TODO:something
        return []

    def iterate(self):
        # TODO: something
        return self.storage.iterate()

    def compute_entropy_variation(self, boundaryMode="unique", last_punct=0):
        self.storage.compute_entropy_variation(boundaryMode, last_punct)

    def compute_entropy(self, boundaryMode="unique", last_punct=0):
        self.storage.compute_entropy(boundaryMode, last_punct)

    def normalise_types(self, nmax, centralf=np.mean, spreadf=lambda x: 1.):
        self.storage.normalise_types(nmax, centralf, spreadf)

    def prune(self):
        # TODO:something
        pass
