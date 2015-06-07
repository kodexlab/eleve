#ifndef _LEAF_BLOCK_HPP_
#define _LEAF_BLOCK_HPP_

#include "block.hpp"

class LeafBlock: public Block
{
    /*
     * DOCID | COUNT | DOCID | COUNT
    */

    private:
    std::vector<ShingleInfo> data;

    LeafBlock() {};

    public:

    LeafBlock(ShingleInfo& info)
    {
        data.push_back(info);
    }

    Block* block_for(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end)
    {
        assert(shingle_it == shingle_end);
        return this;
    };

    std::unique_ptr<Block> add_shingle(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, ShingleInfo& info);

    TokenBlock split();

    size_t size()
    {
        return data.size();
    };

    std::unique_ptr<BlockIterator> begin_childs()
    {
        return std::unique_ptr<EmptyBlockIterator>(new EmptyBlockIterator());
    };

    COUNT count();
};

#endif
