#include <boost/python.hpp>
#include <boost/python/stl_iterator.hpp>

#include "list.hpp"
#include "child_list.hpp"
#include "index_list.hpp"

namespace py = boost::python;

class Trie
{
    protected:

    Node root;

    public:

    Trie() : root(0, std::unique_ptr<ChildList>(new ChildList()), 0)
    {
    };

    void add_ngram(py::list ngram, COUNT freq=1)
    {
        std::vector<ID> shingle{py::stl_input_iterator<ID>(ngram),
                                py::stl_input_iterator<ID>()};

        root.add_shingle(shingle.begin(), shingle.end(), freq);
    };

    COUNT query_count(py::list ngram)
    {
        std::vector<ID> shingle{py::stl_input_iterator<ID>(ngram),
                                py::stl_input_iterator<ID>()};

        Node* b = root.search_child(shingle.cbegin(), shingle.cend());
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
