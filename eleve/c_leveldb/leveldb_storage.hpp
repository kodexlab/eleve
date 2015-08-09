#ifndef _LEVELDB_STORAGE_HPP_
#define _LEVELDB_STORAGE_HPP_
#include "leveldb_trie.hpp"

typedef const std::vector<std::string> strVec;

class LeveldbStorage
{
    protected:
    size_t ngram_length;
    LeveldbTrie fwd;
    LeveldbTrie bwd;

    public:

    inline static std::vector<std::string> reverse(const std::vector<std::string>& ids)
    {
        return std::vector<std::string>(ids.rbegin(), ids.rend());
    };
    
    LeveldbStorage(size_t order, std::string path, strVec& terminals): ngram_length(order), fwd(path + "_fwd"), bwd(path + "_bwd")
    {
        std::set<std::string> t = std::set<std::string>(terminals.cbegin(), terminals.cend());
        fwd.set_terminals(t);
        bwd.set_terminals(t);
    };

    LeveldbStorage(size_t o, std::string path = "/tmp/level_trie") : LeveldbStorage(o, path, {"^", "$"}) {};

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
