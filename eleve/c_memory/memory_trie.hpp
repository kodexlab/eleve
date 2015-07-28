#ifndef _MEMORYTRIE_HPP_
#define _MEMORYTRIE_HPP_

#include <boost/python.hpp>
#include <boost/python/stl_iterator.hpp>

#include "node.hpp"
#include "child_list.hpp"
#include "entropy.hpp"

namespace py = boost::python;

class MemoryTrie
{
    protected:

    Node root;
    HStats hstats;
    bool dirty;

    void update_stats_rec(float parent_entropy, int depth, Node* node);

    public:

    MemoryTrie() : root(0, std::unique_ptr<ChildList>(new ChildList()), 0), dirty(true)
    {
    };

    void update_stats();

    void add_ngram(py::list ngram, int freq);

    void add_ngram_(py::list ngram)
    {
        add_ngram(ngram, 1);
    };

    COUNT query_count(py::list ngram);
    float query_entropy(py::list ngram);
    float query_ev(py::list ngram);

    void clear();
    float query_autonomy(py::list ngram);
};

#endif
