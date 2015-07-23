#ifndef _CONFIG_HPP_
#define _CONFIG_HPP_

#include <assert.h>
#include <vector>
#include <memory>
#include <algorithm>

const size_t BLOCK_MAX_SIZE = 128;

typedef uint32_t ID;
typedef uint32_t COUNT;
typedef std::vector<ID>::const_iterator shingle_const_iterator;

#endif
