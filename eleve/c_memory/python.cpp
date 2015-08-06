#include "python.hpp"
#include "memory_storage.hpp"

typedef py::stl_input_iterator<std::string> pyStrIt;
typedef py::stl_input_iterator<ID> pyIdIt;

class PyMemoryTrie: public MemoryTrie
{
    public:

    void add_ngram_(py::list ngram, int freq)
    {
        add_ngram(std::vector<ID>{pyIdIt(ngram), pyIdIt()}, freq);
    };
    void add_ngram__(py::list ngram)
    {
        add_ngram(std::vector<ID>{pyIdIt(ngram), pyIdIt()}, 1);
    };
    COUNT query_count_(py::list ngram)
    {
        return query_count(std::vector<ID>{pyIdIt(ngram), pyIdIt()});
    };
    float query_entropy_(py::list ngram)
    {
        return query_entropy(std::vector<ID>{pyIdIt(ngram), pyIdIt()});
    };
    float query_ev_(py::list ngram)
    {
        return query_ev(std::vector<ID>{pyIdIt(ngram), pyIdIt()});
    };
    float query_autonomy_(py::list ngram)
    {
        return query_autonomy(std::vector<ID>{pyIdIt(ngram), pyIdIt()});
    };
};

class PyMemoryStorage: public MemoryStorage
{
    public:

    PyMemoryStorage(size_t o): MemoryStorage(o) {};

    float query_autonomy_(py::list ngram)
    {
        return query_autonomy(strVec{pyStrIt(ngram), pyStrIt()});
    };
    float query_ev_(py::list ngram)
    {
        return query_ev(strVec{pyStrIt(ngram), pyStrIt()});
    };
    float query_count_(py::list ngram)
    {
        return query_count(strVec{pyStrIt(ngram), pyStrIt()});
    };
    float query_entropy_(py::list ngram)
    {
        return query_entropy(strVec{pyStrIt(ngram), pyStrIt()});
    };
    void add_sentence_(py::list s, int freq)
    {
        add_sentence(strVec{pyStrIt(s), pyStrIt()}, freq);
    };
    void add_sentence__(py::list s)
    {
        add_sentence_(s, 1);
    };
    void add_ngram_(py::list s, int freq)
    {
        add_ngram(strVec{pyStrIt(s), pyStrIt()}, freq);
    };
    void add_ngram__(py::list s)
    {
        add_ngram(strVec{pyStrIt(s), pyStrIt()}, 1);
    };

};

BOOST_PYTHON_MODULE(cstorages)
{
    using namespace boost::python;

    class_<PyMemoryTrie, boost::noncopyable>("MemoryTrie")
        .def("add_ngram", &PyMemoryTrie::add_ngram_)
        .def("add_ngram", &PyMemoryTrie::add_ngram__)
        .def("query_count", &PyMemoryTrie::query_count_)
        .def("query_entropy", &PyMemoryTrie::query_entropy_)
        .def("update_stats", &PyMemoryTrie::update_stats)
        .def("query_ev", &PyMemoryTrie::query_ev_)
        .def("query_autonomy", &PyMemoryTrie::query_autonomy_)
        .def("clear", &PyMemoryTrie::clear)
    ;

    class_<PyMemoryStorage, boost::noncopyable>("MemoryStorage", init<size_t>())
        .def("add_ngram", &PyMemoryStorage::add_ngram_)
        .def("add_ngram", &PyMemoryStorage::add_ngram__)
        .def("add_sentence", &PyMemoryStorage::add_sentence_)
        .def("add_sentence", &PyMemoryStorage::add_sentence__)
        .def("query_count", &PyMemoryStorage::query_count_)
        .def("query_entropy", &PyMemoryStorage::query_entropy_)
        .def("query_ev", &PyMemoryStorage::query_ev_)
        .def("query_autonomy", &PyMemoryStorage::query_autonomy_)
        .def("clear", &PyMemoryStorage::clear)
        .def("update_stats", &PyMemoryStorage::update_stats)
    ;
}
