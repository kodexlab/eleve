#include <boost/python.hpp>
#include <boost/python/stl_iterator.hpp>

#include "block.hpp"
#include "list_block.hpp"
#include "index_block.hpp"

namespace py = boost::python;

class Trie
{
    protected:

    std::unique_ptr<Block> root;

    void add_shingle(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, ShingleInfo& info)
    {
        auto b = root->add_shingle(shingle_it, shingle_end, info);
        if(b)
            root = std::move(b);

        if(root->size() > BLOCK_MAX_SIZE)
        {
            // tb is the right part of the splitted block + the token in the middle
            // tb2 is the token in the middle + the left part.
            auto tb = root->split();
            auto tb2 = TokenBlock(tb.token, std::move(root));
            auto last = std::move(tb.block);
            root = std::unique_ptr<Block>(new IndexBlock(tb2, last));
        }
    };

    public:

    Trie()
    {
        root = std::unique_ptr<Block>(new ListBlock());
    };

    void add_ngram(py::list ngram, ID docid, COUNT freq)
    {
        std::vector<ID> shingle{py::stl_input_iterator<ID>(ngram),
                                py::stl_input_iterator<ID>()};

        ShingleInfo info(docid, freq);

        add_shingle(shingle.begin(), shingle.end(), info);
    };

    COUNT query_count(py::list ngram)
    {
        std::vector<ID> shingle{py::stl_input_iterator<ID>(ngram),
                                py::stl_input_iterator<ID>()};

        Block* b = root->block_for(shingle.cbegin(), shingle.cend());
        if(! b)
        {
            return 0;
        }
        return b->count();
    };

    void update_stats()
    {
    };

    float query_entropy(py::list ngram)
    {
        std::vector<ID> shingle{py::stl_input_iterator<ID>(ngram),
                                py::stl_input_iterator<ID>()};
        

    };
};

BOOST_PYTHON_MODULE(eleve_trie)
{
    using namespace boost::python;
    class_<Trie, boost::noncopyable>("Trie")
        .def("add_ngram", &Trie::add_ngram)
        .def("query_count", &Trie::query_count)
        .def("query_entropy", &Trie::query_entropy)
    ;
}
