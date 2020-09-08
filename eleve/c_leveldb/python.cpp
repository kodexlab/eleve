#include "python.hpp"
#include "leveldb_storage.hpp"
#include "Python.h"

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
            const char* u = PyUnicode_AsUTF8AndSize(o, &s);
            r.push_back(std::string(u, s));
        }
        else
        {
            o = PyObject_Str(o);
            Py_ssize_t s;
            const char* u = PyUnicode_AsUTF8AndSize(o, &s);
            r.push_back(std::string(u, s));
            Py_DECREF(o);
        }
    }
    return r;
};

class PyLeveldbTrie: public LeveldbTrie
{
    public:

    using LeveldbTrie::LeveldbTrie;

    void add_ngram_(py::list ngram, int freq)
    {
        add_ngram(convert(ngram), freq);
    };
    COUNT query_count_(py::list ngram)
    {
        return query_count(convert(ngram));
    };
    float query_entropy_(py::list ngram)
    {
        return query_entropy(convert(ngram));
    };
    float query_ev_(py::list ngram)
    {
        return query_ev(convert(ngram));
    };
    float query_autonomy_(py::list ngram)
    {
        return query_autonomy(convert(ngram));
    };
    bool get_dirty()
    {
        return dirty;
    };
    std::string get_path()
    {
        return path;
    };
    py::list get_normalization()
    {
        py::list normalization_list;
        for(auto& norm: normalization)
        {
            normalization_list.append(py::make_tuple(norm.mean, norm.stdev));
        }
        return normalization_list;
    };
};

class PyLeveldbStorage: public LeveldbStorage
{
    public:

    using LeveldbStorage::LeveldbStorage;

    void add_ngram_(py::list ngram, int freq)
    {
        add_ngram(convert(ngram), freq);
    };
    void add_ngram__(py::list ngram)
    {
        add_ngram(convert(ngram), 1);
    };
    void add_sentence_(py::list sentence, int freq, size_t ngram_length)
    {
        add_sentence(convert(sentence), freq, ngram_length);
    };
    COUNT query_count_(py::list ngram)
    {
        return query_count(convert(ngram));
    };
    float query_entropy_(py::list ngram)
    {
        return query_entropy(convert(ngram));
    };
    float query_ev_(py::list ngram)
    {
        return query_ev(convert(ngram));
    };
    float query_autonomy_(py::list ngram)
    {
        return query_autonomy(convert(ngram));
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
    std::string get_path()
    {
        return path;
    };
};

BOOST_PYTHON_MODULE(cleveldb)
{
    using namespace boost::python;

    class_<PyLeveldbTrie, boost::noncopyable>("LeveldbTrie",
          init<std::string>(py::args("path")))
        .add_property("dirty", &PyLeveldbTrie::get_dirty)
        .add_property("normalization", &PyLeveldbTrie::get_normalization)
        .add_property("path", &PyLeveldbTrie::get_path)
        .def("update_stats", &PyLeveldbTrie::update_stats, py::args("ngram"))
        .def("add_ngram", &PyLeveldbTrie::add_ngram_, (py::args("ngram"), py::args("freq")=1))
        .def("max_depth", &PyLeveldbTrie::max_depth)
        .def("query_count", &PyLeveldbTrie::query_count_, py::args("ngram"))
        .def("query_entropy", &PyLeveldbTrie::query_entropy_, py::args("ngram"))
        .def("query_ev", &PyLeveldbTrie::query_ev_, py::args("ngram"))
        .def("query_autonomy", &PyLeveldbTrie::query_autonomy_, py::args("ngram"))
        .def("clear", &PyLeveldbTrie::clear)
        .def("close", &PyLeveldbTrie::close)
    ;

   class_<PyLeveldbStorage, boost::noncopyable>("LeveldbStorage",
          init<std::string, optional<size_t>>(py::args("path", "default_ngram_length")))
        .add_property("default_ngram_length", &PyLeveldbStorage::get_default_ngram_length)
        .add_property("sentence_start", &PyLeveldbStorage::get_sentence_start)
        .add_property("sentence_end", &PyLeveldbStorage::get_sentence_end)
        .add_property("path", &PyLeveldbStorage::get_path)
        .def("update_stats", &PyLeveldbStorage::update_stats)
        .def("add_ngram", &PyLeveldbStorage::add_ngram_, (py::args("ngram"), py::args("freq")=1))
        .def("add_sentence", &PyLeveldbStorage::add_sentence_, (py::args("sentence"), py::args("freq")=1, py::args("ngram_length")=0))
        .def("query_count", &PyLeveldbStorage::query_count_, py::args("ngram"))
        .def("query_entropy", &PyLeveldbStorage::query_entropy_, py::args("ngram"))
        .def("query_ev", &PyLeveldbStorage::query_ev_, py::args("ngram"))
        .def("query_autonomy", &PyLeveldbStorage::query_autonomy_, py::args("ngram"))
        .def("clear", &PyLeveldbStorage::clear)
        .def("close", &PyLeveldbStorage::close)
    ;
}
