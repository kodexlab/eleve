#include "leveldb_trie.hpp"
#include <array>

LeveldbTrie::LeveldbTrie(const std::string& path)
{
    leveldb::Options options;
    options.create_if_missing = true;
    options.write_buffer_size = 64*1024*1024;
    options.block_size = 16*1024;

    auto status = leveldb::DB::Open(options, path, &db);
    if(! status.ok())
    {
        std::cerr << "Unable to open the database at " << path << ": " << status.ToString() << std::endl;
        exit(EXIT_FAILURE);
    }

    // load normalization constants and dirty status.

    dirty = true;
    for(char i = 0;; i++)
    {
        std::string value;
        std::array<char, 2> key;
        key[0] = 0xff;
        key[1] = i;
        auto status = db->Get(read_options, leveldb::Slice(key.data(), 2), &value);
        if(! status.ok())
            break;

        Normalization n;
        assert(value.size() == sizeof(float) * 2);
        n.mean = *(float*)value.data();
        n.stdev = *(float*)(value.data() + sizeof(float));
        normalization.push_back(n);

        dirty = false;
    }
};


void LeveldbTrie::update_stats_rec(float parent_entropy, size_t depth, Node& node)
{
    node.update_entropy(terminals);

    if(!isnan(node.entropy) && (node.entropy != 0. || parent_entropy != 0.))
    {
        float ev = node.entropy - parent_entropy;

        if(normalization.size() <= depth)
        {
            normalization.resize(depth + 1);
        }

        Normalization n = normalization[depth];
        float old_mean = n.mean;
        n.count += 1;
        n.mean += (ev - old_mean) / float(n.count);
        n.stdev += (ev - old_mean)*(ev - n.mean);
        normalization[depth] = n;
    }

    auto it = db->NewIterator(read_options);
    auto end = node.end_childs();
    for(it->Seek(leveldb::Slice(node.begin_childs())); it->Valid() && it->key().compare(end) < 0; it->Next())
    {
        Node child = Node(db, it->key().ToString(), it->value().data());
        update_stats_rec(node.entropy, depth + 1, child);
    }
};

void LeveldbTrie::update_stats()
{
    if(! dirty)
        return;

    normalization.clear();

    auto root = search_node(std::vector<std::string>());
    update_stats_rec(NAN, 0, root);

    for(size_t i = 0; i < normalization.size(); i++)
    {
        auto& n = normalization[i];

        if(n.count != 0)
        {
            n.stdev = sqrtf(n.stdev / float(n.count));
        }

        std::array<char, 2> key;
        key[0] = 0xff;
        key[1] = i;

        std::array<char, sizeof(float) * 2> value;
        *(float*)value.data() = n.mean;
        *(float*)(value.data() + sizeof(float)) = n.stdev;

        db->Put(write_options,
                leveldb::Slice(key.data(), 2),
                leveldb::Slice(value.data(), sizeof(float) * 2));
    };

    // compact the database
    db->CompactRange(NULL, NULL);

    dirty = false;
};

void LeveldbTrie::add_ngram(const std::vector<std::string>& ngram, int freq)
{
    if(freq == 0)
        return;

    set_dirty();
    
    // set to true if we are sure we need to create the node
    // which means it doesn't exist in leveldb
    bool create = false;

    std::string key;
    key.push_back(0);

    leveldb::WriteBatch write_batch;

    Node node(db, key);
    node.count += freq;
    node.save(&write_batch);

    for(size_t i = 0; i < ngram.size(); i++)
    {
        key[0] = i + 1;
        key.push_back(0);
        key += ngram[i];

        node = Node(db, key, (char*)create);
        if(! node.count)
            create = true;

        node.count += freq;
        node.save(&write_batch);
    };

    auto status = db->Write(write_options, &write_batch);
    assert(status.ok());
};

COUNT LeveldbTrie::query_count(const std::vector<std::string>& ngram)
{
    return search_node(ngram).count;
};

float LeveldbTrie::query_entropy(const std::vector<std::string>& ngram)
{
    set_clean();
    return search_node(ngram).entropy;
};

float LeveldbTrie::query_ev(const std::vector<std::string>& ngram)
{
    set_clean();
    if(ngram.empty())
        return NAN;
    auto node = search_node(ngram);
    if(isnan(node.entropy))
        return NAN;
    auto parent = search_node(std::vector<std::string>(ngram.cbegin(), ngram.cend() - 1));
    if(node.entropy == 0. && parent.entropy == 0.)
        return NAN;
    return node.entropy - parent.entropy;
};

float LeveldbTrie::query_autonomy(const std::vector<std::string>& ngram)
{
    float ev = query_ev(ngram);
    if(isnan(ev) || normalization.size() <= ngram.size())
        return NAN;

    auto& n = normalization[ngram.size()];
    if(! n.stdev)
        return NAN;

    return (ev - n.mean) / n.stdev;
};

void LeveldbTrie::clear()
{
    auto it = db->NewIterator(read_options);
    for(it->SeekToFirst(); it->Valid(); it->Next())
    {
        db->Delete(write_options, it->key());
    }
    dirty = true;
};
