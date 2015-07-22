#ifndef _LEAF_BLOCK_HPP_
#define _LEAF_BLOCK_HPP_

#include "block.hpp"

class LeafBlock: public Block
{
    /*
     * DOCID | COUNT | DOCID | COUNT
    */

    private:
    COUNT m_count;

    LeafBlock() {};

    public:

    LeafBlock(COUNT count): m_count(count) {}

    Block* block_for(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end)
    {
        assert(shingle_it == shingle_end);
        return this;
    };

    std::unique_ptr<Block> add_shingle(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, COUNT count);

    TokenBlockPair split();

    size_t size() const
    {
        return 1;
    };

    std::unique_ptr<BlockIterator> begin_childs()
    {
        return std::unique_ptr<EmptyBlockIterator>(new EmptyBlockIterator());
    };

    COUNT count() const
    {
        return m_count;
    }
};

#endif
