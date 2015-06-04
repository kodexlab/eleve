#include <vector>
#include <memory>
#include <assert.h>
#include <map>

const size_t BLOCK_MAX_SIZE = 100;

typedef unsigned int ID;
typedef unsigned int COUNT;
typedef std::vector<ID>::const_iterator shingle_const_iterator;

class LeafBlock;
class ListBlock;
struct TokenBlock;

struct ShingleInfo
{
    ID docid;
    COUNT count;

    ShingleInfo(ID d, COUNT c): docid(d), count(c) {};
};

struct Block
{
    virtual void add_shingle(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, ShingleInfo& info) = 0;
    virtual TokenBlock split() = 0;
    virtual size_t size() = 0;

    virtual Block* block_for(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end) = 0;
    virtual ListBlock::iterator begin_childs() = 0;
    virtual ListBlock::iterator end_childs() = 0;
    /*virtual LeafBlock::iterator begin_leafs() = 0;
    virtual LeafBlock::iterator end_leafs() = 0;
    virtual ShingleInfo::iterator begin_postings() = 0;
    virtual ShingleInfo::iterator end_postings() = 0;*/

    virtual COUNT count();
    virtual size_t doc_count(); // std::map or hyperloglog
    virtual std::map<ID, COUNT> postings();
    virtual float entropy();
};

struct TokenBlock
{
    ID token;
    std::unique_ptr<Block> block;

    TokenBlock(ID t, std::unique_ptr<Block> b): token(t), block(std::move(b)) {};
};

class IndexBlock: public Block
{
    /*
     * Block* | ID | Block* | ID | Block*
     * (Block* | ID) | (Block* | ID) | Block*
    */

    private:
    std::unique_ptr<Block> last;
    std::vector<TokenBlock> data;

    IndexBlock() {};

    public:

    IndexBlock(TokenBlock& b1, std::unique_ptr<Block>& b2)
    {
        last = std::move(b2);
        data.push_back(b1);
    }

    TokenBlock split()
    {
        // (Block* | ID) | Block*
        size_t new_size = data.size() / 2;
        auto token = data[new_size].token;
        auto other = std::unique_ptr<IndexBlock>(new IndexBlock());
        other->last = std::move(last);
        last = std::move(data[new_size].block);
        other->data.assign(data.begin() + new_size + 1, data.end());
        data.resize(new_size);
        return TokenBlock(token, std::move(other));
    }

    void add_shingle(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, ShingleInfo& info)
    {
        auto it = data.begin();
        while(it < data.end() && *shingle_it > it->token)
        {
            ++it;
        }
        if(it == data.end())
        {
            last->add_shingle(shingle_it, shingle_end, info);
        }
        else
        {
            it->block->add_shingle(shingle_it, shingle_end, info);
        }

        if(it->block->size() > BLOCK_MAX_SIZE)
        {
            if(it == data.end())
            {
                auto tb = last->split();
                auto tb2 = TokenBlock(tb.token, std::move(last));
                data.push_back(tb);
                last = std::move(tb.block);
            }
            else
            {
                auto tb = it->block->split();
                auto left_token = it->token;
                it->token = tb.token;
                ++it;
                auto tb2 = TokenBlock(left_token, std::move(tb.block));
                data.insert(it, tb2);
            }
        }
    }

    Block* block_for(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end)
    {
        auto it = data.cbegin();
        while(it < data.cend() && *shingle_it > it->token)
        {
            ++it;
        }
        if(it == data.cend())
        {
            return last->block_for(shingle_it, shingle_end);
        }
        return it->block->block_for(shingle_it, shingle_end);
    }

    size_t size()
    {
        return data.size() + 1;
    };

};

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

    void add_shingle(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, ShingleInfo& info)
    {
        assert(shingle_it == shingle_end);

        auto it = data.begin();
        while(it->docid < info.docid && it < data.end())
        {
            ++it;
        }
        if(it->docid == info.docid)
        {
            it->count += info.count;
        }
        else
        {
            it = data.insert(it, info);
        }
    };

    TokenBlock split()
    {
        size_t new_size = data.size() / 2;
        auto token = data[new_size].docid;
        auto other = std::unique_ptr<LeafBlock>(new LeafBlock());
        other->data.assign(data.begin() + new_size, data.end());
        data.resize(new_size);
        return TokenBlock(token, std::move(other));
    };

    size_t size()
    {
        return data.size();
    };
};

class ListBlock: public Block
{ 
    /*
     * List of tokens that follows a shingle.
     * ID | META | Block& | ID | META | Block& | ID | META | Block&
    */

    private:
    std::vector<TokenBlock> data;

    ListBlock() {};

    public:

    ListBlock(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, ShingleInfo& info)
    {
        auto token = *shingle_it;

        std::unique_ptr<Block> block;
        if(shingle_end == shingle_it)
            block = std::unique_ptr<Block>(new LeafBlock(info));
        else
            block = std::unique_ptr<Block>(new ListBlock(++shingle_it, shingle_end, info));

        data.push_back(TokenBlock(token, std::move(block)));
    }

    Block* block_for(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end)
    {
        if(shingle_it == shingle_end)
            return this;

        auto it = data.cbegin();
        while(it < data.cend() && it->token != *shingle_it)
        {
            ++it;
        }
        if(it == data.cend())
            return nullptr;

        return (it->block)->block_for(++shingle_it, shingle_end);
    }

    void add_shingle(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, ShingleInfo& info)
    {
        assert(shingle_it != shingle_end);

        auto it = data.begin();
        while(it->token < *shingle_it && it < data.end())
        {
            ++it;
        }

        if(it->token == *shingle_it)
        {
            // the token exists, add it recursively
            it->block->add_shingle(++shingle_it, shingle_end, info);
        }
        else
        {
            // let's create the token
            auto new_block = std::unique_ptr<Block>(new ListBlock(++shingle_it, shingle_end, info));
            it = data.insert(it, TokenBlock(*shingle_it, std::move(new_block)));
        }

        if(it->block->size() > BLOCK_MAX_SIZE)
        {
            // tb is the right part of the splitted block + the token in the middle
            // tb2 is the token in the middle + the left part.
            auto tb = it->block->split();
            auto tb2 = TokenBlock(tb.token, std::move(it->block));
            auto last = std::move(tb.block);
            it->block = std::unique_ptr<Block>(new IndexBlock(tb2, last));
        }
    }

    size_t size()
    {
        return data.size();
    };

    TokenBlock split()
    {
        size_t new_size = data.size() / 2;
        auto token = data[new_size].token;
        auto other = std::unique_ptr<ListBlock>(new ListBlock());
        other->data.assign(data.begin() + new_size, data.end());
        data.resize(new_size);
        return TokenBlock(token, std::move(other));
    };
};

class Trie
{
    Trie()
    {
    }

    ~Trie()
    {
    }

};
