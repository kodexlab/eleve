#include <vector>
#include <memory>
#include <assert.h>
#include <map>
#include <iostream>

#include <boost/python.hpp>
#include <boost/python/stl_iterator.hpp>

const size_t BLOCK_MAX_SIZE = 128;

typedef uint32_t ID;
typedef uint32_t COUNT;
typedef std::vector<ID>::const_iterator shingle_const_iterator;

class Block;
class LeafBlock;
class ListBlock;
struct TokenBlock;

struct ShingleInfo
{
    ID docid;
    COUNT count;

    ShingleInfo(ID d, COUNT c): docid(d), count(c) {};
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
    virtual void add_shingle(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, ShingleInfo& info) = 0;
    virtual TokenBlock split() = 0;
    virtual size_t size() = 0;

    virtual Block* block_for(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end) = 0;
    virtual std::unique_ptr<BlockIterator> begin_childs() = 0;

    virtual COUNT count() = 0;
    //virtual std::map<ID, COUNT> postings();
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

    void add_shingle(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, ShingleInfo& info)
    {
        assert(shingle_it != shingle_end);

        auto it = std::lower_bound(data.begin(), data.end(), *shingle_it, [](TokenBlock& a, ID t) {return a.token < t;});
        // it->token >= token

        if(it == data.end())
        {
            last->add_shingle(shingle_it, shingle_end, info);
        }
        else
        {
            it->block->add_shingle(shingle_it, shingle_end, info);
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
    };

    TokenBlock split()
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

    size_t size()
    {
        return data.size();
    };

    std::unique_ptr<BlockIterator> begin_childs()
    {
        return std::unique_ptr<EmptyBlockIterator>(new EmptyBlockIterator());
    };

    COUNT count()
    {
        COUNT c = 0;
        for(auto it = data.begin(); it != data.end(); ++it)
        {
            c += it->count;
        }
        return c;
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


    public:

    ListBlock() {};

    ListBlock(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, ShingleInfo& info)
    {
        auto token = *shingle_it;
        ++shingle_it;

        std::unique_ptr<Block> block;
        if(shingle_end == shingle_it)
        {
            block = std::unique_ptr<Block>(new LeafBlock(info));
        }
        else
        {
            block = std::unique_ptr<Block>(new ListBlock(shingle_it, shingle_end, info));
        }

        data.push_back(TokenBlock(token, std::move(block)));
    }

    Block* block_for(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end)
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
    }

    void add_shingle(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, ShingleInfo& info)
    {
        assert(shingle_it != shingle_end);

        auto token = *shingle_it;

        auto it = std::lower_bound(data.begin(), data.end(), token, [](TokenBlock& a, ID t) {return a.token < t;});
        // it->token >= token

        if(it != data.end() && it->token == token)
        {
            // the token exists, add it recursively
            it->block->add_shingle(++shingle_it, shingle_end, info);
        }
        else
        {
            // let's create the token
            ++shingle_it;
            std::unique_ptr<Block> new_block;
            if(shingle_it == shingle_end)
            {
                new_block = std::unique_ptr<Block>(new LeafBlock(info));
            }
            else
            {
                new_block = std::unique_ptr<Block>(new ListBlock(shingle_it, shingle_end, info));
            }
            it = data.insert(it, TokenBlock(token, std::move(new_block)));
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
        for(auto it = data.begin() + new_size + 1; it != data.end(); ++it)
        {
            other->data.push_back(std::move(*it));
        }
        data.erase(data.begin() + new_size, data.end());
        return TokenBlock(token, std::move(other));
    };

    std::unique_ptr<BlockIterator> begin_childs()
    {
        return std::unique_ptr<ListBlockIterator>(new ListBlockIterator(this));
    };

    COUNT count()
    {
        COUNT c = 0;
        for(auto it = data.begin(); it != data.end(); ++it)
        {
            c += it->block->count();
        }
        return c;
    };
};

namespace py = boost::python;

class Trie
{
    protected:

    std::unique_ptr<Block> root;

    void add_shingle(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, ShingleInfo& info)
    {
        root->add_shingle(shingle_it, shingle_end, info);

        if(root->size() > BLOCK_MAX_SIZE)
        {
            // tb is the right part of the splitted block + the token in the middle
            // tb2 is the token in the middle + the left part.
            auto tb = root->split();
            auto tb2 = TokenBlock(tb.token, std::move(root));
            auto last = std::move(tb.block);
            root = std::unique_ptr<Block>(new IndexBlock(tb2, last));
        }
    };

    public:

    Trie()
    {
        root = std::unique_ptr<Block>(new ListBlock());
    };

    void add_ngram(py::list ngram, ID docid, COUNT freq)
    {
        std::vector<ID> shingle{py::stl_input_iterator<ID>(ngram),
                                py::stl_input_iterator<ID>()};

        ShingleInfo info(docid, freq);

        add_shingle(shingle.begin(), shingle.end(), info);
    };

    COUNT query_count(py::list ngram)
    {
        std::vector<ID> shingle{py::stl_input_iterator<ID>(ngram),
                                py::stl_input_iterator<ID>()};

        Block* b = root->block_for(shingle.cbegin(), shingle.cend());
        if(! b)
        {
            return 0;
        }
        return b->count();
    }
};

BOOST_PYTHON_MODULE(eleve_trie)
{
    using namespace boost::python;
    class_<Trie, boost::noncopyable>("Trie")
        .def("add_ngram", &Trie::add_ngram)
        .def("query_count", &Trie::query_count)
    ;
}
