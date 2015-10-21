#ifndef _MEMORY_STORAGE_HPP_
#define _MEMORY_STORAGE_HPP_
#include "memory_trie.hpp"
#include <unordered_map>

typedef const std::vector<std::string> strVec;

class MemoryStorage
{
    protected:
        size_t default_ngram_length;
        // Use PRIVATE_USE_AREA codes
        std::string sentence_start = "\xee\x80\xab"; // in unicode => \ue02b
        //  see http://www.fileformat.info/info/unicode/char/e02b/index.htm
        std::string sentence_end = "\xee\x80\xad";  // in unicode => \ue02d
        //  see http://www.fileformat.info/info/unicode/char/e02d/index.htm
        MemoryTrie fwd;
        MemoryTrie bwd;
        std::unordered_map<std::size_t, std::string> hash_to_token;

        std::vector<ID> tokens_to_ids(strVec& tokens);
        strVec ids_to_tokens(const std::vector<ID>& ids);

    public:
        MemoryStorage(size_t default_ngram_length=5);

        inline static std::vector<ID> reverse(const std::vector<ID>& ids)
        {
            return std::vector<ID>(ids.rbegin(), ids.rend());
        };

        void add_sentence(std::vector<std::string> s, int freq=1, size_t ngram_length=0);
        void add_ngram(strVec& s, int freq=1);

        void clear();
        void close(){};
        void update_stats();

        float query_autonomy(strVec& ngram);
        float query_ev(strVec& ngram);
        COUNT query_count(strVec& ngram);
        float query_entropy(strVec& ngram);
};

#endif
