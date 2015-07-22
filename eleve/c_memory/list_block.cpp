#include "list_block.hpp"

ListBlock::ListBlock(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, COUNT count)
{
    auto token = *shingle_it;
    ++shingle_it;

    std::unique_ptr<Block> block;
    if(shingle_end == shingle_it)
    {
        block = std::unique_ptr<Block>(new LeafBlock(count));
    }
    else
    {
        block = std::unique_ptr<Block>(new UniqueListBlock(shingle_it, shingle_end, count));
    }

    data.push_back(TokenBlockPair(token, std::move(block)));
};

Block* ListBlock::block_for(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end)
{
    if(shingle_it == shingle_end)
        return this;

    auto it = data.begin();
    while(it != data.end() && it->token != *shingle_it)
    {
        ++it;
    }
    if(it == data.end())
        return nullptr;

    return (it->block)->block_for(++shingle_it, shingle_end);
};

std::unique_ptr<Block> ListBlock::add_shingle(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, COUNT count)
{
    assert(shingle_it != shingle_end);

    auto token = *shingle_it;

    auto it = std::lower_bound(data.begin(), data.end(), token, [](TokenBlockPair& a, ID t) {return a.token < t;});
    // it->token >= token

    if(it != data.end() && it->token == token)
    {
        // the token exists, add it recursively
        auto b = it->block->add_shingle(++shingle_it, shingle_end, count);
        if(b)
            it->block = std::move(b);
    }
    else
    {
        // let's create the token
        ++shingle_it;
        std::unique_ptr<Block> new_block;
        if(shingle_it == shingle_end)
        {
            new_block = std::unique_ptr<Block>(new LeafBlock(count));
        }
        else
        {
            new_block = std::unique_ptr<Block>(new UniqueListBlock(shingle_it, shingle_end, count));
        }
        it = data.insert(it, TokenBlockPair(token, std::move(new_block)));
    }

    if(it->block->size() > BLOCK_MAX_SIZE)
    {
        // tb is the right part of the splitted block + the token in the middle
        // tb2 is the token in the middle + the left part.
        auto tb = it->block->split();
        auto tb2 = TokenBlockPair(tb.token, std::move(it->block));
        auto last = std::move(tb.block);
        it->block = std::unique_ptr<Block>(new IndexBlock(tb2, last));
    }

    return nullptr;
};

TokenBlockPair ListBlock::split()
{
    size_t new_size = data.size() / 2;
    auto token = data[new_size].token;
    auto other = std::unique_ptr<ListBlock>(new ListBlock());
    for(auto it = data.begin() + new_size + 1; it != data.end(); ++it)
    {
        other->data.push_back(std::move(*it));
    }
    data.erase(data.begin() + new_size, data.end());
    return TokenBlockPair(token, std::move(other));
};

COUNT ListBlock::count() const
{
    COUNT c = 0;
    for(auto it = data.begin(); it != data.end(); ++it)
    {
        c += it->block->count();
    }
    return c;
};
