#ifndef _UNIQUE_LIST_BLOCK_HPP_
#define _UNIQUE_LIST_BLOCK_HPP_

#include "block.hpp"
#include "list_block.hpp"

class UniqueListBlock: public Block
{ 
    /*
     * List of tokens that follows a shingle.
     * ID | META | Block& | ID | META | Block& | ID | META | Block&
    */

    private:
    TokenBlock data;

    class UniqueListBlockIterator: public BlockIterator
    {
        private:
        TokenBlock& data;
        bool ended;

        public:

        UniqueListBlockIterator(UniqueListBlock* b): data(b->data), ended(false)
        {
        }

        void next()
        {
            ended = true;
        };

        std::pair<ID, Block*> get()
        {
            return ended
                ? std::pair<ID, Block*>(NULL, nullptr)
                : std::pair<ID, Block*>(data.token, data.block.get());
        };
    };


    public:

    UniqueListBlock(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, ShingleInfo& info);

    Block* block_for(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end);

    std::unique_ptr<Block> add_shingle(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, ShingleInfo& info);

    size_t size()
    {
        return 1;
    };

    TokenBlock split()
    {
        assert(false);
    };

    std::unique_ptr<BlockIterator> begin_childs()
    {
        return std::unique_ptr<UniqueListBlockIterator>(new UniqueListBlockIterator(this));
    };

    COUNT count()
    {
        return data.block->count();
    };
};


#endif
