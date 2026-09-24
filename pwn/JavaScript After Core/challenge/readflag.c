#include <stdio.h>
#include <stdlib.h>

int main(void)
{
    FILE *f = fopen("flag.txt", "r");
    if (!f) {
        perror("flag.txt");
        return 1;
    }

    char buf[256];
    if (fgets(buf, sizeof(buf), f))
        printf("%s", buf);
    fclose(f);
    return 0;
}
