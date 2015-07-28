#include "memory_storage.hpp"
#include <functional>

std::vector<ID> MemoryStorage::tokens_to_ids(std::vector<std::string> tokens)
{
    auto ids = std::vector<ID>();
    ids.reserve(tokens.size());
    for(auto& token: tokens)
    {
        // calculate the hash, putting it in the mapping if it's new
        std::hash<std::string> hash_fn;
        auto hash = hash_fn(token);
        while(true)
        {
            auto it = hash_to_token.find(hash);
            if(it == hash_to_token.end()) // never seen
            {
                hash_to_token[hash] = token;
                break;
            }
            if(it->second == token) // known
            {
                break;
            }
            hash++; // collision, increment and try again
        }

        // add it
        ids.push_back(hash);
    }
    return ids;
};

std::vector<std::string> MemoryStorage::ids_to_tokens(std::vector<ID> ids)
{
    auto tokens = std::vector<std::string>();
    tokens.reserve(ids.size());
    for(auto& id: ids)
    {
        tokens.push_back(hash_to_token[id]);
    }
    return tokens;
};

void MemoryStorage::add_ngram(py::list s, int freq)
{
};
