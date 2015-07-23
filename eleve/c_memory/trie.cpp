#include <boost/python.hpp>
#include <boost/python/stl_iterator.hpp>

#include "node.hpp"
#include "child_list.hpp"
#include "entropy.hpp"
#include <cmath>

namespace py = boost::python;

class Trie
{
    protected:

    Node root;
    HStats hstats;
    bool dirty;

    void update_stats_rec(float parent_entropy, int depth, Node* node)
    {
        float entropy = node->entropy(hstats);
        
        if(entropy != NAN && (entropy || parent_entropy))
        {
            float ev = entropy - parent_entropy;

            // entropy variation to take into account
            
            if(hstats.normalization.size() <= depth)
            {
                hstats.normalization.resize(depth + 1);
            }

            auto& normalization = hstats.normalization[depth];
            auto old_mean = normalization.mean;
            normalization.count++;

            normalization.mean += (ev - old_mean) / normalization.count;
            normalization.stdev += (ev - old_mean)*(ev - normalization.mean);
        }

        for(auto it = node->begin_childs(); it->get(); it->next())
        {
            update_stats_rec(entropy, depth + 1, it->get());
        }
    };

    public:

    Trie() : root(0, std::unique_ptr<ChildList>(new ChildList()), 0), dirty(true)
    {
    };

    void update_stats()
    {
        // clean the normalization structure
        hstats.normalization.clear();

        // fill it
        update_stats_rec(NAN, 0, &root);

        // calculate the standard deviation given the partial sum
        for(auto& i: hstats.normalization)
        {
            i.stdev = sqrtf(i.stdev / float(i.count ? i.count : 1));
        }

        dirty = false;
    };

    void add_ngram(py::list ngram, COUNT freq=1)
    {
        std::vector<ID> shingle{py::stl_input_iterator<ID>(ngram),
                                py::stl_input_iterator<ID>()};

        dirty = true;

        root.add_shingle(shingle.begin(), shingle.end(), freq);
    };

    COUNT query_count(py::list ngram)
    {
        std::vector<ID> shingle{py::stl_input_iterator<ID>(ngram),
                                py::stl_input_iterator<ID>()};

        Node* n = root.search_child(shingle.cbegin(), shingle.cend());
        if(! n)
        {
            return 0;
        }
        return n->count();
    };

    float query_entropy(py::list ngram)
    {
        std::vector<ID> shingle{py::stl_input_iterator<ID>(ngram),
                                py::stl_input_iterator<ID>()};

        Node* n = root.search_child(shingle.cbegin(), shingle.cend());
        if(! n)
        {
            return NAN;
        }
        return n->entropy(hstats);
    };

    float query_ev(py::list ngram)
    {
        std::vector<ID> shingle{py::stl_input_iterator<ID>(ngram),
                                py::stl_input_iterator<ID>()};

        if(! shingle.size())
            return NAN;

        Node* parent = root.search_child(shingle.cbegin(), shingle.cend() - 1);
        if(! parent)
            return NAN;
        Node* child = parent->search_child(shingle.cend() - 1, shingle.cend());
        if(! child)
            return NAN;
        float parent_entropy = parent->entropy(hstats);
        float entropy = child->entropy(hstats);
        if(entropy != NAN && (entropy || parent_entropy))
            return entropy - parent_entropy;
        return NAN;
    }

    float query_autonomy(py::list ngram)
    {
        if(dirty)
            update_stats();

        float ev = query_ev(ngram);
        if(ev == NAN)
            return NAN;

        auto& n = hstats.normalization[py::len(ngram)];
        return (ev - n.mean) / n.stdev;
    }
};

BOOST_PYTHON_MODULE(eleve_trie)
{
    using namespace boost::python;
    class_<Trie, boost::noncopyable>("Trie")
        .def("add_ngram", &Trie::add_ngram)
        .def("query_count", &Trie::query_count)
        .def("query_entropy", &Trie::query_entropy)
        .def("update_stats", &Trie::update_stats)
        .def("query_ev", &Trie::query_ev)
        .def("query_autonomy", &Trie::query_autonomy)
    ;
}
