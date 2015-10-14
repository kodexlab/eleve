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

class PyLeveldbTrie: public LeveldbTrie
{
    public:

    using LeveldbTrie::LeveldbTrie;

    void add_ngram_(py::list ngram, int freq)
    {
        add_ngram(convert(ngram), freq);
    };
    void add_ngram__(py::list ngram)
    {
        add_ngram(convert(ngram), 1);
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
};

class PyLeveldbStorage: public LeveldbStorage
{
    public:

    using LeveldbStorage::LeveldbStorage;

    PyLeveldbStorage(size_t order, std::string path, py::list terminals) :
        LeveldbStorage(order, path, convert(terminals))
    {
    };

    void add_ngram_(py::list ngram, int freq)
    {
        add_ngram(convert(ngram), freq);
    };
    void add_ngram__(py::list ngram)
    {
        add_ngram(convert(ngram), 1);
    };
    void add_sentence_(py::list sentence, int freq)
    {
        add_sentence(convert(sentence), freq);
    };
    void add_sentence__(py::list sentence)
    {
        add_sentence(convert(sentence), 1);
    };
    float query_count_(py::list ngram)
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

    size_t get_ngram_length()
    {
        return ngram_length;
    };
};

BOOST_PYTHON_MODULE(cleveldb)
{
    using namespace boost::python;

    class_<PyLeveldbTrie, boost::noncopyable>("LeveldbTrie", init<std::string>())
        .def("add_ngram", &PyLeveldbTrie::add_ngram_)
        .def("add_ngram", &PyLeveldbTrie::add_ngram__)
        .def("query_count", &PyLeveldbTrie::query_count_)
        .def("query_entropy", &PyLeveldbTrie::query_entropy_)
        .def("update_stats", &PyLeveldbTrie::update_stats)
        .def("query_ev", &PyLeveldbTrie::query_ev_)
        .def("query_autonomy", &PyLeveldbTrie::query_autonomy_)
        .def("clear", &PyLeveldbTrie::clear)
    ;

   class_<PyLeveldbStorage, boost::noncopyable>("LeveldbStorage", init<int, std::string,  optional<py::list> >())
        .def("add_ngram", &PyLeveldbStorage::add_ngram_)
        .def("add_ngram", &PyLeveldbStorage::add_ngram__)
        .def("add_sentence", &PyLeveldbStorage::add_sentence_)
        .def("add_sentence", &PyLeveldbStorage::add_sentence__)
        .def("query_count", &PyLeveldbStorage::query_count_)
        .def("query_entropy", &PyLeveldbStorage::query_entropy_)
        .def("update_stats", &PyLeveldbStorage::update_stats)
        .def("query_ev", &PyLeveldbStorage::query_ev_)
        .def("query_autonomy", &PyLeveldbStorage::query_autonomy_)
        .def("clear", &PyLeveldbStorage::clear)
        .add_property("ngram_length", &PyLeveldbStorage::get_ngram_length)
    ;
}
