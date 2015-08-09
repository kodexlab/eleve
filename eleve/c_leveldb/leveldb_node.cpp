#include "leveldb_node.hpp"
#include <array>
#include <iostream>

Node::Node(leveldb::DB* db, const std::string& key, const char* data): db(db), key(key), count(0), entropy(NAN)
{
    if(data == nullptr)
    {
        std::string value;
        auto s = db->Get(read_options, leveldb::Slice(key), &value);
        if(! s.ok())
        {
            assert(s.IsNotFound());
        }
        else
        {
            assert(value.size() == sizeof(count) + sizeof(entropy));
            count = *(COUNT*)value.data();
            entropy = *(float*)(value.data() + sizeof(count));
        }
    }
    else if(data != (char*)1)
    {
        count = *(COUNT*)data;
        entropy = *(float*)(data + sizeof(count));
    }
};

void Node::save(leveldb::WriteBatch* batch) const
{
    std::array<char, sizeof(count) + sizeof(entropy)> data;
    *(COUNT*)data.data() = count;
    *(float*)(data.data() + sizeof(count)) = entropy;

    if(batch == nullptr)
    {
        auto status = db->Put(write_options, key, leveldb::Slice(data.data(), data.size()));
        assert(status.ok());
    }
    else
    {
        batch->Put(key, leveldb::Slice(data.data(), data.size()));
    }
};

std::string Node::begin_childs() const
{
    std::string s(key);
    s[0]++;
    s.push_back(0);
    return std::move(s);
};

std::string Node::end_childs() const
{
    std::string s(key);
    s[0]++;
    s.push_back(1);
    return std::move(s);
};

void Node::update_entropy(std::set<std::string>& terminals)
{
    if(count == 0)
    {
        entropy = NAN;
        return;
    }

    float e = 0;
    COUNT sum_counts = 0;
    
    auto it = db->NewIterator(read_options);
    auto end = end_childs();
    for(it->Seek(leveldb::Slice(begin_childs())); it->Valid() && it->key().compare(end) < 0; it->Next())
    {
        Node child = Node(db, it->key().ToString(), it->value().data());

        if(child.count == 0)
            continue;

        sum_counts += child.count;
        
        const std::string key_end = std::string(child.key.begin() + child.key.rfind((char)0) + 1, child.key.end());
        
        if(terminals.count(key_end))
        {
            e += (child.count / float(count)) * log2f(count);
        }
        else
        {
            e -= (child.count / float(count)) * log2f(child.count / float(count));
        }
    }
    assert(e >= 0);
    if(! sum_counts)
    {
        e = NAN;
    }
    else
    {
        assert(sum_counts == count);
    }

    if(e != entropy && !(isnan(entropy) && isnan(e)))
    {
        entropy = e;
        save();
    }
};
