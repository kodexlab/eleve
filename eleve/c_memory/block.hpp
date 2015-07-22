#ifndef _BLOCK_HPP_
#define _BLOCK_HPP_

#include <vector>
#include <memory>
#include <assert.h>
#include <map>
#include <iostream>
#include <algorithm>

struct Block;
struct TokenBlockPair;

const size_t BLOCK_MAX_SIZE = 128;

typedef uint32_t ID;
typedef uint32_t COUNT;
typedef std::vector<ID>::const_iterator shingle_const_iterator;

class BlockIterator
{
    public:
    virtual void next() = 0;
    virtual std::pair<ID, Block*> get() = 0;
};

class EmptyBlockIterator : public BlockIterator
{
    public:
    void next() {};
    std::pair<ID, Block*> get() { return std::pair<ID, Block*>(NULL, nullptr); };
};

struct Block
{
    // Recursive function used to add the occurence of a shingle
    virtual std::unique_ptr<Block> add_shingle(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, COUNT count=1) = 0;

    // To split the block in two, modifying it and returning a new one
    virtual TokenBlockPair split() = 0;
    // Get the size of the internal list, for calling split() if its too big
    virtual size_t size() const = 0;

    // Get the number of childs
    virtual COUNT count() const = 0;

    // Search for a sub-block
    virtual Block* block_for(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end) = 0;

    // Iterator to the childs
    virtual std::unique_ptr<BlockIterator> begin_childs() = 0;
};

struct __attribute__((packed)) TokenBlockPair
{
    std::unique_ptr<Block> block;
    ID token;

    TokenBlockPair(ID t, std::unique_ptr<Block> b): block(std::move(b)), token(t) {};
};

#endif
