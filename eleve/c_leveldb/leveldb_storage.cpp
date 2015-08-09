#include "leveldb_storage.hpp"

void LeveldbStorage::add_ngram(strVec& s, int freq)
{
    fwd.add_ngram(s, freq);
    bwd.add_ngram(reverse(s), freq);
};

void LeveldbStorage::add_sentence(std::vector<std::string> s, int freq)
{
    if(! s.size())
        return;

    s.insert(s.begin(), "^");
    s.push_back("$");

    for(auto it = s.begin(); it < s.end() - 1; it++)
    {
        fwd.add_ngram(std::vector<std::string>(it, std::min(it + ngram_length, s.end())), freq);
    }
    for(auto it = s.rbegin(); it < s.rend() - 1; it++)
    {
        bwd.add_ngram(std::vector<std::string>(it, std::min(it + ngram_length, s.rend())), freq);
    }
};

void LeveldbStorage::clear()
{
    fwd.clear();
    bwd.clear();
};

void LeveldbStorage::update_stats()
{
    fwd.update_stats();
    bwd.update_stats();
};

float LeveldbStorage::query_autonomy(strVec& ngram)
{
    float f = fwd.query_autonomy(ngram);
    if(isnan(f))
        return NAN;
    float b = bwd.query_autonomy(reverse(ngram));
    if(isnan(b))
        return NAN;
    return (f + b) / 2.f;
};

float LeveldbStorage::query_ev(strVec& ngram)
{
    float f = fwd.query_ev(ngram);
    if(isnan(f))
        return NAN;
    float b = bwd.query_ev(reverse(ngram));
    if(isnan(b))
        return NAN;
    return (f + b) / 2.f;
};

float LeveldbStorage::query_count(strVec& ngram)
{
    return (fwd.query_count(ngram) + bwd.query_count(reverse(ngram))) / 2.f;
};

float LeveldbStorage::query_entropy(strVec& ngram)
{
    float f = fwd.query_entropy(ngram);
    if(isnan(f))
        return NAN;
    float b = bwd.query_entropy(reverse(ngram));
    if(isnan(b))
        return NAN;
    return (f + b) / 2.f;
};
