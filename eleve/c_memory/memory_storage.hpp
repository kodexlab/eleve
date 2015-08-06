#ifndef _MEMORY_STORAGE_HPP_
#define _MEMORY_STORAGE_HPP_
#include "memory_trie.hpp"

typedef const std::vector<std::string> strVec;

class MemoryStorage
{
    protected:
    size_t ngram_length;
    MemoryTrie fwd;
    MemoryTrie bwd;
    std::map<std::size_t, std::string> hash_to_token;

    std::vector<ID> tokens_to_ids(strVec& tokens);
    strVec ids_to_tokens(const std::vector<ID>& ids);

    public:

    inline static std::vector<ID> reverse(const std::vector<ID>& ids)
    {
        return std::vector<ID>(ids.rbegin(), ids.rend());
    };
    
    MemoryStorage(size_t order, strVec& terminals): ngram_length(order)
    {
        auto terminals_ids = tokens_to_ids(terminals);
        std::set<ID> t = std::set<ID>(terminals_ids.cbegin(), terminals_ids.cend());
        fwd = MemoryTrie(t);
        bwd = MemoryTrie(t);
    };

    MemoryStorage(size_t o) : MemoryStorage(o, {"^", "$"}) {};

    void add_sentence(std::vector<std::string> s, int freq=1);
    void add_ngram(strVec& s, int freq=1);

    void clear();
    void update_stats();

    float query_autonomy(strVec& ngram);
    float query_ev(strVec& ngram);
    float query_count(strVec& ngram);
    float query_entropy(strVec& ngram);
};

#endif
