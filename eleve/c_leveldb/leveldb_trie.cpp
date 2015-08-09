#include "leveldb_trie.hpp"
#include <array>

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

    auto it = db->NewIterator(leveldb::ReadOptions());
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

    assert(normalization.empty());

    auto root = search_node(std::vector<std::string>());
    update_stats_rec(NAN, 0, root);

    for(size_t i = 0; i < normalization.size(); i++)
    {
        auto n = normalization[i];
        if(n.count == 0)
            continue;
        n.stdev = sqrtf(n.stdev / float(n.count));

        std::array<char, 2> key;
        key[0] = 0xff;
        key[1] = i;

        std::array<char, sizeof(float) * 2> value;
        *(float*)value.data() = n.mean;
        *(float*)(value.data() + sizeof(float)) = n.stdev;

        db->Put(leveldb::WriteOptions(),
                leveldb::Slice(key.data(), 2),
                leveldb::Slice(value.data(), sizeof(float) * 2));
    };

    normalization.clear();
    dirty = false;
};

void LeveldbTrie::add_ngram(const std::vector<std::string>& ngram, int freq)
{
    if(freq == 0)
        return;

    dirty = true;
    
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

    auto status = db->Write(leveldb::WriteOptions(), &write_batch);
    assert(status.ok());
};

COUNT LeveldbTrie::query_count(const std::vector<std::string>& ngram)
{
    return search_node(ngram).count;
};

float LeveldbTrie::query_entropy(const std::vector<std::string>& ngram)
{
    check_dirty();
    return search_node(ngram).entropy;
};

float LeveldbTrie::query_ev(const std::vector<std::string>& ngram)
{
    check_dirty();
    if(! ngram.size())
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
    if(isnan(ev))
        return NAN;

    float mean, stdev;
    // read mean and stdev
    {
        std::array<char, 2> key;
        key[0] = 0xff;
        key[1] = ngram.size();
        std::string value;
        auto s = db->Get(leveldb::ReadOptions(), leveldb::Slice(key.data(), 2), &value);
        if(! s.ok())
        {
            return NAN;
        }
        assert(value.size() == sizeof(float) * 2);
        mean = *(float*)value.data();
        stdev = *(float*)(value.data() + sizeof(float));
    }

    return (ev - mean) / stdev;
};

void LeveldbTrie::clear()
{
    auto it = db->NewIterator(leveldb::ReadOptions());
    auto write_options = leveldb::WriteOptions();
    for(it->SeekToFirst(); it->Valid(); it->Next())
    {
        db->Delete(write_options, it->key());
    }
    dirty = true;
};
