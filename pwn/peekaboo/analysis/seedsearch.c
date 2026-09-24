#define _DEFAULT_SOURCE
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#ifdef _OPENMP
#include <omp.h>
#endif

static uint32_t first_and_key(uint32_t seed, unsigned char key[32]) {
    uint32_t state[31];
    int64_t word = seed ? seed : 1;
    state[0] = (uint32_t)word;
    for (int i = 1; i < 31; ++i) {
        word = (16807 * word) % 2147483647;
        state[i] = (uint32_t)word;
    }

    uint32_t value = 0;
    uint32_t first = 0;
    for (int i = 34; i <= 376; ++i) {
        value = state[i % 31] + state[(i - 3) % 31];
        state[i % 31] = value;
        if (i == 344)
            first = value >> 1;
        if (i >= 345)
            key[i - 345] = (unsigned char)(value >> 1);
    }
    return first;
}

int main(int argc, char **argv) {
    if (argc == 2) {
        uint32_t seed = (uint32_t)strtoul(argv[1], NULL, 0);
        unsigned char key[32];
        uint32_t mine = first_and_key(seed, key);
        srand(seed);
        uint32_t theirs = (uint32_t)rand();
        printf("custom=%u glibc=%u\n", mine, theirs);
        return mine != theirs;
    }
    if (argc != 3) {
        fprintf(stderr, "usage: %s START END < target_low22_on_stdin\n", argv[0]);
        return 2;
    }

    uint32_t start = (uint32_t)strtoul(argv[1], NULL, 0);
    uint32_t end = (uint32_t)strtoul(argv[2], NULL, 0);
    uint32_t target;
    if (scanf("%x", &target) != 1)
        return 2;

    #pragma omp parallel for schedule(static)
    for (uint32_t seed = start; seed < end; ++seed) {
        unsigned char key[32];
        uint32_t value = first_and_key(seed, key);
        if ((value & 0x3fffffU) == target) {
            #pragma omp critical
            {
                printf("%06x ", seed);
                for (int i = 0; i < 32; ++i)
                    printf("%02x", key[i]);
                putchar('\n');
                fflush(stdout);
            }
        }
    }
    return 0;
}
