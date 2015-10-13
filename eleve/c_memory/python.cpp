#include "python.hpp"
#include "memory_storage.hpp"
#include "Python.h"

typedef py::stl_input_iterator<ID> pyIdIt;

std::vector<std::string> convert(py::list& ngram)
{
    std::vector<std::string> r;
    r.reserve(py::len(ngram));
    for(int i = 0; i < py::len(ngram); ++i)
    {
        PyObject* o = py::api::object(ngram[i]).ptr();
        if(PyUnicode_Check(o))
        {
            Py_ssize_t s;
            char* u = PyUnicode_AsUTF8AndSize(o, &s);
            r.push_back(std::string(u, s));
        }
        else
        {
            o = PyObject_Str(o);
            Py_ssize_t s;
            char* u = PyUnicode_AsUTF8AndSize(o, &s);
            r.push_back(std::string(u, s));
            Py_DECREF(o);
        }
    }
    return r;
};

class PyMemoryTrie: public MemoryTrie
{
    public:

    using MemoryTrie::MemoryTrie;

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

    using MemoryStorage::MemoryStorage;

    PyMemoryStorage(size_t order, py::list terminals) : PyMemoryStorage(order, convert(terminals))
    {
    };

    float query_autonomy_(py::list ngram)
    {
        return query_autonomy(convert(ngram));
    };
    float query_ev_(py::list ngram)
    {
        return query_ev(convert(ngram));
    };
    float query_count_(py::list ngram)
    {
        return query_count(convert(ngram));
    };
    float query_entropy_(py::list ngram)
    {
        return query_entropy(convert(ngram));
    };
    void add_sentence_(py::list s, int freq)
    {
        add_sentence(convert(s), freq);
    };
    void add_sentence__(py::list s)
    {
        add_sentence(convert(s), 1);
    };
    void add_ngram_(py::list s, int freq)
    {
        add_ngram(convert(s), freq);
    };
    void add_ngram__(py::list s)
    {
        add_ngram(convert(s), 1);
    };

};

BOOST_PYTHON_MODULE(cmemory)
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

    class_<PyMemoryStorage, boost::noncopyable>("MemoryStorage",
        init<size_t, optional<py::list>>(py::args("order", "terminals")))
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
