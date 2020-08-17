#include "bb.h"
#include <stdio.h>
#include <stdlib.h>

const int32_t n = 2;

int32_t box2_ping(int32_t a) {
    return a + n;
}

int32_t box2_ping_import(int32_t a) {
    return sys_ping(a) + n;
}

int32_t box2_ping_abort(int32_t a) {
    if (!a) {
        exit(-n);
    }

    printf("box%d: should not reach here!\n", n);
    return n;
}

int box2_hello(void) {
    printf("box%d says hello!\n", n);
    return 0;
}
