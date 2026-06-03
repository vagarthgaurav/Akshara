CC      = gcc
CFLAGS  = -std=c99 -Wall -Wextra -Wpedantic -I..

SEG_SRCS   = test_segmenter.c ../segmenter.c
SEG_TARGET = test_segmenter

LUT_SRCS   = test_lookup.c ../aks_parser.c ../lookup.c
LUT_TARGET = test_lookup

BLT_SRCS   = test_blit.c ../aks_parser.c ../lookup.c ../segmenter.c ../blit.c
BLT_TARGET = test_blit

.PHONY: all run clean

all: $(SEG_TARGET) $(LUT_TARGET) $(BLT_TARGET)

$(SEG_TARGET): $(SEG_SRCS)
	$(CC) $(CFLAGS) -o $@ $^

$(LUT_TARGET): $(LUT_SRCS)
	$(CC) $(CFLAGS) -o $@ $^

$(BLT_TARGET): $(BLT_SRCS)
	$(CC) $(CFLAGS) -o $@ $^

run: all
	./$(SEG_TARGET)
	./$(LUT_TARGET)
	./$(BLT_TARGET)

clean:
	rm -f $(SEG_TARGET) $(LUT_TARGET) $(BLT_TARGET)
