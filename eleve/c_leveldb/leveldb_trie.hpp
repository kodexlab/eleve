#ifndef _LEVELDBTRIE_HPP_
#define _LEVELDBTRIE_HPP_

#include "config.hpp"
#include "leveldb_node.hpp"
#include <iostream>
#include <array>

const std::string DEFAULT_PATH = "/tmp/level_trie";

struct Normalization
{
    float mean;
    float stdev;
    COUNT count;
};

class LeveldbTrie
{
    protected:

    std::vector<Normalization> normalization;
    std::set<std::string> terminals;
    bool dirty;
    leveldb::DB* db;

    Node search_node(const std::vector<std::string>& ngram)
    {
        std::string key;
        key.push_back(ngram.size());
        for(auto& s : ngram)
        {
            key.push_back(0);
            key += s;
        }
        return Node(db, key);
    };

    void update_stats_rec(float parent_entropy, size_t depth, Node& node);

    inline void set_dirty()
    {
        if(! dirty)
        {
            std::array<char, 2> key;
            key[0] = 0xff;
            key[1] = 0;
            db->Delete(write_options, leveldb::Slice(key.data(), 2));

            dirty = true;
        }
    };

    inline void set_clean()
    {
        if(dirty)
        {
            update_stats();
        }
    };

    public:

    LeveldbTrie(const std::string& path = DEFAULT_PATH);

    LeveldbTrie(const std::string& path, const std::set<std::string>& terms) : LeveldbTrie(path)
    {
        terminals = terms;
    };

    ~LeveldbTrie()
    {
        delete db;
    };

    void set_terminals(std::set<std::string>& t)
    {
        terminals = t;
    };

    void update_stats();

    void add_ngram(const std::vector<std::string>& ngram, int freq=1);

    COUNT query_count(const std::vector<std::string>& ngram);
    float query_entropy(const std::vector<std::string>& ngram);
    float query_ev(const std::vector<std::string>& ngram);
    float query_autonomy(const std::vector<std::string>& ngram);

    void clear();
};

#endif
