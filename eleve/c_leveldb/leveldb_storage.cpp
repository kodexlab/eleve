#include "leveldb_storage.hpp"

std::string LeveldbStorage::directory_add(const std::string& _path, const std::string& subdir)
{
    if(! boost::filesystem::is_directory(_path))
    {
        if(! boost::filesystem::create_directory(_path))
        {
            std::cerr << "Unable to create directory for database: " << _path << std::endl;
            exit(EXIT_FAILURE);
        }
    }
    return _path + "/" + subdir;
};

LeveldbStorage::LeveldbStorage(const std::string path, size_t _default_ngram_length):
    path(path), default_ngram_length(_default_ngram_length),
    fwd(directory_add(path, "fwd")),
    bwd(directory_add(path, "bwd"))
{
    // Set the terminals to Tries
    auto terminals = std::set<std::string>();
    terminals.insert(sentence_start);
    terminals.insert(sentence_end);
    fwd.set_terminals(terminals);
    bwd.set_terminals(terminals);

    // Configure the config db
    leveldb::Options options;
    options.create_if_missing = true;
    options.write_buffer_size = 64*1024*1024;
    options.block_size = 16*1024;

    auto status = leveldb::DB::Open(options, directory_add(path, "/config"), &config);
    if(! status.ok())
    {
        std::cerr << "Unable to open the database at " << path << ": " << status.ToString() << std::endl;
        exit(EXIT_FAILURE);
    }
    // try to get the default_ngram_length value from config db
    std::string value;
    status = config->Get(leveldb::ReadOptions(), "default_ngram_length", &value);
    if (status.ok()) {
        default_ngram_length = *(size_t*) value.data();
    } else {
        // store default_ngram_length in a config DB
        std::array<char, sizeof(size_t)> setvalue;
        *(size_t*)setvalue.data() = default_ngram_length;
        status = config->Put(leveldb::WriteOptions(), "default_ngram_length", leveldb::Slice(setvalue.data(), sizeof(size_t)));
    }
};


void LeveldbStorage::add_ngram(strVec& s, int freq)
{
    fwd.add_ngram(s, freq);
    bwd.add_ngram(reverse(s), freq);
};

void LeveldbStorage::add_sentence(std::vector<std::string> sentence, int freq, size_t ngram_length)
{
    if(! sentence.size())
        return;

    if(ngram_length == 0){
        ngram_length = default_ngram_length;
    }

    sentence.insert(sentence.begin(), sentence_start);
    sentence.push_back(sentence_end);

    for(auto it = sentence.begin(); it < sentence.end() - 1; it++)
    {
        fwd.add_ngram(std::vector<std::string>(it, std::min(it + ngram_length, sentence.end())), freq);
    }
    for(auto it = sentence.rbegin(); it < sentence.rend() - 1; it++)
    {
        bwd.add_ngram(std::vector<std::string>(it, std::min(it + ngram_length, sentence.rend())), freq);
    }
};

void LeveldbStorage::update_stats()
{
    fwd.update_stats();
    bwd.update_stats();
};

float LeveldbStorage::query_autonomy(strVec& ngram)
{
    float f = fwd.query_autonomy(ngram);
    if(std::isnan(f))
        return NAN;
    float b = bwd.query_autonomy(reverse(ngram));
    // Notice that the above can be NaN. In which case it's propagated anyway.
    return (f + b) / 2.f;
};

float LeveldbStorage::query_ev(strVec& ngram)
{
    float f = fwd.query_ev(ngram);
    if(std::isnan(f))
        return NAN;
    float b = bwd.query_ev(reverse(ngram));
    // Notice that the above can be NaN. In which case it's propagated anyway.
    return (f + b) / 2.f;
};

COUNT LeveldbStorage::query_count(strVec& ngram)
{
    return fwd.query_count(ngram);
};

float LeveldbStorage::query_entropy(strVec& ngram)
{
    float f = fwd.query_entropy(ngram);
    if(std::isnan(f))
        return NAN;
    float b = bwd.query_entropy(reverse(ngram));
    // Notice that the above can be NaN. In which case it's propagated anyway.
    return (f + b) / 2.f;
};

void LeveldbStorage::clear()
{
    fwd.clear();
    bwd.clear();
};

void LeveldbStorage::close()
{
    if(config != NULL)
    {
        delete config;
        config = NULL;
    }
    fwd.close();
    bwd.close();
};

