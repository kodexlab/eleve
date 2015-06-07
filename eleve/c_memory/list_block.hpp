#ifndef _LIST_BLOCK_HPP_
#define _LIST_BLOCK_HPP_

#include "block.hpp"
#include "unique_list_block.hpp"
#include "unique_leaf_block.hpp"
#include "index_block.hpp"

class ListBlock: public Block
{ 
    friend class UniqueListBlock;

    /*
     * List of tokens that follows a shingle.
     * ID | META | Block& | ID | META | Block& | ID | META | Block&
    */

    private:
    std::vector<TokenBlock> data;

    class ListBlockIterator: public BlockIterator
    {
        private:
        std::vector<TokenBlock>::iterator current_child;
        std::vector<TokenBlock>::iterator childs_end;

        public:

        ListBlockIterator(ListBlock* b)
        {
            childs_end = b->data.end();
            current_child = b->data.begin();
        }

        void next()
        {
            if(current_child != childs_end)
            {
                ++current_child;
            }
        };

        std::pair<ID, Block*> get()
        {
            return (current_child == childs_end)
                ? std::pair<ID, Block*>(NULL, nullptr)
                : std::pair<ID, Block*>(current_child->token, current_child->block.get());
        };
    };

    ListBlock(TokenBlock& tb) {data.push_back(TokenBlock(tb.token, std::move(tb.block)));};

    public:

    ListBlock() {};

    ListBlock(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, ShingleInfo& info);

    Block* block_for(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end);

    std::unique_ptr<Block> add_shingle(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, ShingleInfo& info);

    size_t size()
    {
        return data.size();
    };

    TokenBlock split();

    std::unique_ptr<BlockIterator> begin_childs()
    {
        return std::unique_ptr<ListBlockIterator>(new ListBlockIterator(this));
    };

    COUNT count();
};

#endif
