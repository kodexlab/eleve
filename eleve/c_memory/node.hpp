#ifndef _NODE_HPP_
#define _NODE_HPP_

#include "entropy.hpp"
#include "config.hpp"

struct List;

class __attribute__((packed)) Node
{
    private:
    std::unique_ptr<List> m_list;
    ID m_token;
    COUNT m_count;

    public:

    Node(ID token, std::unique_ptr<List> b, COUNT count): m_list(std::move(b)), m_token(token), m_count(count) {};

    void add_shingle(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, COUNT count=1);

    Node* search_child(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end);

    COUNT count() const
    {
        return m_count;
    };

    COUNT set_count(COUNT count)
    {
        m_count = count;
    };

    inline ID token() const
    {
        return m_token;
    };

    float entropy(HStats& hstats) const;
};

#endif
