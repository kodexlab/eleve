all: memory_trie.so

memory_trie.so: *.cpp *.hpp
	clang++ -O2 -Wall -lboost_python3 -lpython3.4m -I/usr/include/python3.4m --std=c++11 -shared -fPIC -o memory_storage.so *.cpp

clean:
	rm memory_storage.so
