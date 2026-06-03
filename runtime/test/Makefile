CC      = gcc
CFLAGS  = -std=c99 -Wall -Wextra -Wpedantic -I..

SEG_SRCS   = test_segmenter.c ../segmenter.c
SEG_TARGET = test_segmenter

LUT_SRCS   = test_lookup.c ../aks_parser.c ../lookup.c
LUT_TARGET = test_lookup

.PHONY: all run clean

all: $(SEG_TARGET) $(LUT_TARGET)

$(SEG_TARGET): $(SEG_SRCS)
	$(CC) $(CFLAGS) -o $@ $^

$(LUT_TARGET): $(LUT_SRCS)
	$(CC) $(CFLAGS) -o $@ $^

run: all
	./$(SEG_TARGET)
	./$(LUT_TARGET)

clean:
	rm -f $(SEG_TARGET) $(LUT_TARGET)
