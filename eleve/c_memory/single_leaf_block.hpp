#ifndef _SINGLE_LEAF_BLOCK_HPP
#define _SINGLE_LEAF_BLOCK_HPP

#include "block.hpp"
#include "leaf_block.hpp"

class SingleLeafBlock: public Block
{
    private:
    ID data;

    public:

    SingleLeafBlock(ShingleInfo& info): data(info.docid)
    {
        assert(info.count == 1);
    }

    Block* block_for(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end)
    {
        assert(shingle_it == shingle_end);
        return this;
    };

    std::unique_ptr<Block> add_shingle(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, ShingleInfo& info)
    {
        assert(shingle_it == shingle_end);

        std::unique_ptr<Block> b;
        auto this_info = ShingleInfo(data, 1);
        if(info.docid == data)
        {
            b = std::unique_ptr<Block>(new UniqueLeafBlock(this_info));
        }
        else
        {
            b = std::unique_ptr<Block>(new LeafBlock(this_info));
        }

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
        return 1;
    };

};

#endif
