#include "leaf_block.hpp"

std::unique_ptr<Block> LeafBlock::add_shingle(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, COUNT count)
{
    assert(shingle_it == shingle_end);

    m_count += count;

    return nullptr;
};

TokenBlockPair LeafBlock::split()
{
    assert(0);
};
