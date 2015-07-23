#ifndef _UNIQUE_LIST_BLOCK_HPP_
#define _UNIQUE_LIST_BLOCK_HPP_

#include "list.hpp"
#include "child_list.hpp"

class SingleChildList: public List
{ 
    /*
     * List of tokens that follows a shingle.
     * ID | META | List& | ID | META | List& | ID | META | List&
    */

    private:
    Node data;

    class SingleChildListIterator: public ListIterator
    {
        private:
        Node& data;
        bool ended;

        public:

        SingleChildListIterator(SingleChildList* b): data(b->data), ended(false)
        {
        }

        void next()
        {
            ended = true;
        };

        Node* get()
        {
            return ended
                ? nullptr
                : &data;
        };
    };


    public:

    SingleChildList(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, COUNT count);

    Node* search_child(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end);

    std::unique_ptr<List> add_shingle(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, COUNT count);

    size_t size() const
    {
        return 1;
    };

    TokenListPair split()
    {
        assert(false);
    };

    std::unique_ptr<ListIterator> begin_childs()
    {
        return std::unique_ptr<SingleChildListIterator>(new SingleChildListIterator(this));
    };

};


#endif
