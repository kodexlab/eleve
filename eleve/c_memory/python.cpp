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
    bool get_dirty()
    {
        return dirty;
    };
    py::list get_normalization()
    {
        py::list normalization_list;
        for(auto& norm: hstats.normalization)
        {
            normalization_list.append( py::make_tuple(norm.mean, norm.stdev));
        }
        return normalization_list;
    };
};


class PyMemoryStorage: public MemoryStorage
{
    public:

    using MemoryStorage::MemoryStorage;

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
    void add_sentence_(py::list s, int freq, size_t ngram_length)
    {
        add_sentence(convert(s), freq, ngram_length);
    };
    void add_ngram_(py::list s, int freq)
    {
        add_ngram(convert(s), freq);
    };
    void add_ngram__(py::list s)
    {
        add_ngram(convert(s), 1);
    };
    size_t get_default_ngram_length()
    {
        return default_ngram_length;
    };
    std::string get_sentence_start()
    {
        return sentence_start;
    };
    std::string get_sentence_end()
    {
        return sentence_end;
    };
};


BOOST_PYTHON_MODULE(cmemory)
{
    using namespace boost::python;

    class_<PyMemoryTrie, boost::noncopyable>("MemoryTrie")
        .add_property("dirty", &PyMemoryTrie::get_dirty)
        .add_property("normalization", &PyMemoryTrie::get_normalization)
        .def("max_depth", &PyMemoryTrie::max_depth)
        .def("update_stats", &PyMemoryTrie::update_stats)
        .def("add_ngram", &PyMemoryTrie::add_ngram_, py::args("ngram", "freq"))
        .def("add_ngram", &PyMemoryTrie::add_ngram__, py::args("ngram"))
        .def("query_count", &PyMemoryTrie::query_count_, py::args("ngram"))
        .def("query_entropy", &PyMemoryTrie::query_entropy_, py::args("ngram"))
        .def("query_ev", &PyMemoryTrie::query_ev_, py::args("ngram"))
        .def("query_autonomy", &PyMemoryTrie::query_autonomy_, py::args("ngram"))
        .def("clear", &PyMemoryTrie::clear)
    ;

    class_<PyMemoryStorage, boost::noncopyable>("MemoryStorage", init<optional<size_t>>(py::args("default_ngram_length")))
        .add_property("default_ngram_length", &PyMemoryStorage::get_default_ngram_length)
        .add_property("sentence_start", &PyMemoryStorage::get_sentence_start)
        .add_property("sentence_end", &PyMemoryStorage::get_sentence_end)
        .def("update_stats", &PyMemoryStorage::update_stats)
        .def("add_ngram", &PyMemoryStorage::add_ngram_, py::args("ngram", "freq"))
        .def("add_ngram", &PyMemoryStorage::add_ngram__, py::args("ngram"))
        .def("add_sentence", &PyMemoryStorage::add_sentence_, (py::arg("sentence"), py::arg("freq")=1, py::arg("ngram_length")=0))
        .def("query_count", &PyMemoryStorage::query_count_, py::args("ngram"))
        .def("query_entropy", &PyMemoryStorage::query_entropy_, py::args("ngram"))
        .def("query_ev", &PyMemoryStorage::query_ev_, py::args("ngram"))
        .def("query_autonomy", &PyMemoryStorage::query_autonomy_, py::args("ngram"))
        .def("clear", &PyMemoryStorage::clear)
    ;
}
