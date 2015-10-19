#include "memory_trie.hpp"

#include <cmath>

size_t MemoryTrie::max_depth()
{
    if(dirty) update_stats();
    return hstats.normalization.size();
}

void MemoryTrie::update_stats_rec(float parent_entropy, int depth, Node* node)
{
    float entropy = node->entropy(hstats);

    if(hstats.normalization.size() < depth)
    {
        hstats.normalization.resize(depth);
    }

    if(depth > 0 && !isnan(entropy) && (entropy != 0. || parent_entropy != 0.))
    {
        float ev = entropy - parent_entropy;

        // entropy variation to take into account
        auto& normalization = hstats.normalization[depth-1];
        auto old_mean = normalization.mean;
        normalization.count++;

        normalization.mean += (ev - old_mean) / normalization.count;
        normalization.stdev += (ev - old_mean)*(ev - normalization.mean);
    }

#ifndef NDEBUG
    int64_t old_token = -1;
#endif
    for(auto it = node->begin_childs(); it->get(); it->next())
    {
#ifndef NDEBUG
        assert(it->get()->token() > old_token);
        old_token = it->get()->token();
#endif
        update_stats_rec(entropy, depth + 1, it->get());
    }
};

void MemoryTrie::update_stats()
{
    // clean the normalization structure
    hstats.normalization.clear();

    // fill it
    update_stats_rec(NAN, 0, &root);

    // calculate the standard deviation given the partial sum
    for(auto& i: hstats.normalization)
    {
        i.stdev = sqrtf(i.stdev / float(i.count ? i.count : 1));
    }

    dirty = false;
};

void MemoryTrie::add_ngram(const std::vector<ID>& shingle, int freq)
{
    if(freq == 0 || shingle.cbegin() == shingle.cend())
        return;

    dirty = true;
    root.add_shingle(shingle.begin(), shingle.end(), freq);
};

COUNT MemoryTrie::query_count(const std::vector<ID>& shingle)
{

    Node* n = root.search_child(shingle.cbegin(), shingle.cend());
    if(! n)
    {
        return 0;
    }
    return n->count();
};

float MemoryTrie::query_entropy(const std::vector<ID>& shingle)
{
    /* TODO: Remove
    std::cerr << "ENTROPY" << std::endl;
    for(auto it = root.begin_childs(); it->get(); it->next())
    {
        std::cerr << it->get()->token() << " " << it->get()->count() << std::endl;
    };
    */

    Node* n = root.search_child(shingle.cbegin(), shingle.cend());
    if(! n)
    {
        return NAN;
    }
    return n->entropy(hstats);
};

float MemoryTrie::query_ev(const std::vector<ID>& shingle)
{
    if(! shingle.size())
        return NAN;

    Node* parent = root.search_child(shingle.cbegin(), shingle.cend() - 1);
    if(! parent)
        return NAN;
    Node* child = parent->search_child(shingle.cend() - 1, shingle.cend());
    if(! child)
        return NAN;
    assert(parent != child);
    float parent_entropy = parent->entropy(hstats);
    assert(! isnan(parent_entropy));
    float entropy = child->entropy(hstats);

    if((! isnan(entropy)) && (entropy != 0. || parent_entropy != 0.))
        return entropy - parent_entropy;
    return NAN;
};

float MemoryTrie::query_autonomy(const std::vector<ID>& shingle)
{
    if(dirty)
        update_stats();

    float ev = query_ev(shingle);
    if(isnan(ev))
        return NAN;

    auto& n = hstats.normalization[shingle.size()-1];
    return (ev - n.mean) / n.stdev;
};

void MemoryTrie::clear()
{
    dirty = true;
    root = Node(0, std::unique_ptr<ChildList>(new ChildList()), 0);
};
