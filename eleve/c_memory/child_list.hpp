#ifndef _LIST_BLOCK_HPP_
#define _LIST_BLOCK_HPP_

#include "list.hpp"
#include "single_child_list.hpp"
#include "index_list.hpp"

class ChildList: public List
{ 
    friend class SingleChildList;

    /*
     * List of tokens that follows a shingle.
     * ID | META | List& | ID | META | List& | ID | META | List&
    */

    private:
    std::vector<Node> data;

    class ChildListIterator: public ListIterator
    {
        private:
        std::vector<Node>::iterator current_child;
        std::vector<Node>::iterator childs_end;

        public:

        ChildListIterator(ChildList* b)
        {
            childs_end = b->data.end();
            current_child = b->data.begin();
        }

        void next()
        {
            if(current_child != childs_end)
            {
                ++current_child;
            }
        };

        Node* get()
        {
            return (current_child == childs_end)
                ? nullptr
                : &(*current_child);
        };
    };

    ChildList(Node& tb) {data.push_back(std::move(tb));};

    public:

    ChildList() {};

    ChildList(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, const COUNT count);

    Node* search_child(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end);

    std::unique_ptr<List> add_shingle(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, const int count);

    size_t size() const
    {
        return data.size();
    };

    TokenListPair split();

    std::unique_ptr<ListIterator> begin_childs()
    {
        return std::unique_ptr<ChildListIterator>(new ChildListIterator(this));
    };
};

#endif
