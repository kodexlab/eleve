#ifndef _LEVELDBTRIE_HPP_
#define _LEVELDBTRIE_HPP_

#include "config.hpp"
#include "leveldb_node.hpp"
#include <iostream>

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

    inline void check_dirty()
    {
        if(dirty)
            update_stats();
    };

    public:

    LeveldbTrie(const std::string& path = "/tmp/test_trie") : dirty(false)
    {
        leveldb::Options options;
        options.create_if_missing = true;
        options.write_buffer_size = 64*1024*1024;
        //options.block_size = 16*1024;

        auto status = leveldb::DB::Open(options, path, &db);
        if(! status.ok())
        {
            std::cerr << "Unable to open the database at " << path << ": " << status.ToString() << std::endl;
            exit(EXIT_FAILURE);
        }
    };

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
