CC = clang++
CFLAGS = -O2 -Wall --std=c++11 -shared -fPIC
INCLUDES = -I/usr/include/python3.4m
LIBS = -lboost_python3 -lpython3.4m
LIB_NAME = cstorages.so
SRC = $(wildcard *.cpp)
OBJ_FILES = $(SRC:.cpp=.o)

all: $(LIB_NAME)

%.o : %.cpp
	$(CC) $(CFLAGS) $(INCLUDES) -o $@ $<

$(LIB_NAME): $(OBJ_FILES)
	$(CC) $(CFLAGS) -o $(LIB_NAME) $(OBJ_FILES) $(LIBS)

clean:
	rm $(LIB_NAME) $(OBJ_FILES)
