#include "leaf_block.hpp"

std::unique_ptr<Block> LeafBlock::add_shingle(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, ShingleInfo& info)
{
    assert(shingle_it == shingle_end);

    auto it = std::lower_bound(data.begin(), data.end(), info.docid, [](ShingleInfo& a, ID t) {return a.docid < t;});
    // it->token >= token
    
    if(it->docid == info.docid)
    {
        it->count += info.count;
    }
    else
    {
        it = data.insert(it, info);
    }

    return nullptr;
};

TokenBlock LeafBlock::split()
{
    size_t new_size = data.size() / 2;
    auto token = data[new_size].docid;
    auto other = std::unique_ptr<LeafBlock>(new LeafBlock());
    for(auto it = data.begin() + new_size + 1; it != data.end(); ++it)
    {
        other->data.push_back(std::move(*it));
    }
    data.erase(data.begin() + new_size, data.end());
    return TokenBlock(token, std::move(other));
};

COUNT LeafBlock::count()
{
    COUNT c = 0;
    for(auto it = data.begin(); it != data.end(); ++it)
    {
        c += it->count;
    }
    return c;
};
