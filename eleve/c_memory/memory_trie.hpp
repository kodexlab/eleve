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

    void update_stats();

    void add_ngram(std::vector<ID> shingle, int freq);

    COUNT query_count(std::vector<ID> shingle);
    float query_entropy(std::vector<ID> shingle);
    float query_ev(std::vector<ID> shingle);

    void clear();
    float query_autonomy(std::vector<ID> shingle);
};

#endif
