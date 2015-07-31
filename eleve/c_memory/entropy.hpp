#ifndef _ENTROPY_HPP_
#define _ENTROPY_HPP_
#include "config.hpp"
#include <set>
#include <map>
#include <array>

class Node;

struct HStats
{
    std::set<COUNT> terminals;
    
    struct Normalization
    {
        float mean;
        float stdev;
        COUNT count;
    };

    std::vector<Normalization> normalization;

    std::map<const Node*, float> entropy_cache;
};

#endif
