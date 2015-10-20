#ifndef _LEVELDBTRIE_HPP_
#define _LEVELDBTRIE_HPP_

#include "config.hpp"
#include "leveldb_node.hpp"
#include <iostream>
#include <array>

struct Normalization
{
    float mean;
    float stdev;
    COUNT count;
};

class LeveldbTrie
{
    protected:
        std::string path;
        std::vector<Normalization> normalization;
        std::set<std::string> terminals;
        bool dirty;
        leveldb::DB* db;

        Node search_node(const std::vector<std::string>& ngram);
        void update_stats_rec(float parent_entropy, size_t depth, Node& node);
        inline void set_dirty();
        inline void set_clean();

    public:
        LeveldbTrie(const std::string& path);
        LeveldbTrie(const std::string& path, const std::set<std::string>& terms) : LeveldbTrie(path)
        {
            terminals = terms;
        };

        ~LeveldbTrie()
        {
            close();
        };

        void update_stats();

        void add_ngram(const std::vector<std::string>& ngram, int freq=1);

        size_t max_depth();
        COUNT query_count(const std::vector<std::string>& ngram);
        float query_entropy(const std::vector<std::string>& ngram);
        float query_ev(const std::vector<std::string>& ngram);
        float query_autonomy(const std::vector<std::string>& ngram);

        void clear();
        void close();
};

#endif
