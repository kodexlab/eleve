all: eleve_trie.so

eleve_trie.so:
	clang++ -Wall -O2 -lboost_python3 -lpython3.4m -I/usr/include/python3.4m --std=c++11 -shared -fPIC -o eleve_trie.so *.cpp

clean:
	rm eleve_trie.so
