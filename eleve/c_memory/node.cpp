#include "node.hpp"
#include "list.hpp"
#include "index_list.hpp"
#include <cmath>

Node::Node(ID token, std::unique_ptr<List> b, COUNT count): m_childs(std::move(b)), m_token(token), m_count(count), m_entropy(INFINITY)
{
};

void Node::add_shingle(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, int count)
{
    m_entropy = INFINITY;
    m_count += count;

    if(! m_childs)
    {
        // case where we are at a leaf
        assert(shingle_it == shingle_end);
        return;
    }

    assert(shingle_it != shingle_end);

    auto r = m_childs->add_shingle(shingle_it, shingle_end, count);
    if(r)
        m_childs = std::move(r);

    if(m_childs->size() > BLOCK_MAX_SIZE)
    {
        // tb is the right part of the splitted list + the token in the middle
        // tb2 is the token in the middle + the left part.
        auto right_part = m_childs->split();
        auto left_part = TokenListPair(right_part.token, std::move(m_childs));
        auto last = std::move(right_part.list);
        m_childs = std::unique_ptr<List>(new IndexList(left_part, last));
    }

};

std::unique_ptr<ListIterator> Node::begin_childs()
{
    if(! m_childs)
    {
        return std::unique_ptr<ListIterator>(new EmptyListIterator());
    }

    return m_childs->begin_childs();
};

Node* Node::search_child(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end)
{
    if(shingle_it == shingle_end)
        return this;

    if(! m_childs)
    {
        // it's a leaf...
        return nullptr;
    }

    return m_childs->search_child(shingle_it, shingle_end);
};

float Node::entropy(HStats& hstats)
{
    if((! m_childs) || (! m_count))
        return NAN;

    if(! isinf(m_entropy))
        return m_entropy;

#ifndef NDEBUG
    COUNT sum_count = 0;
#endif
    float entropy = 0;
    for(auto it = m_childs->begin_childs(); it->get(); it->next())
    {
        Node* node = it->get();
#ifndef NDEBUG
        sum_count += node->count();
#endif
        if(! node->count())
            continue;

        if(hstats.terminals.count(node->token()))
        {
            // terminals are counted only once
            entropy += (node->count() / float(m_count)) * log2f(m_count);
        }
        else
        {
            entropy -= (node->count() / float(m_count)) * log2f(node->count() / float(m_count));
        }
    }
#ifndef NDEBUG
    // integrity of the tree : the counter of a node must be equal to the sum of its childs
    // if it isn't, the entropy computation we just made using m_count is wrong
    assert(m_count == sum_count);
#endif
    assert(entropy >= 0);
    m_entropy = entropy;
    return entropy;
};
