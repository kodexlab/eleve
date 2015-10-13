#include "index_list.hpp"

void IndexList::IndexListIterator::next()
{
    current_child_iterator->next();
    if(current_child_iterator->get() == nullptr && index_list != nullptr)
    {
        current_child++;
        if(current_child == index_list->data.end())
        {
            current_child_iterator = index_list->last->begin_childs();
            index_list = nullptr;
        }
        else
        {
            current_child_iterator = current_child->list->begin_childs();
        }
    }
};

TokenListPair IndexList::split()
{
    size_t new_size = data.size() / 2;
    auto token = data[new_size].token;
    auto other = std::unique_ptr<IndexList>(new IndexList(std::move(last)));
    last = std::move(data[new_size].list);
    for(auto it = data.begin() + new_size + 1; it != data.end(); ++it)
    {
        other->data.push_back(std::move(*it));
    }
    data.erase(data.begin() + new_size, data.end());
    return TokenListPair(token, std::move(other));
};

std::unique_ptr<List> IndexList::add_shingle(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, const int count)
{
    assert(shingle_it != shingle_end);

    auto it = std::lower_bound(data.begin(), data.end(), *shingle_it, [](TokenListPair& a, ID t) {return a.token < t;});
    assert(it == data.end() || it->token >= *shingle_it);

    std::unique_ptr<List> b;
    if(it == data.end())
    {
        b = last->add_shingle(shingle_it, shingle_end, count);
        if(b)
            last = std::move(b);

        if(last->size() > BLOCK_MAX_SIZE)
        {
            auto right_part = last->split();
            auto left_part = TokenListPair(right_part.token, std::move(last));
            data.push_back(std::move(left_part));
            last = std::move(right_part.list);
        }
    }
    else
    {
        b = it->list->add_shingle(shingle_it, shingle_end, count);
        if(b)
            it->list = std::move(b);

        if(it->list->size() > BLOCK_MAX_SIZE)
        {
            auto right_part = it->list->split();
            auto left_token = it->token;
            it->token = right_part.token;
            auto new_right_part = TokenListPair(left_token, std::move(right_part.list));
            data.insert(it + 1, std::move(new_right_part));
        }
    }

    return nullptr;
};

