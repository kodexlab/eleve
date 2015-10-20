#ifndef _LEVELDB_STORAGE_HPP_
#define _LEVELDB_STORAGE_HPP_
#include "leveldb_trie.hpp"
#include <boost/filesystem.hpp>

typedef const std::vector<std::string> strVec;

#define DEFAULT_TERMINALS {"^", "$"}

class LeveldbStorage
{
    protected:
        size_t ngram_length;
        LeveldbTrie fwd;
        LeveldbTrie bwd;

        static std::string directory_add(const std::string& path, const std::string& subdir)
        {
            if(! boost::filesystem::is_directory(path))
            {
                if(! boost::filesystem::create_directory(path))
                {
                    std::cerr << "Unable to create directory for database: " << path << std::endl;
                    exit(EXIT_FAILURE);
                }
            }

            return path + "/" + subdir;
        };

        static inline std::set<std::string> strvec_to_set(strVec& terminals)
        {
            return std::set<std::string>(terminals.cbegin(), terminals.cend());
        };

    public:
        LeveldbStorage(size_t order, std::string path, strVec& terminals): ngram_length(order),
                                                                           fwd(directory_add(path, "fwd"), strvec_to_set(terminals)),
                                                                           bwd(directory_add(path, "bwd"), strvec_to_set(terminals))
        {
        };

        LeveldbStorage(size_t o, std::string path): LeveldbStorage(o, path, DEFAULT_TERMINALS) {};

        inline static std::vector<std::string> reverse(const std::vector<std::string>& ids)
        {
            return std::vector<std::string>(ids.rbegin(), ids.rend());
        };
        

        void add_sentence(std::vector<std::string> s, int freq=1);
        void add_ngram(strVec& s, int freq=1);

        void clear();
        void update_stats();

        float query_autonomy(strVec& ngram);
        float query_ev(strVec& ngram);
        float query_count(strVec& ngram);
        float query_entropy(strVec& ngram);
};

#endif
