#ifndef _INDEX_BLOCK_HPP_
#define _INDEX_BLOCK_HPP_

#include "block.hpp"

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

    class IndexBlockIterator: public BlockIterator
    {
        private:
        std::unique_ptr<BlockIterator> current_child_iterator;
        std::vector<TokenBlock>::iterator current_child;
        std::vector<TokenBlock>::iterator childs_end;

        public:

        IndexBlockIterator(IndexBlock* b)
        {
            childs_end = b->data.end();
            current_child = b->data.begin();
            current_child_iterator = current_child->block->begin_childs();
        }

        IndexBlockIterator(const IndexBlockIterator&) = delete;

        void next()
        {
            current_child_iterator->next();
            if(current_child_iterator->get().second == nullptr && current_child != childs_end)
            {
                current_child++;
                if(current_child != childs_end)
                {
                    current_child_iterator = current_child->block->begin_childs();
                }
            }
        };

        std::pair<ID, Block*> get()
        {
            return current_child_iterator->get();
        };
    };

    public:

    IndexBlock(TokenBlock& b1, std::unique_ptr<Block>& b2)
    {
        last = std::move(b2);
        data.push_back(std::move(b1));
    }

    std::unique_ptr<BlockIterator> begin_childs()
    {
        return std::unique_ptr<IndexBlockIterator>(new IndexBlockIterator(this));
    };

    TokenBlock split()
    {
        // (Block* | ID) | Block*
        size_t new_size = data.size() / 2;
        auto token = data[new_size].token;
        auto other = std::unique_ptr<IndexBlock>(new IndexBlock());
        other->last = std::move(last);
        last = std::move(data[new_size].block);
        for(auto it = data.begin() + new_size + 1; it != data.end(); ++it)
        {
            other->data.push_back(std::move(*it));
        }
        data.erase(data.begin() + new_size, data.end());
        return TokenBlock(token, std::move(other));
    }

    std::unique_ptr<Block> add_shingle(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, ShingleInfo& info)
    {
        assert(shingle_it != shingle_end);

        auto it = std::lower_bound(data.begin(), data.end(), *shingle_it, [](TokenBlock& a, ID t) {return a.token < t;});
        // it->token >= token

        std::unique_ptr<Block> b;
        if(it == data.end())
        {
            b = last->add_shingle(shingle_it, shingle_end, info);
            if(b)
                last = std::move(b);
        }
        else
        {
            b = it->block->add_shingle(shingle_it, shingle_end, info);
            if(b)
                it->block = std::move(b);
        }

        if((it == data.end() ? last->size() : it->block->size()) > BLOCK_MAX_SIZE)
        {
            if(it == data.end())
            {
                auto tb = last->split();
                auto tb2 = TokenBlock(tb.token, std::move(last));
                data.push_back(std::move(tb2));
                last = std::move(tb.block);
            }
            else
            {
                auto tb = it->block->split();
                auto left_token = it->token;
                it->token = tb.token;
                ++it;
                auto tb2 = TokenBlock(left_token, std::move(tb.block));
                data.insert(it, std::move(tb2));
            }
        }

        return nullptr;
    }

    Block* block_for(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end)
    {
        auto it = data.begin();
        while(it != data.end() && *shingle_it > it->token)
        {
            ++it;
        }
        if(it == data.end())
        {
            return last->block_for(shingle_it, shingle_end);
        }
        return it->block->block_for(shingle_it, shingle_end);
    }

    size_t size()
    {
        return data.size() + 1;
    };

    COUNT count()
    {
        COUNT c = 0;
        for(auto it = data.begin(); it != data.end(); ++it)
        {
            c += it->block->count();
        }
        c += last->count();
        return c;
    };
};

#endif
