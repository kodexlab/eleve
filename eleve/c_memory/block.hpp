#ifndef _BLOCK_HPP_
#define _BLOCK_HPP_

#include <vector>
#include <memory>
#include <assert.h>
#include <map>
#include <iostream>
#include <algorithm>

struct Block;
struct TokenBlock;

const size_t BLOCK_MAX_SIZE = 128;

typedef uint32_t ID;
typedef uint32_t COUNT;
typedef std::vector<ID>::const_iterator shingle_const_iterator;

struct ShingleInfo
{
    ID docid;
    COUNT count;

    ShingleInfo(ID d, COUNT c): docid(d), count(c) {};
    ShingleInfo(const ShingleInfo& other): docid(other.docid), count(other.count) {};
};

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
    virtual std::unique_ptr<Block> add_shingle(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, ShingleInfo& info) = 0;
    virtual TokenBlock split() = 0;
    virtual size_t size() = 0;

    virtual Block* block_for(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end) = 0;
    virtual std::unique_ptr<BlockIterator> begin_childs() = 0;

    virtual COUNT count() = 0;
    //virtual std::map<ID, COUNT> postings();
};

struct __attribute__((packed)) TokenBlock
{
    std::unique_ptr<Block> block;
    ID token;

    TokenBlock(ID t, std::unique_ptr<Block> b): block(std::move(b)), token(t) {};
};

#endif
