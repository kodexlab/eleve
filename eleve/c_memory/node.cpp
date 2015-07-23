#include "node.hpp"
#include "list.hpp"
#include "index_list.hpp"
#include <cmath>

Node::Node(ID token, std::unique_ptr<List> b, COUNT count): m_list(std::move(b)), m_token(token), m_count(count)
{
};

void Node::add_shingle(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, COUNT count)
{
    m_count += count;

    if(! m_list)
    {
        // case where we are at a leaf
        assert(shingle_it == shingle_end);
        return;
    }

    assert(shingle_it != shingle_end);

    auto r = m_list->add_shingle(shingle_it, shingle_end, count);
    if(r)
        m_list = std::move(r);

    if(m_list->size() > BLOCK_MAX_SIZE)
    {
        // tb is the right part of the splitted list + the token in the middle
        // tb2 is the token in the middle + the left part.
        auto tb = m_list->split();
        auto tb2 = TokenListPair(m_token, std::move(m_list));
        auto last = std::move(tb.list);
        m_list = std::unique_ptr<List>(new IndexList(tb2, last));
    }

};

std::unique_ptr<ListIterator> Node::begin_childs()
{
    if(! m_list)
    {
        return std::unique_ptr<ListIterator>(new EmptyListIterator());
    }

    return m_list->begin_childs();
};

Node* Node::search_child(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end)
{
    if(shingle_it == shingle_end)
        return this;

    if(! m_list)
    {
        // it's a leaf...
        return nullptr;
    }

    return m_list->search_child(shingle_it, shingle_end);
};

float Node::entropy(HStats& hstats) const
{
    if((! m_list) || (! m_count))
        return NAN;

#ifndef NDEBUG
    COUNT sum_count = 0;
#endif
    float entropy = 0;
    for(auto it = m_list->begin_childs(); it->get(); it->next())
    {
        Node* node = it->get();
#ifndef NDEBUG
        sum_count += node->count();
#endif
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
    return entropy;
};
