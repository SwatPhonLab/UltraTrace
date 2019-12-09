import itertools
import re

from abc import ABC, abstractmethod

class TKMLError(Exception): pass

class TKMLLexerError(TKMLError): pass
class TKMLParserError(TKMLError): pass

class ParseContext:
    def __init__(self):
        self.root = None
        self._ids = dict()
        self._classes = dict()
        self._vars = dict()
    def add_id(self, id_node, node):
        if not isinstance(id_node, Id):
            raise TKMLParserError(f'expected Id, got {type(id_node)}')
        if len(id_node.children) != 1:
            raise TKMLParserError(f'expected Id to have 1 child, got {len(id_node.children)}')
        name = id_node.children[0].val
        if name in self._ids:
            raise TKMLParserError(f'cannot have multiple nodes identified by "{name}"')
        self._ids[name] = node
    def add_var(self, varid_node, node):
        if not isinstance(varid_node, VariableIdentifier):
            raise TKMLParserError(f'expected VariableIdentifier, got {type(varid_node)}')
        name = varid_node.val
        if name in self._vars:
            raise TKMLParserError(f'cannot have multiple variables identified by "{name}"')
        self._vars[name] = node
    def get(self, name):
        if name.startswith('$'):
            return self._vars.get(name, None)
        else:
            return self._ids.get(name, None)

class Token(ABC):
    def __init__(self, context, val):
        self.context = context
        self.val = val
        self.parent = None
        self.children = []
    def add_child(self, child):
        if not self.is_valid_child(child):
            raise TKMLParserError(f'cannot add {type(child)} child to {type(self)}')
        if isinstance(child, Id):
            self.context.add_id(child, self)
        if isinstance(child, VariableIdentifier):
            self.context.add_var(child, self)
        child.parent = self
        self.children.append(child)
    @abstractmethod
    def is_valid_child(self, child):
        pass
    def __repr__(self):
        return f'{type(self).__name__}'

class OpenParen(Token):
    def is_valid_child(self, child):
        return False

class CloseParen(Token):
    def is_valid_child(self, child):
        return False

class StringLiteral(Token):
    def is_valid_child(self, child):
        return False
    def __repr__(self):
        return f'"{self.val}"'

class IntLiteral(Token):
    def __init__(self, context, val):
        super().__init__(context, val)
        try:
            self.val = int(val)
        except ValueError:
            raise TKMLLexerError(f'cannot interpret as integer: {val}')
    def is_valid_child(self, child):
        return False
    def __repr__(self):
        return repr(self.val)

class VariableIdentifier(Token):
    def is_valid_child(self, child):
        return False
    def __repr__(self):
        return f'{self.val}'

class Identifier(Token):
    constructors = dict()
    allow_recursive_children = False
    def __init_subclass__(cls):
        name = cls.__name__.lower()
        cls.constructors[name] = cls
    def __new__(cls, context, name):
        if cls == Identifier:
            if name not in cls.constructors:
                raise TKMLLexerError(f'"{name}" has no known constructor')
            return super().__new__(cls.constructors[name])
        else:
            return super().__new__(cls)
    @property
    @staticmethod
    @abstractmethod
    def valid_children():
        pass
    def is_valid_child(self, child):
        return type(child) in self.valid_children \
            or (self.allow_recursive_children and type(child) is type(self))
    def __repr__(self):
        return f'{type(self).__name__}<{",".join(map(repr, self.children))}>'

class Var(Identifier):
    valid_children = [VariableIdentifier]

class Id(Identifier):
    valid_children = [StringLiteral]
class Icon(Identifier):
    valid_children = [StringLiteral]
class Text(Identifier):
    valid_children = [StringLiteral]
class Class(Identifier):
    valid_children = [StringLiteral]

class Rows(Identifier):
    valid_children = [StringLiteral]
class Cols(Identifier):
    valid_children = [StringLiteral]
class Row(Identifier):
    valid_children = [IntLiteral]
class Col(Identifier):
    valid_children = [IntLiteral]
class Sticky(Identifier):
    valid_children = [StringLiteral]

class Attrs(Identifier):
    valid_children = [Rows, Cols, Row, Col, Sticky]
class Defclass(Identifier):
    valid_children = [StringLiteral, Attrs]

class Label(Identifier):
    valid_children = [Id, Text]
class Button(Identifier):
    valid_children = [Id, Text, Icon]
class Dropdown(Identifier):
    valid_children = [Id, Var]
class Input(Identifier):
    valid_children = [Id, Var]
class Listbox(Identifier):
    valid_children = [Id]
class Canvas(Identifier):
    valid_children = [Id]
class Div(Identifier):
    valid_children = [Canvas, Listbox, Input, Dropdown, Button, Label, Class, Attrs, Text, Icon, Id, Var]
    allow_recursive_children = True
class Root(Identifier):
    valid_children = [Defclass, Div, Canvas, Listbox, Input, Dropdown, Button, Label, Text, Icon, Id, Var]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.context.root is not None:
            raise TKMLParserError('cannot have multiple roots!')
        self.context.root = self

def lex_tkml(filename):

    OPEN_PAREN = re.compile(r'^\(')
    CLOSE_PAREN = re.compile(r'^\)')
    WHITESPACE = re.compile(r'^\s')
    DOUBLE_QUOTE = re.compile(r'^"')
    VAR_IDENT = re.compile(r'^[\$a-z]')
    IDENT = re.compile(r'^[a-z_]')
    NUMBER = re.compile(r'^[0-9]')

    context = ParseContext()

    with open(filename) as fp:

        def getchar():
            return fp.read(1)

        token = ''

        while True:

            char = getchar()
            if not char:
                return

            if WHITESPACE.match(char):
                continue

            elif OPEN_PAREN.match(char):
                yield OpenParen(context, char)

            elif CLOSE_PAREN.match(char):
                yield CloseParen(context, char)

            elif DOUBLE_QUOTE.match(char):
                char = getchar()
                while DOUBLE_QUOTE.match(char) is None:
                    token += char
                    char = getchar()
                yield StringLiteral(context, token)
                token = ''

            elif NUMBER.match(char):
                matched_close_paren = False
                while NUMBER.match(char):
                    token += char
                    char = getchar()
                    if CLOSE_PAREN.match(char):
                        matched_close_paren = True
                yield IntLiteral(context, token)
                if matched_close_paren:
                    yield CloseParen(context, ')')
                token = ''

            elif IDENT.match(char):
                token += char
                matched_close_paren = False
                while True:
                    char = getchar()
                    if IDENT.match(char):
                        token += char
                    elif WHITESPACE.match(char):
                        break
                    elif CLOSE_PAREN.match(char):
                        matched_close_paren = True
                        break
                    else:
                        raise TKMLLexerError()
                yield Identifier(context, token)
                if matched_close_paren:
                    yield CloseParen(context, ')')
                token = ''

            elif VAR_IDENT.match(char):
                token += char
                matched_close_paren = False
                while True:
                    char = getchar()
                    if IDENT.match(char):
                        token += char
                    elif WHITESPACE.match(char):
                        break
                    elif CLOSE_PAREN.match(char):
                        matched_close_paren = True
                        break
                    else:
                        raise TKMLLexerError()
                yield VariableIdentifier(context, token)
                if matched_close_paren:
                    yield CloseParen(context, ')')
                token = ''

            else:
                raise TKMLLexerError()

def peek(it):
    it, copy = itertools.tee(it)
    return next(copy)

def parse_tokens(tokens, depth=0):
    try:

        token = next(tokens)

        if isinstance(token, OpenParen):
            token = next(tokens)
            tokens, peeks = itertools.tee(tokens)
            while not isinstance(peek(tokens), CloseParen):
                token.add_child(parse_tokens(tokens, depth + 1))
            next(tokens)
            return token
        elif isinstance(token, CloseParen):
            raise TKMLParserError('unexpected )')
        else:
            return token

    except StopIteration:
        raise TKMLParserError('unexpected EOF')

def generate_python(tree):
    pass

if __name__ == '__main__':

    tokens = lex_tkml('./layout.tkml')
    parse_tree = parse_tokens(tokens)
    print(parse_tree)
    print(generate_python(parse_tree))
