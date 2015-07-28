#include "memory_trie.hpp"

#include <cmath>

void MemoryTrie::update_stats_rec(float parent_entropy, int depth, Node* node)
{
    float entropy = node->entropy(hstats);
    
    // entropy == entropy, for « entropy != NAN »
    if(entropy == entropy && (entropy || parent_entropy))
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

void MemoryTrie::update_stats()
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

void MemoryTrie::add_ngram(py::list ngram, int freq)
{
    std::vector<ID> shingle{py::stl_input_iterator<ID>(ngram),
                            py::stl_input_iterator<ID>()};

    dirty = true;

    root.add_shingle(shingle.begin(), shingle.end(), freq);
};

COUNT MemoryTrie::query_count(py::list ngram)
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

float MemoryTrie::query_entropy(py::list ngram)
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

float MemoryTrie::query_ev(py::list ngram)
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

    // entropy == entropy for « entropy != NAN » (that always returns true)
    if(entropy == entropy && (entropy || parent_entropy))
        return entropy - parent_entropy;
    return NAN;
}

float MemoryTrie::query_autonomy(py::list ngram)
{
    if(dirty)
        update_stats();

    float ev = query_ev(ngram);
    if(ev != ev) // if ev is NAN
        return NAN;

    auto& n = hstats.normalization[py::len(ngram)];
    return (ev - n.mean) / n.stdev;
}

void MemoryTrie::clear()
{
    dirty = true;
    root = Node(0, std::unique_ptr<ChildList>(new ChildList()), 0);
};

BOOST_PYTHON_MODULE(memory_trie)
{
    using namespace boost::python;
    class_<MemoryTrie, boost::noncopyable>("MemoryTrie")
        .def("add_ngram", &MemoryTrie::add_ngram)
        .def("add_ngram", &MemoryTrie::add_ngram_)
        .def("query_count", &MemoryTrie::query_count)
        .def("query_entropy", &MemoryTrie::query_entropy)
        .def("update_stats", &MemoryTrie::update_stats)
        .def("query_ev", &MemoryTrie::query_ev)
        .def("query_autonomy", &MemoryTrie::query_autonomy)
        .def("clear", &MemoryTrie::clear)
    ;
}
