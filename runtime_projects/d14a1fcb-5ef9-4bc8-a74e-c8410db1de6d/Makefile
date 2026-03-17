CC ?= gcc
CFLAGS ?= -O2 -Wall -w
MATIEC_LIB_DIR ?= /Users/apple/Beremiz/matiec/lib
MATIEC_C_DIR := $(MATIEC_LIB_DIR)/C
GENERATED_DIR := generated_c
BUILD_DIR := build
SOURCES := $(wildcard $(GENERATED_DIR)/*.c)
RUNTIME_MAIN := runtime_main.c
SOURCES += $(RUNTIME_MAIN)
OBJECTS := $(patsubst $(GENERATED_DIR)/%.c,$(BUILD_DIR)/%.o,$(SOURCES))
OBJECTS := $(patsubst %.c,$(BUILD_DIR)/%.o,$(OBJECTS))
TARGET := runtime_binary

all: $(TARGET)

$(TARGET): $(OBJECTS)
	$(CC) $(CFLAGS) -o $@ $(OBJECTS)

$(BUILD_DIR)/%.o: $(GENERATED_DIR)/%.c
	@mkdir -p $(BUILD_DIR)
	$(CC) $(CFLAGS) -I $(GENERATED_DIR) -I $(MATIEC_C_DIR) -include $(GENERATED_DIR)/POUS.h -include $(GENERATED_DIR)/LOCATED_VARIABLES.h -c $< -o $@

$(BUILD_DIR)/runtime_main.o: runtime_main.c
	@mkdir -p $(BUILD_DIR)
	$(CC) $(CFLAGS) -I $(GENERATED_DIR) -I $(MATIEC_C_DIR) -include $(GENERATED_DIR)/POUS.h -c $< -o $@

clean:
	rm -rf $(BUILD_DIR) $(TARGET)
