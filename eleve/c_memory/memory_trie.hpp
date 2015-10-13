#ifndef _MEMORYTRIE_HPP_
#define _MEMORYTRIE_HPP_

#include "node.hpp"
#include "child_list.hpp"
#include "entropy.hpp"

class MemoryTrie
{
    protected:

    Node root;
    HStats hstats;
    bool dirty;

    void update_stats_rec(float parent_entropy, int depth, Node* node);

    public:

    MemoryTrie() : root(0, std::unique_ptr<ChildList>(new ChildList()), 0), dirty(true)
    {
    };

    MemoryTrie(const std::set<ID>& terminals) : MemoryTrie()
    {
        hstats = HStats(terminals);
    };

    void update_stats();

    void add_ngram(const std::vector<ID>& shingle, int freq=1);

    COUNT query_count(const std::vector<ID>& shingle);
    float query_entropy(const std::vector<ID>& shingle);
    float query_ev(const std::vector<ID>& shingle);
    float query_autonomy(const std::vector<ID>& shingle);

    void clear();
};

#endif
