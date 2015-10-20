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

        IndexList(std::unique_ptr<List> l): last(std::move(l))
        {
            assert(last);
        };

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

                void next();

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
        };

        std::unique_ptr<ListIterator> begin_childs()
        {
            return std::unique_ptr<IndexListIterator>(new IndexListIterator(this));
        };

        TokenListPair split();

        std::unique_ptr<List> add_shingle(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, const int count);

        Node* search_child(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end)
        {
            auto it = std::lower_bound(data.begin(), data.end(), *shingle_it, [](TokenListPair& a, ID t) {return a.token < t;});
            assert(it == data.end() || it->token >= *shingle_it);

            return (it == data.end() ? last : it->list)->search_child(shingle_it, shingle_end);
        };

        size_t size() const { return data.size() + 1; };

};

#endif
