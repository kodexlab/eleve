#ifndef _INDEX_BLOCK_HPP_
#define _INDEX_BLOCK_HPP_

#include "list.hpp"

class IndexList: public List
{
    /*
     * List* | ID | List* | ID | List*
     * (List* | ID) | (List* | ID) | List*
    */

    private:
    std::unique_ptr<List> last;
    std::vector<TokenListPair> data;

    IndexList() {};

    class IndexListIterator: public ListIterator
    {
        private:
        IndexList* index_list;
        std::unique_ptr<ListIterator> current_child_iterator;
        std::vector<TokenListPair>::iterator current_child;

        public:

        IndexListIterator(IndexList* b): index_list(b)
        {
            current_child = b->data.begin();
            current_child_iterator = current_child->list->begin_childs();
        }

        IndexListIterator(const IndexListIterator&) = delete;

        void next()
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
                    current_child_iterator = current_child->list->begin_childs();
            }
        };

        Node* get()
        {
            return current_child_iterator->get();
        };
    };

    public:

    IndexList(TokenListPair& b1, std::unique_ptr<List>& b2)
    {
        last = std::move(b2);
        data.push_back(std::move(b1));
    }

    std::unique_ptr<ListIterator> begin_childs()
    {
        return std::unique_ptr<IndexListIterator>(new IndexListIterator(this));
    };

    TokenListPair split()
    {
        // (List* | ID) | List*
        size_t new_size = data.size() / 2;
        auto token = data[new_size].token;
        auto other = std::unique_ptr<IndexList>(new IndexList());
        other->last = std::move(last);
        last = std::move(data[new_size].list);
        for(auto it = data.begin() + new_size; it != data.end(); ++it)
        {
            other->data.push_back(std::move(*it));
        }
        data.erase(data.begin() + new_size, data.end());
        return TokenListPair(token, std::move(other));
    }

    std::unique_ptr<List> add_shingle(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, int count)
    {
        assert(shingle_it != shingle_end);

        auto it = std::lower_bound(data.begin(), data.end(), *shingle_it, [](TokenListPair& a, ID t) {return a.token < t;});
        // it->token >= token

        std::unique_ptr<List> b;
        if(it == data.end())
        {
            b = last->add_shingle(shingle_it, shingle_end, count);
            if(b)
                last = std::move(b);
        }
        else
        {
            b = it->list->add_shingle(shingle_it, shingle_end, count);
            if(b)
                it->list = std::move(b);
        }

        if((it == data.end() ? last->size() : it->list->size()) > BLOCK_MAX_SIZE)
        {
            if(it == data.end())
            {
                auto tb = last->split();
                auto tb2 = TokenListPair(tb.token, std::move(last));
                data.push_back(std::move(tb2));
                last = std::move(tb.list);
            }
            else
            {
                auto tb = it->list->split();
                auto left_token = it->token;
                it->token = tb.token;
                ++it;
                auto tb2 = TokenListPair(left_token, std::move(tb.list));
                data.insert(it, std::move(tb2));
            }
        }

        return nullptr;
    }

    Node* search_child(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end)
    {
        auto it = data.begin();
        while(it != data.end() && *shingle_it > it->token)
        {
            ++it;
        }
        if(it == data.end())
        {
            return last->search_child(shingle_it, shingle_end);
        }
        return it->list->search_child(shingle_it, shingle_end);
    }

    size_t size() const
    {
        return data.size() + 1;
    };

};

#endif
