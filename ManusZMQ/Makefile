CXX      := g++
CXXFLAGS := -g --std=c++17
LDFLAGS  := -L../ManusSDK/lib -lManusSDK -lncurses -lzmq -Wl,-rpath=../ManusSDK/lib
OBJ_DIR  := ./objects
TARGET   := ManusZMQ.out
INCLUDE  := -I../ManusSDK/include -I..

SRC      := ManusZMQ.cpp ../ClientPlatformSpecific.cpp
OBJECTS  := $(OBJ_DIR)/ManusZMQ.o $(OBJ_DIR)/ClientPlatformSpecific.o
DEPS     := $(OBJECTS:.o=.d)

all: $(OBJ_DIR) $(TARGET)

$(OBJ_DIR):
	mkdir -p $(OBJ_DIR)

$(OBJ_DIR)/ManusZMQ.o: ManusZMQ.cpp
	$(CXX) $(CXXFLAGS) $(INCLUDE) -c $< -MMD -o $@

$(OBJ_DIR)/ClientPlatformSpecific.o: ../ClientPlatformSpecific.cpp
	$(CXX) $(CXXFLAGS) $(INCLUDE) -c $< -MMD -o $@

$(TARGET): $(OBJECTS)
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LDFLAGS)

-include $(DEPS)

clean:
	rm -f $(TARGET)
	rm -rf $(OBJ_DIR)

.PHONY: all clean
