#include "unique_list_block.hpp"

UniqueListBlock::UniqueListBlock(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, ShingleInfo& info): data(TokenBlock(0, nullptr))
{
    auto token = *shingle_it;
    ++shingle_it;

    std::unique_ptr<Block> block;
    if(shingle_end == shingle_it)
    {
        block = std::unique_ptr<Block>(new UniqueLeafBlock(info));
    }
    else
    {
        block = std::unique_ptr<Block>(new UniqueListBlock(shingle_it, shingle_end, info));
    }

    data = TokenBlock(token, std::move(block));
};

Block* UniqueListBlock::block_for(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end)
{
    if(shingle_it == shingle_end)
    {
        return this;
    }
    else if(data.token != *shingle_it)
    {
        return nullptr;
    }
    else
    {
        return data.block->block_for(++shingle_it, shingle_end);
    }
};

std::unique_ptr<Block> UniqueListBlock::add_shingle(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, ShingleInfo& info)
{
    assert(shingle_it != shingle_end);

    auto token = *shingle_it;

    if(data.token == token)
    {
        // the token exists, add it recursively
        auto b = data.block->add_shingle(++shingle_it, shingle_end, info);
        if(b)
        {
            data.block = std::move(b);
        }

        if(data.block->size() > BLOCK_MAX_SIZE)
        {
            // tb is the right part of the splitted block + the token in the middle
            // tb2 is the token in the middle + the left part.
            auto tb = data.block->split();
            auto tb2 = TokenBlock(tb.token, std::move(data.block));
            auto last = std::move(tb.block);
            data.block = std::unique_ptr<Block>(new IndexBlock(tb2, last));
        }

        return nullptr;
    }

    std::unique_ptr<Block> b = std::unique_ptr<Block>(new ListBlock(data));
    b->add_shingle(shingle_it, shingle_end, info);

    return std::move(b);
};

