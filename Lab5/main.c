#include <stdio.h>
#include <ctype.h>
#include <stdlib.h>

/* 
 * Lab 5: Recursive Descent Parser in C
 * Student: Nchinde Tandjong Josue (UBaEP063)
 * 
 * Grammar:
 * expr   -> term ((+|-) term)*
 * term   -> factor ((*|/) factor)*
 * factor -> ( expr ) | Number
 */

char *input_ptr;
char lookahead;

void next() {
    lookahead = *input_ptr++;
    while(isspace((unsigned char)lookahead)) {
        lookahead = *input_ptr++;
    }
}

void match(char expected) {
    if (lookahead == expected) {
        next();
    } else {
        printf("Error: Expected '%c' but found '%c'\n", expected, lookahead);
        exit(1);
    }
}

int expr();
int term();
int factor();

int factor() {
    int val;
    if (isdigit(lookahead)) {
        val = lookahead - '0';
        next();
        // Handle multi-digit numbers
        while(isdigit(lookahead)) {
            val = val * 10 + (lookahead - '0');
            next();
        }
        if (isspace((unsigned char)lookahead)) {
            next();
        }
        return val;
    } else if (lookahead == '(') {
        match('(');
        val = expr();
        match(')');
        return val;
    } else {
        printf("Error: Unexpected character '%c'\n", lookahead);
        exit(1);
    }
}

int term() {
    int val = factor();
    while (isspace((unsigned char)lookahead)) {
        next();
    }
    while (lookahead == '*' || lookahead == '/') {
        if (lookahead == '*') {
            match('*');
            val *= factor();
        } else {
            match('/');
            int divisor = factor();
            if (divisor == 0) {
                printf("Error: Division by zero\n");
                exit(1);
            }
            val /= divisor;
        }
    }
    return val;
}

int expr() {
    int val = term();
    while (isspace((unsigned char)lookahead)) {
        next();
    }
    while (lookahead == '+' || lookahead == '-') {
        if (lookahead == '+') {
            match('+');
            val += term();
        } else {
            match('-');
            val -= term();
        }
    }
    return val;
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Recursive Descent Parser (C Implementation)\n");
        printf("Usage: ./main \"expression\"\n");
        printf("Example: ./main \"3 + 4 * 5\"\n");
        return 1;
    }

    input_ptr = argv[1];
    next(); // Load first character
    
    int result = expr();
    
    if (lookahead == '\0') {
        printf("Parsing Successful! Result: %d\n", result);
    } else {
        printf("Error: Unexpected symbols at end of expression: '%c'\n", lookahead);
    }
    
    return 0;
}
