%module cleveldb
%include "std_vector.i"
%include "std_string.i"

namespace std
{
    %template(StrVector) vector<string>;
}

%{
#define SWIG_FILE_WITH_INIT
#include "leveldb_storage.hpp"
#include "leveldb_trie.hpp"
%}
%include "leveldb_storage.hpp"
%include "leveldb_trie.hpp"

