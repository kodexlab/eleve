CC = g++
CFLAGS = -O2 -Wall --std=c++11 -fPIC
LDFLAGS = -shared
INCLUDES = -I/usr/include/python3.4m
LIBS = -lpython3.4m -lleveldb
LIB_NAME = _cleveldb.so
SRC = $(wildcard *.cpp)
OBJ_FILES = $(SRC:.cpp=.o)

all: $(LIB_NAME)

%.o : %.cpp %.hpp
	$(CC) $(CFLAGS) $(INCLUDES) -o $@ -c $<

$(LIB_NAME): $(OBJ_FILES)
	$(CC) $(LDFLAGS) -o $(LIB_NAME) $(OBJ_FILES) $(LIBS)

clean:
	rm $(LIB_NAME) $(OBJ_FILES)
