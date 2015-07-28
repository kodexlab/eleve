#ifndef _MEMORY_STORAGE_HPP_
#define _MEMORY_STORAGE_HPP_
#include "memory_trie.hpp"

class MemoryStorage
{
    protected:
    unsigned char order;
    MemoryTrie fwd;
    MemoryTrie bwd;
    std::map<std::size_t, std::string> hash_to_token;

    std::vector<ID> tokens_to_ids(std::vector<std::string> tokens);
    std::vector<std::string> ids_to_tokens(std::vector<ID> ids);

    public:
    
    MemoryStorage() {};

    void add_sentence(py::list s, int freq=1);
    void add_ngram(py::list s, int freq=1);

    void clear();

    float query_autonomy(py::list ngram);
    float query_ev(py::list ngram);
    float query_count(py::list ngram);
    float query_entropy(py::list ngram);

};

#endif
