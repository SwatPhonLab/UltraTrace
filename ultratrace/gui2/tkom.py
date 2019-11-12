import itertools
import re


class TKMLError(Exception): pass

class TKMLLexerError(TKMLError): pass
class TKMLParserError(TKMLError): pass

class Token:
    def __init__(self, content):
        self.content = content
    def __repr__(self):
        return f'{type(self).__name__}<{self.content}>'

class OpenParen(Token): pass
class CloseParen(Token): pass
class Identifier(Token): pass
class VariableIdentifier(Token): pass
class StringLiteral(Token): pass

valid_identifiers = set(['root', 'div', 'id', 'label', 'text',
    'button', 'dropdown', 'var', 'input', 'listbox', 'icon', 'canvas'])

def lex_tkml(filename):

    OPEN_PAREN = re.compile(r'^\(')
    CLOSE_PAREN = re.compile(r'^\)')
    WHITESPACE = re.compile(r'^\s')
    DOUBLE_QUOTE = re.compile(r'^"')
    VAR_IDENT = re.compile(r'^[\$a-z]')
    IDENT = re.compile(r'^[a-z_]')

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
                yield OpenParen(char)

            elif CLOSE_PAREN.match(char):
                yield CloseParen(char)

            elif DOUBLE_QUOTE.match(char):
                token += char
                char = getchar()
                while DOUBLE_QUOTE.match(char) is None:
                    token += char
                    char = getchar()
                token += char
                yield StringLiteral(token)
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
                if token not in valid_identifiers:
                    raise TKMLLexerError()
                yield Identifier(token)
                if matched_close_paren:
                    yield CloseParen(')')
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
                yield VariableIdentifier(token)
                if matched_close_paren:
                    yield CloseParen(')')
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
            children = []
            tokens, peeks = itertools.tee(tokens)
            while not isinstance(peek(tokens), CloseParen):
                children.append(parse_tokens(tokens, depth + 1))
            next(tokens)
            return children
        elif isinstance(token, CloseParen):
            raise TKMLParserError('unexpected )')
        else:
            return token

    except StopIteration:
        raise TKMLParserError('unexpected EOF')

if __name__ == '__main__':

    tokens = lex_tkml('./layout.tkml')
    parse_tree = parse_tokens(tokens)
    print(parse_tree)
