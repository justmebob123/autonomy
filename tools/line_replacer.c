#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_LINE_LENGTH 10000

int replace_line(const char *filename, int line_num, const char *new_content) {
    FILE *file = fopen(filename, "r");
    if (!file) {
        fprintf(stderr, "Error: Cannot open file %s\n", filename);
        return 1;
    }
    
    // Read all lines
    char **lines = NULL;
    int num_lines = 0;
    int capacity = 100;
    lines = malloc(capacity * sizeof(char*));
    
    char buffer[MAX_LINE_LENGTH];
    while (fgets(buffer, sizeof(buffer), file)) {
        if (num_lines >= capacity) {
            capacity *= 2;
            lines = realloc(lines, capacity * sizeof(char*));
        }
        lines[num_lines] = strdup(buffer);
        num_lines++;
    }
    fclose(file);
    
    // Replace the target line
    if (line_num > 0 &amp;&amp; line_num <= num_lines) {
        free(lines[line_num - 1]);
        lines[line_num - 1] = malloc(strlen(new_content) + 2);
        sprintf(lines[line_num - 1], "%s\n", new_content);
    } else {
        fprintf(stderr, "Error: Line number %d out of range (1-%d)\n", line_num, num_lines);
        return 1;
    }
    
    // Write back
    file = fopen(filename, "w");
    if (!file) {
        fprintf(stderr, "Error: Cannot write to file %s\n", filename);
        return 1;
    }
    
    for (int i = 0; i < num_lines; i++) {
        fputs(lines[i], file);
        free(lines[i]);
    }
    fclose(file);
    free(lines);
    
    return 0;
}

int main(int argc, char *argv[]) {
    if (argc != 4) {
        fprintf(stderr, "Usage: %s <filename> <line_number> <new_content>\n", argv[0]);
        return 1;
    }
    
    const char *filename = argv[1];
    int line_num = atoi(argv[2]);
    const char *new_content = argv[3];
    
    return replace_line(filename, line_num, new_content);
}