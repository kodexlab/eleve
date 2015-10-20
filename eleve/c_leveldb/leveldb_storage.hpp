#ifndef _LEVELDB_STORAGE_HPP_
#define _LEVELDB_STORAGE_HPP_
#include "leveldb_trie.hpp"
#include <boost/filesystem.hpp>

typedef const std::vector<std::string> strVec;

class LeveldbStorage
{
    protected:
        std::string path;
        size_t default_ngram_length;
        std::string sentence_start = "^";
        std::string sentence_end = "$";
        
        LeveldbTrie fwd;
        LeveldbTrie bwd;

        leveldb::DB* config;

        static std::string directory_add(const std::string& path, const std::string& subdir);
        static inline std::set<std::string> strvec_to_set(strVec& terminals)
        {
            return std::set<std::string>(terminals.cbegin(), terminals.cend());
        };

    public:
        LeveldbStorage(const std::string path, size_t default_ngram_length=5);

        inline static std::vector<std::string> reverse(const std::vector<std::string>& ids)
        {
            return std::vector<std::string>(ids.rbegin(), ids.rend());
        };

        void add_sentence(std::vector<std::string> sentence, int freq=1, size_t ngram_length=0);
        void add_ngram(strVec& s, int freq=1);

        void update_stats();

        float query_autonomy(strVec& ngram);
        float query_ev(strVec& ngram);
        float query_count(strVec& ngram);
        float query_entropy(strVec& ngram);

        void clear();
        void close();
};

#endif
