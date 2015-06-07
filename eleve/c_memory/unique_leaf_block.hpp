#ifndef _UNIQUE_LEAF_BLOCK_HPP
#define _UNIQUE_LEAF_BLOCK_HPP

#include "block.hpp"
#include "leaf_block.hpp"

class UniqueLeafBlock: public Block
{
    private:
    ShingleInfo data;

    public:

    UniqueLeafBlock(ShingleInfo& info): data(info)
    {
    }

    Block* block_for(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end)
    {
        assert(shingle_it == shingle_end);
        return this;
    };

    std::unique_ptr<Block> add_shingle(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, ShingleInfo& info)
    {
        assert(shingle_it == shingle_end);

        if(info.docid == data.docid)
        {
            data.count += info.count;
            return nullptr;
        }

        std::unique_ptr<Block> b = std::unique_ptr<Block>(new LeafBlock(data));
        b->add_shingle(shingle_it, shingle_end, info);

        return std::move(b);
    };

    TokenBlock split()
    {
        assert(false);
    };

    size_t size()
    {
        return 1;
    };

    std::unique_ptr<BlockIterator> begin_childs()
    {
        return std::unique_ptr<EmptyBlockIterator>(new EmptyBlockIterator());
    };

    COUNT count()
    {
        return data.count;
    };

};

#endif
