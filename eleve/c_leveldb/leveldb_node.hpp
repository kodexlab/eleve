#ifndef _LEVELDBNODE_HPP_
#define _LEVELDBNODE_HPP_

#include "config.hpp"
#include "leveldb/slice.h"
#include "leveldb/write_batch.h"

static const leveldb::ReadOptions read_options;
static const leveldb::WriteOptions write_options;

class Node
{
    protected:
        leveldb::DB* db;

        static std::string ascii_key(const std::string& key)
        {
            std::string r;
            for(auto& c: key)
            {
                r += std::to_string((int)c);
                r += " ";
            }
            return r;
        };

    public:
        std::string key;
        COUNT count;
        float entropy;

        // data can be :
        //  - nullptr, which means that the data needs to be retrieved (and set the default if not found)
        //  - 1, which means that the default should be set and no attempt to retrieve (to speed up the cases where we are sure it is not in the DB)
        //  - any pointer, which means that we have the data at that pointer
        Node(leveldb::DB* db, const std::string& key, const char* data = nullptr);

        void save(leveldb::WriteBatch* batch = nullptr) const;

        void update_entropy(std::set<std::string>& terminals);

        std::string begin_childs() const;
        std::string end_childs() const; // key PAST the childs
};

#endif
