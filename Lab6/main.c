#include <stdio.h>
#include <ctype.h>
#include <stdlib.h>
#include <string.h>

/* 
 * Lab 6: Intermediate Code Generation (TAC)
 * Student: Nchinde Tandjong Josue (UBaEP063)
 */

char *input_ptr;
char lookahead;
int temp_count = 0;

// Function to generate a new temporary variable (t1, t2...)
char* new_temp() {
    char* temp = (char*)malloc(5);
    sprintf(temp, "t%d", ++temp_count);
    return temp;
}

void next() {
    lookahead = *input_ptr++;
    while(lookahead == ' ' || lookahead == '\t') { lookahead = *input_ptr++; }
}

void match(char expected) {
    if (lookahead == expected) next();
    else { printf("Error: Expected '%c'\n", expected); exit(1); }
}

char* term();
char* factor();
char* expr();

// Factor -> NUM | (Expr)
char* factor() {
    char* temp = (char*)malloc(10);
    if (isdigit(lookahead)) {
        int val = 0;
        while(isdigit(lookahead)) {
            val = val * 10 + (lookahead - '0');
            next();
        }
        sprintf(temp, "%d", val);
        return temp;
    } else if (lookahead == '(') {
        match('(');
        temp = expr();
        match(')');
        return temp;
    }
    return NULL;
}

// Term -> Factor * Factor
char* term() {
    char* left = factor();
    while (lookahead == '*' || lookahead == '/') {
        char op = lookahead;
        match(op);
        char* right = factor();
        
        char* result = new_temp();
        printf("%s = %s %c %s\n", result, left, op, right);
        left = result;
    }
    return left;
}

// Expr -> Term + Term
char* expr() {
    char* left = term();
    while (lookahead == '+' || lookahead == '-') {
        char op = lookahead;
        match(op);
        char* right = term();
        
        char* result = new_temp();
        printf("%s = %s %c %s\n", result, left, op, right);
        left = result;
    }
    return left;
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: ./codegen \"3+4*5\"\n");
        return 1;
    }
    input_ptr = argv[1];
    next();
    printf("--- Three Address Code (TAC) ---\n");
    expr();
    return 0;
}
