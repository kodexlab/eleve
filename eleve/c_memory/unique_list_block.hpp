#ifndef _UNIQUE_LIST_BLOCK_HPP_
#define _UNIQUE_LIST_BLOCK_HPP_

#include "block.hpp"
#include "list_block.hpp"
#include "leaf_block.hpp"

class UniqueListBlock: public Block
{ 
    /*
     * List of tokens that follows a shingle.
     * ID | META | Block& | ID | META | Block& | ID | META | Block&
    */

    private:
    TokenBlockPair data;

    class UniqueListBlockIterator: public BlockIterator
    {
        private:
        TokenBlockPair& data;
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

    UniqueListBlock(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, COUNT count);

    Block* block_for(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end);

    std::unique_ptr<Block> add_shingle(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, COUNT count);

    size_t size() const
    {
        return 1;
    };

    TokenBlockPair split()
    {
        assert(false);
    };

    std::unique_ptr<BlockIterator> begin_childs()
    {
        return std::unique_ptr<UniqueListBlockIterator>(new UniqueListBlockIterator(this));
    };

    COUNT count() const
    {
        return data.block->count();
    };
};


#endif
