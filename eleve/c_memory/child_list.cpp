#include "child_list.hpp"

ChildList::ChildList(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, COUNT count)
{
    auto token = *shingle_it;
    ++shingle_it;

    std::unique_ptr<List> list;
    if(shingle_end == shingle_it)
    {
        list = nullptr;
    }
    else
    {
        list = std::unique_ptr<List>(new SingleChildList(shingle_it, shingle_end, count));
    }

    data.push_back(Node(token, std::move(list), count));
};

Node* ChildList::search_child(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end)
{
    assert(shingle_it != shingle_end);

    auto it = data.begin();
    while(it != data.end() && it->token() != *shingle_it)
    {
        ++it;
    }
    if(it == data.end())
        return nullptr;

    return it->search_child(shingle_it + 1, shingle_end);
};

std::unique_ptr<List> ChildList::add_shingle(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, COUNT count)
{
    assert(shingle_it != shingle_end);

    auto token = *shingle_it;

    auto it = std::lower_bound(data.begin(), data.end(), token, [](Node& a, ID t) {return a.token() < t;});
    // it->token >= token

    if(it != data.end() && it->token() == token)
    {
        // the token exists, add it recursively
        it->add_shingle(++shingle_it, shingle_end, count);
    }
    else
    {
        // let's create the token
        ++shingle_it;
        std::unique_ptr<List> new_list;
        if(shingle_it == shingle_end)
        {
            new_list = nullptr;
        }
        else
        {
            new_list = std::unique_ptr<List>(new SingleChildList(shingle_it, shingle_end, count));
        }
        it = data.insert(it, Node(token, std::move(new_list), count));
    }

    return nullptr;
};

TokenListPair ChildList::split()
{
    size_t new_size = data.size() / 2;
    auto token = data[new_size].token();
    auto other = std::unique_ptr<ChildList>(new ChildList());
    for(auto it = data.begin() + new_size; it != data.end(); ++it)
    {
        other->data.push_back(std::move(*it));
    }
    data.erase(data.begin() + new_size, data.end());
    return TokenListPair(token, std::move(other));
};
