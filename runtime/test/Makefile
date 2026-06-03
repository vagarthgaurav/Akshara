CC      = gcc
CFLAGS  = -std=c99 -Wall -Wextra -Wpedantic -I..

SRCS    = test_segmenter.c ../segmenter.c
TARGET  = test_segmenter

.PHONY: all run clean

all: $(TARGET)

$(TARGET): $(SRCS)
	$(CC) $(CFLAGS) -o $@ $^

run: $(TARGET)
	./$(TARGET)

clean:
	rm -f $(TARGET)
