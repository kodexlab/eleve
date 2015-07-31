#ifndef _NODE_HPP_
#define _NODE_HPP_

#include "entropy.hpp"
#include "config.hpp"

struct List;
class ListIterator;

class __attribute__((packed)) Node
{
    private:
    std::unique_ptr<List> m_childs;
    ID m_token;
    COUNT m_count;
    float m_entropy;

    public:

    Node(ID token, std::unique_ptr<List> b, COUNT count);

    void add_shingle(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, int count=1);

    Node* search_child(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end);

    std::unique_ptr<ListIterator> begin_childs();

    COUNT count() const
    {
        return m_count;
    };

    inline ID token() const
    {
        return m_token;
    };

    float entropy(HStats& hstats);
};

#endif
