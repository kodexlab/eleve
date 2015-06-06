#include <vector>
#include <memory>
#include <assert.h>
#include <map>
#include <iostream>

#include <boost/python.hpp>
#include <boost/python/stl_iterator.hpp>

/*
 BLOCK:
 1 bit always 1 + 2 bits for type + 13 bits for size
 DATA (depending on type)

 BLOCK can also be:
 null byte + 64 bits ptr to a BLOCK (see above)

 INDEX-DATA:
 (TOKEN are delta-encoded)
 BLOCK | TOKEN | BLOCK | TOKEN ... | BLOCK | TOKEN | BLOCK

 LEAF-DATA:
 (DOCID are delta-encoded, count are VB encoded without delta)
 DOCID | COUNT | DOCID | COUNT | DOCID

 LIST-DATA:
 (TOKEN are delta-encoded)
 TOKEN | BLOCK | TOKEN | BLOCK | ... | TOKEN | BLOCK
 in the future:
 TOKEN | META | BLOCK | TOKEN | META | BLOCK ...

 TO ENCODE NGRAM (1,2) for docid 1:
 1 01 x || 1 | 1 01 x || 2 | 1 10 x || 1 | 1 |
*/

#define MSG(a) std::cerr << a << std::endl;

const size_t INLINE_MAX_SIZE = 128;
const size_t BLOCK_MAX_SIZE = 4096 - 2;
const size_t LEAF_MAX_GROWTH = 6;

typedef uint32_t ID;
typedef uint32_t COUNT;
typedef std::vector<ID>::const_iterator shingle_const_iterator;

struct ShingleInfo
{
    ID docid;
    COUNT count;

    ShingleInfo(ID d, COUNT c): docid(d), count(c) {};
};




template<typename T> inline T read_cn(char*& buffer)
{
    register T number = 0;
    register char ptr;
    do
    { 
        ptr = *buffer++;
        number = (number << 7) | (ptr & 0x7F);
    }
    while(ptr & 0x80);
    return number;
};

inline void pass_cn(char*& buffer)
{
    while(*buffer++ & 0x80);
};

inline void copy_cn(char*& src, char*& dst)
{
    while(*src & 0x80)
    {
        *dst++ = *src++;
    }
    *dst++ = *src++;
}

template<typename T> inline uint8_t cn_size(T number)
{
    register uint8_t i;
    for(i = sizeof(number) * 8 / 7; i && ! (number >> i * 7); --i);
    return i + 1;
};

template<typename T> inline void write_cn(char*& buffer, T number)
{
    uint8_t size = cn_size(number) - 1;
    for(uint8_t i = size; i; --i)
    {
        *(buffer + size - i) = (number >> i*7) & 0x7F | 0x80;
    }
    *(buffer + size) = number & 0x7F;
    buffer += size + 1;
};

inline size_t block_size(char* ptr)
{
    return *(uint8_t*)ptr ? *(uint16_t*)ptr & 0x1fff : 1 + sizeof(char*);
};

void move_block(char*& src, char*& dst, bool free_mem=true)
{
    if(! *(uint8_t*)src)
    {
        *(uint8_t*)dst = 0;
        *(char**)(dst + 1) = *((char**) src + 1);
        dst += 1 + sizeof(char*);
        src += 1 + sizeof(char*);
        return;
    }

    size_t size = block_size(src);
    if(size <= INLINE_MAX_SIZE)
    {
        memcpy(dst, src, size);
        if(free_mem)
        {
            free(src);
        }
        dst += size;
        src += size;
    }
    else
    {
        *(uint8_t*)dst = 0;
        *(char**)(dst + 1) = src;
        dst += 1 + sizeof(char*);
        src += size;
    }
};

char* create_shingle(shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, ShingleInfo& info)
{
    MSG("-> create_shingle")
    if(shingle_it == shingle_end)
    {
        MSG("create leaf shingle")
        uint16_t s = 2 + cn_size(info.docid) + cn_size(info.count);
        MSG(" size " << s)
        char* ptr = (char*)malloc(s);
        *(uint16_t*)ptr = 0xA000 | s;
        char* ptr2 = ptr + 2;
        write_cn(ptr2, info.docid);
        write_cn(ptr2, info.count);
        return ptr;
    }
    else
    {
        MSG("create token " << *shingle_it)
        char* child = create_shingle(shingle_it + 1, shingle_end, info);
        uint16_t child_size = block_size(child);
        uint16_t s = child_size + 2 + cn_size(*shingle_it);
        char* ptr = (char*)malloc(s);
        *((uint16_t*)ptr) = 0xC000 | s;
        char* ptr2 = ptr + 2;
        write_cn(ptr2, *shingle_it);
        memcpy(ptr2, child, child_size);
        free(child);
        return ptr;
    }
};

char* add_shingle(char* const ptr, shingle_const_iterator shingle_it, shingle_const_iterator shingle_end, ShingleInfo& info)
{
    MSG("-> add_shingle")
    if(! *(uint8_t*)ptr)
    {
        MSG("pointer wrapper")
        char* real_ptr = *(char**)(ptr + 1);
        char* new_ptr = add_shingle(real_ptr, shingle_it, shingle_end, info);
        if(new_ptr != real_ptr)
        {
            free(real_ptr);
        }
        return new_ptr;
    }

    char* const block_end = ptr + block_size(ptr);

    switch((*(uint16_t*)ptr & 0x6000) >> 13)
    {
        case 1: // leaf
        {
            MSG("add shingle for leaf, docid " << info.docid);
            assert(shingle_it == shingle_end);

            char* const new_ptr = (char*)malloc(block_size(ptr) + LEAF_MAX_GROWTH);
            char* new_cur = new_ptr + 2;
            char* ptr_cur = ptr + 2;
            ID docid = 0;
            ID gap;

            while(ptr_cur < block_end)
            {
                gap = read_cn<ID>(ptr_cur);
                assert(gap);
                docid += gap;
                MSG(" docid " << docid)
                if(docid >= info.docid)
                {
                    break;
                }
                write_cn(new_cur, gap);
                copy_cn(ptr_cur, new_cur); // count, unchanged
            }
            
            // add the block
            
            if(ptr_cur >= block_end)
            {
                MSG("shingle added at end");
                write_cn(new_cur, info.docid - docid);
                write_cn(new_cur, info.count);
            }
            else if(docid == info.docid)
            {
                MSG("shingle merged");
                write_cn(new_cur, gap);
                COUNT c = read_cn<COUNT>(ptr_cur);
                write_cn(new_cur, c + info.count);
            }
            else
            {
                MSG("shingle inserted");
                write_cn(new_cur, info.docid - (docid - gap));
                write_cn(new_cur, info.count);

                write_cn(new_cur, docid - info.docid);
                copy_cn(ptr_cur, new_cur);
            }
            
            // copy the rest

            while(ptr_cur < block_end)
            {
                copy_cn(ptr_cur, new_cur);
                copy_cn(ptr_cur, new_cur);
            }

            *(uint16_t*)new_ptr = (new_cur - new_ptr) | 0xA000; // 0b101...
            return new_ptr;
        }
        break;
        case 2: // list of tokens
        {
            const ID token_to_add = *shingle_it;
            MSG("add shingle for token " << token_to_add);
            ++shingle_it;

            // first pass to create child node

            char* ptr_cur = ptr + 2;
            ID token = 0;

            while(ptr_cur < block_end)
            {
                token += read_cn<size_t>(ptr_cur);
                MSG(" token " << token)
                if(token >= token_to_add)
                {
                    break;
                }
                ptr_cur += block_size(ptr_cur);
            }

            char* child_block;
            if(token == token_to_add)
            {
                child_block = add_shingle(ptr_cur, shingle_it, shingle_end, info);
                if(child_block == ptr_cur)
                {
                    return ptr;
                }
            }
            else
            {
                child_block = create_shingle(shingle_it, shingle_end, info);
            }

            // second pass to merge child node

            const bool merge_inline = block_size(child_block) <= INLINE_MAX_SIZE;
            const size_t child_size = merge_inline ? block_size(child_block) : 1 + sizeof(char*);
            
            // only if needed because size differs :
            if(token == token_to_add && child_size == block_size(ptr_cur))
            {
                if(merge_inline)
                {
                    memcpy(ptr_cur, child_block, child_size);
                    free(child_block);
                    MSG("inline merge via memcpy");
                }
                else
                {
                    MSG("pointer merge")
                    *(char**)(ptr_cur + 1) = child_block;
                }
                return ptr;
            }

            MSG("full merge");

            const size_t old_child_size = token == token_to_add ? block_size(ptr_cur) : 0;
            char* const new_ptr = (char*)malloc(block_size(ptr) - old_child_size + child_size);
            assert(new_ptr > 0);
            char* new_cur = new_ptr + 2;
            ptr_cur = ptr + 2;
            token = 0;
            ID gap;

            while(ptr_cur < block_end)
            {
                gap = read_cn<ID>(ptr_cur);
                assert(gap);
                token += gap;
                MSG(" token " << token)
                if(token >= token_to_add)
                {
                    break;
                }
                write_cn(new_cur, gap);
                move_block(ptr_cur, new_cur, false);
            }
            
            // add the block
            
            if(ptr_cur >= block_end)
            {
                write_cn(new_cur, token_to_add - token);
                move_block(child_block, new_cur);
            }
            else if(token == token_to_add)
            {
                write_cn(new_cur, gap);
                move_block(child_block, new_cur);
            }
            else
            {
                write_cn(new_cur, token_to_add - (token - gap));
                move_block(child_block, new_cur);

                write_cn(new_cur, token - token_to_add);
                move_block(ptr_cur, new_cur, false);
            }
            
            // copy the rest

            while(ptr_cur < block_end)
            {
                copy_cn(ptr_cur, new_cur);
                move_block(ptr_cur, new_cur, false);
            }

            *(uint16_t*)new_ptr = (new_cur - new_ptr) | 0xC000; // 0b110...
            return new_ptr;

        }
        break;
        case 3:
        {
            assert(false);
        }
        break;
        default:
        assert(false);
    }
};

namespace py = boost::python;

class Trie
{
    protected:

    char* root = nullptr;

    public:

    Trie()
    {
    };

    void add_ngram(py::list ngram, ID docid, COUNT freq)
    {
        std::vector<ID> shingle{py::stl_input_iterator<ID>(ngram),
                                py::stl_input_iterator<ID>()};

        ShingleInfo info(docid, freq);

        if(! root)
        {
            root = create_shingle(shingle.cbegin(), shingle.cend(), info);
        }
        else
        {
            root = add_shingle(root, shingle.cbegin(), shingle.cend(), info);
        }
    };

    COUNT query_count(py::list ngram)
    {
        std::vector<ID> shingle{py::stl_input_iterator<ID>(ngram),
                                py::stl_input_iterator<ID>()};

        return 0;
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
