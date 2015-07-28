all: memory_trie.so

memory_trie.so: *.cpp *.hpp
	clang++ -Wall -O2 -lboost_python3 -lpython3.4m -I/usr/include/python3.4m --std=c++11 -shared -fPIC -o memory_trie.so *.cpp

clean:
	rm memory_trie.so
