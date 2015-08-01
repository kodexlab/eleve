#ifndef _MEMORY_STORAGE_HPP_
#define _MEMORY_STORAGE_HPP_
#include "memory_trie.hpp"
#include "python.hpp"

typedef const std::vector<std::string> strVec;
typedef py::stl_input_iterator<std::string> pyStrIt;

class MemoryStorage
{
    protected:
    size_t order;
    MemoryTrie fwd;
    MemoryTrie bwd;
    std::map<std::size_t, std::string> hash_to_token;

    std::vector<ID> tokens_to_ids(strVec& tokens);
    strVec ids_to_tokens(const std::vector<ID>& ids);
    static std::vector<ID> reverse(const std::vector<ID>&);

    public:
    
    MemoryStorage(size_t o) : order(o) {};

    void add_sentence(std::vector<std::string> s, int freq=1);
    void add_ngram(strVec& s, int freq=1);

    void clear();

    float query_autonomy(strVec& ngram);
    float query_ev(strVec& ngram);
    COUNT query_count(strVec& ngram);
    float query_entropy(strVec& ngram);

    // python interface

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
    void add_sentence_(py::list s, int freq=1)
    {
        add_sentence(strVec{pyStrIt(s), pyStrIt()});
    };
    void add_ngram_(py::list s, int freq=1)
    {
        add_ngram(strVec{pyStrIt(s), pyStrIt()});
    };

};

#endif
