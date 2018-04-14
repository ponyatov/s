### @file

import sys
                                            ### @name core object system

## base class                                            
class Sym:
    def __init__(self,V): self.val = V
    def __repr__(self): return self.dump()
    def dump(self,depth=0):
        S = self.pad(depth) + self.head()
        return S
    
## primitive types base class
class Primitive(Sym):
    pass

## container types base class
class Container(Sym):
    pass

## FIFO stack
class Stack(Container):
    pass
                                            
                                            # FVM: FORTH Virtual Machine
D = Stack('DATA') ; print D

                                            # simple FORTH-like syntax parser

import ply.lex  as lex
import ply.yacc as yacc

tokens = ['SYM']

t_ignore = ' \t\r'

t_ignore_COMMENT = '\#.*'

def t_newline(t):
    r'\n'
    t.lexer.lineno += 1

def t_SYM(t):
    r'[a-zA-Z0-9_]+'
    t.value = Sym(t.value) ; return t

def t_error(t): raise SyntaxError(t)

lexer = lex.lex()

def INTERPRET():                                                # interpreter
    while True:
        next = lexer.token()
        if not next: break
        print next

lexer.input(sys.stdin.read())                   # feed source code from stdin
INTERPRET()
