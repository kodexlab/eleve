#include "memory_storage.hpp"
#include <functional>
#include <cmath>

MemoryStorage::MemoryStorage(size_t default_ngram_length): default_ngram_length(default_ngram_length)
{
    // both terminals are sentence_end and sentence_start
    auto terminals = std::vector<std::string>();
    terminals.push_back(sentence_start);
    terminals.push_back(sentence_end);
    auto terminals_ids = tokens_to_ids(terminals);
    std::set<ID> terminals_ids_set = std::set<ID>(terminals_ids.cbegin(), terminals_ids.cend());
    // create the Tries
    fwd = MemoryTrie(terminals_ids_set);
    bwd = MemoryTrie(terminals_ids_set);
};

std::vector<ID> MemoryStorage::tokens_to_ids(strVec& tokens)
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

strVec MemoryStorage::ids_to_tokens(const std::vector<ID>& ids)
{
    auto tokens = std::vector<std::string>();
    tokens.reserve(ids.size());
    for(auto& id: ids)
    {
        tokens.push_back(hash_to_token[id]);
    }
    return tokens;
};

void MemoryStorage::add_ngram(strVec& ngram, int freq)
{
    auto ids = tokens_to_ids(ngram);
    fwd.add_ngram(ids, freq);
    bwd.add_ngram(reverse(ids), freq);
};

void MemoryStorage::add_sentence(std::vector<std::string> sentence, int freq, size_t ngram_length)
{
    if(! sentence.size())
        return;

    if(ngram_length == 0){
        ngram_length = default_ngram_length;
    }

    sentence.insert(sentence.begin(), sentence_start);
    sentence.push_back(sentence_end);
    auto ids = tokens_to_ids(sentence);

    for(auto it = ids.begin(); it < ids.end() - 1; it++)
    {
        fwd.add_ngram(std::vector<ID>(it, std::min(it + ngram_length, ids.end())), freq);
    }
    for(auto it = ids.rbegin(); it < ids.rend() - 1; it++)
    {
        bwd.add_ngram(std::vector<ID>(it, std::min(it + ngram_length, ids.rend())), freq);
    }
};

void MemoryStorage::clear()
{
    fwd.clear();
    bwd.clear();
};

void MemoryStorage::update_stats()
{
    fwd.update_stats();
    bwd.update_stats();
};

float MemoryStorage::query_autonomy(strVec& ngram)
{
    auto ids = tokens_to_ids(ngram);
    float f = fwd.query_autonomy(ids);
    if(std::isnan(f))
        return NAN;
    float b = bwd.query_autonomy(reverse(ids));
    // Notice that the above can be NaN. In which case it's propagated anyway.
    return (f + b) / 2.f;
};

float MemoryStorage::query_ev(strVec& ngram)
{
    auto ids = tokens_to_ids(ngram);
    float f = fwd.query_ev(ids);
    if(std::isnan(f))
        return NAN;
    float b = bwd.query_ev(reverse(ids));
    // Notice that the above can be NaN. In which case it's propagated anyway.
    return (f + b) / 2.f;
};

COUNT MemoryStorage::query_count(strVec& ngram)
{
    auto ids = tokens_to_ids(ngram);
    return fwd.query_count(ids);
};

float MemoryStorage::query_entropy(strVec& ngram)
{
    auto ids = tokens_to_ids(ngram);
    float f = fwd.query_entropy(ids);
    if(std::isnan(f))
        return NAN;
    float b = bwd.query_entropy(reverse(ids));
    // Notice that the above can be NaN. In which case it's propagated anyway.
    return (f + b) / 2.f;
};
