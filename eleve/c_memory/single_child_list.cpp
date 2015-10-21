#include "single_child_list.hpp"

SingleChildList::SingleChildList(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, COUNT count): data(Node(0, nullptr, 0))
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

    data = Node(token, std::move(list), count);
};

Node* SingleChildList::search_child(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end)
{
    assert(shingle_it != shingle_end);

    if(data.token() != *shingle_it)
    {
        return nullptr;
    }
    else
    {
        return data.search_child(++shingle_it, shingle_end);
    }
};

std::unique_ptr<List> SingleChildList::add_shingle(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, int count)
{
    assert(shingle_it != shingle_end);

    auto token = *shingle_it;

    // Same uniq token, just do recursidf call
    if(data.token() == token)
    {
        // the token exists, add it recursively
        data.add_shingle(++shingle_it, shingle_end, count);
        return nullptr;
    }
    else
    {
        // Node need to be adder : we will replace itself with a ChildList:
        std::unique_ptr<List> new_list = std::unique_ptr<List>(new ChildList(data));
        new_list->add_shingle(shingle_it, shingle_end, count);
        return std::move(new_list);
    }
};

