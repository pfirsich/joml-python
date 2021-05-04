import lark
import json

grammar = r"""
_WS: /[ \t\r\n]/+
_COMMENT: "#" /[^\n]/*
_VALUESEP: ("," | "\n")
KEY: /[^":#{[\s]/ /[^":#]/*
STRING: "\"" (/[^"]*/ | "\\\"") "\""
NULL: "null"
BOOL: "true" | "false"
SIGN: "+" | "-"
DIGIT: "0".."9"
BININTEGER: [SIGN] "0b" ("0" | "1")+
OCTINTEGER: [SIGN] "0o" ("0".."7")+
DECINTEGER: [SIGN] DIGIT+
HEXINTEGER: [SIGN] "0x" ("a".."f" | "A".."F" | DIGIT)+
INTEGER: BININTEGER | OCTINTEGER | HEXINTEGER | DECINTEGER
FLOAT_SPECIAL: [SIGN] ("inf" | "nan")
DECIMAL: [SIGN] (DIGIT+ "." DIGIT* | "." DIGIT+)
EXP: ("e" | "E") [SIGN] DIGIT+
FLOAT_NUMBER: DECINTEGER EXP | DECIMAL [EXP]
FLOAT: FLOAT_SPECIAL | FLOAT_NUMBER

?start: [kvpairs]
key: KEY
kvpair: key ":" value
array: "[" [value (_VALUESEP value)* _VALUESEP?] "]"
?dict: "{" [kvpairs] "}"
kvpairs: kvpair (_VALUESEP kvpair)*
null: NULL
bool: BOOL
integer: INTEGER
float: FLOAT
string: STRING
?value: dict | array | string | integer | float | bool | null

%ignore _WS
%ignore _COMMENT
"""


class ParseError(Exception):
    def __init__(self, lark_exception: lark.exceptions.UnexpectedInput, text: str):
        self.lark_exception = lark_exception
        self.line = lark_exception.line
        self.column = lark_exception.column
        self.cursor = lark_exception.pos_in_stream
        self.state = lark_exception.state
        self.text = text

    def get_context(self):
        return self.lark_exception.get_context(self.text)

    def __str__(self):
        s = "Error at {}:{}:\n{}\n".format(self.line, self.column, self.get_context())
        allowed = self.lark_exception.allowed
        if len(allowed) > 1:
            s += "Expected one of: {}".format(", ".join(allowed))
        else:
            s += "Expected {}".format(list(allowed)[0])
        return s


class Transformer(lark.Transformer):
    def __init__(self, dict_type):
        super().__init__()
        self.dict_type = dict_type

    def kvpairs(self, children):
        return self.dict_type(children)

    array = list
    null = lambda self, _: None
    bool = lambda self, children: children[0] == "true"
    key = lambda self, children: str(children[0])
    kvpair = tuple
    integer = lambda self, children: int(children[0], 0)
    float = lambda self, children: float(children[0])
    string = lambda self, children: children[0][1:-1]


def get_parser():
    if not hasattr(get_parser, "parser"):
        get_parser.parser = lark.Lark(grammar, parser="earley", debug=True,)
    return get_parser.parser


def loads(s: str, dict_type: callable = list):
    try:
        tree = get_parser().parse(s)
        return Transformer(dict_type).transform(tree)
    except lark.exceptions.UnexpectedInput as exc:
        raise ParseError(exc, s) from exc


def load(file, dict_type: callable = list):
    return loads(file.read(), dict_type=dict_type)
