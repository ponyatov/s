## @file

import sys
print sys.argv

### @defgroup sym Object system
### @{

### base class
class Sym:
    def __init__(self,T,V):
        self.tag = T ; self.val = V
        self.nest = [] ; self.attr = {}
    def __lshift__(self,o): return self.push(o)
    def push(self,o):
        self.nest.append(o) ; return self
    def pop(self):
        return self.nest.pop()
    def __getitem__(self,key):
        return self.attr[key]
    def __setitem__(self,key,val):
        self.attr[key] = val ; return self
    def __repr__(self): return self.dump()
    def dump(self,depth=0):
        S = self.pad(depth) + self.head()
        for i in self.attr:
            S += self.pad(depth+1) + \
                self.attr[i].head(prefix='%s = '%i)
        for j in self.nest:
            S += j.dump(depth+1)
        return S
    def pad(self,N): return '\n'+'\t'*N
    def head(self,prefix=''): return '%s<%s:%s>'%(prefix,self.tag,self.val)
    
### primitive types
class Primitive(Sym):
    ### key feature: all primitive types evaluates into itself
    def __call__(self): D << self

### string
class String(Primitive):
    def __init__(self,V):
        Primitive.__init__(self, 'str', V)
        
class Number(Primitive):
    def __init__(self,V):
        Primitive.__init__(self, 'num', float(V))
        
class Integer(Number):
    def __init__(self,V):
        Primitive.__init__(self, 'int', int(V))

class Hex(Number):
    def __init__(self,V):
        Primitive.__init__(self, 'hex', int(V[2:],0x10))
        ### hex numbers has width defined by number of digits
        self.width = len(V)-2
        self.hexmask = '0x%%.%sX' % self.width
        self.headmask = '%%s<%%s:%s>' % self.hexmask
    def head(self,prefix=''):
        return self.headmask % (prefix,self.tag,self.val)
    def save(self): return self.hexmask % self.val

### data containers
class Container(Sym):
    pass

### constant
class Const(Container):
    def __init__(self,Name,Val):
        Container.__init__(self, 'const', Name)
        self << Val
    def head(self,prefix):
        return self.nest[0].head(prefix='%s -> '%Container.head(self,prefix))
    ### marshaling to source code
    def save(self):
        return '%s const %s\n' % (self.nest[0].save(),self.val)

### FIFO stack
class Stack(Container):
    def __init__(self,V):
        Container.__init__(self, 'stack', V)

### unordered key:value storage
class Map(Container):
    def __init__(self,V):
        Container.__init__(self, 'map', V)
    def push(self,o):
        if type(o) == type(BYE): # hack to allow W << FN syntax
            self[o.__name__] = Fn(o)
        else: Container.push(o)
    def __iter__(self): return self.attr.__iter__()

### active elements
class Active(Sym):
    pass

### function (compiled into VM)
class Fn(Active):
    def __init__(self,F):
        Active.__init__(self, 'fn', F.__name__)
        self.fn = F
    def __call__(self): self.fn()

### syntax elements
class Syntax(Sym):
    pass

### lexeme (token) = word name
class Token(Syntax):
    def __init__(self,V,lineno):
        Syntax.__init__(self, 'token', V)
        self['line'] = lineno
    def head(self,prefix=''):
        return '%s<%s:%s> line:%s'%(prefix,self.tag,self.val,self['line'])
    
## @}
                            
### data stack
D = Stack('DATA')
### global vocabulary (system-wide word definitions)
W = Map('FORTH')

### `BYE` stop system
def BYE(): sys.exit(0)
W << BYE

### `SAVE` dump system into marshaling form
def SAVE():
    dump = open('save','w')
    for i in W:
        if W[i].tag not in ['fn']:
            print >>dump,W[i].save()
    print >>dump,'save\nwords\n'
    dump.close()
W << SAVE

### `?` dump data stack
def DumpStack(): print D
W['?'] = Fn(DumpStack)

def WORDS(): print W
W << WORDS

### syntax parser
### (using lex-like regexp-based lexer generator from PLY library)
import ply.lex  as lex
import ply.yacc as yacc

### tokens
tokens = ['SYM','HEX']

### drop spaces
t_ignore = ' \t\r'

### comments
t_ignore_COMMENT = '\#.*'

### increase line number on every LF
def t_newline(t):
    r'\n'
    t.lexer.lineno += 1
    
### hex number
def t_HEX(t):
    r'0x[0-9A-Fa-f]+'
    t.value = Hex(t.value) ; return t

### parse word name
def t_SYM(t):
    r'[a-zA-Z0-9_\?]+'
    t.value = Token(t.value,t.lexer.lineno) ; return t

### lexer error callback
def t_error(t): raise SyntaxError(t)

### create lexer
lexer = lex.lex()

### compile constant
def CONST():
    Val = D.pop()
    WORD() ; Name = D.pop().val 
    W[Name] = Const(Name,Val)
W << CONST

### `WORD ( -- token:wordname )`
### get next word from source code stream
def WORD():
    next = lexer.token()
    if not next: BYE()
    D << next.value
W << WORD

### `FIND ( token:name -- callable:definition )`
### get executable item in vocabulary by its name
def FIND():
    WN = D.pop()
    if WN.tag in ['hex']: D << WN ; return
    try: D << W[WN.val]
    except KeyError:
        try: D << W[WN.val.upper()]
        except KeyError: raise SyntaxError(WN.head())
W << FIND

### `EXECUTE ( callable: -- ... )` run executable item from stack
def EXECUTE(): D.pop()()
W << EXECUTE

### `INTERPRET` interpreter/compiler
def INTERPRET():                                                
    while True:     # BEGIN/AGAIN
        WORD()
        FIND()
        EXECUTE()
W << INTERPRET

print W

### feed lexer
try:
    SRC = open(sys.argv[1],'r').read()
except IndexError:
    SRC = open('src.src','r').read()
lexer.input(SRC)
INTERPRET()
