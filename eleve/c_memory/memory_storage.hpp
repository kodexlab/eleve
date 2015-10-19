#ifndef _MEMORY_STORAGE_HPP_
#define _MEMORY_STORAGE_HPP_
#include "memory_trie.hpp"
#include <unordered_map>

typedef const std::vector<std::string> strVec;

class MemoryStorage
{
    protected:
    size_t default_ngram_length;
    std::string sentence_start = "^";
    std::string sentence_end = "$";
    MemoryTrie fwd;
    MemoryTrie bwd;
    std::unordered_map<std::size_t, std::string> hash_to_token;

    std::vector<ID> tokens_to_ids(strVec& tokens);
    strVec ids_to_tokens(const std::vector<ID>& ids);

    public:

    MemoryStorage(size_t default_ngram_length = 5);

    inline static std::vector<ID> reverse(const std::vector<ID>& ids)
    {
        return std::vector<ID>(ids.rbegin(), ids.rend());
    };

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
