#include "node.hpp"
#include "list.hpp"
#include "index_list.hpp"

void Node::add_shingle(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, COUNT count)
{
    if(! m_list)
    {
        // case where we are at a leaf
        assert(shingle_it == shingle_end);
        m_count += count;
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

Node* Node::search_child(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end)
{
    if(! m_list)
    {
        // it's a leaf...
        return (shingle_it == shingle_end) ? this : nullptr;
    }

    return m_list->search_child(shingle_it, shingle_end);
};

float Node::entropy(HStats& hstats) const
{
    for(auto it = m_list->begin_childs(); it->get() != nullptr; it->next())
    {
    }
    return 0.;
};
