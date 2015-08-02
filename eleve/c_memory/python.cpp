#include "python.hpp"
#include "memory_storage.hpp"

BOOST_PYTHON_MODULE(memory_storage)
{
    using namespace boost::python;

    class_<MemoryStorage, boost::noncopyable>("MemoryStorage", init<size_t>())
        .def("add_ngram", &MemoryStorage::add_ngram_)
        .def("add_ngram", &MemoryStorage::add_ngram__)
        .def("add_sentence", &MemoryStorage::add_sentence_)
        .def("add_sentence", &MemoryStorage::add_sentence__)
        .def("query_count", &MemoryStorage::query_count_)
        .def("query_entropy", &MemoryStorage::query_entropy_)
        .def("query_ev", &MemoryStorage::query_ev_)
        .def("query_autonomy", &MemoryStorage::query_autonomy_)
        .def("clear", &MemoryStorage::clear)
    ;
}
