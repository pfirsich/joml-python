from collections import Counter
import json
import enum

import lark

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


class Node:
    class Type(enum.Enum):
        NULL = enum.auto()
        BOOL = enum.auto()
        INTEGER = enum.auto()
        FLOAT = enum.auto()
        STRING = enum.auto()
        ARRAY = enum.auto()
        DICTIONARY = enum.auto()

    def __init__(self, type, data):
        self.type = type
        self.data = data
        # self.annotation

    def map(self, mapping, default=lambda node: node.data):
        func = mapping.get(self.type, default)
        if self.type == Node.Type.ARRAY:
            return func(Node(self.type, [v.map(mapping, default) for v in self.data]))
        elif self.type == Node.Type.DICTIONARY:
            return func(
                Node(self.type, [(k, v.map(mapping, default)) for k, v in self.data])
            )
        else:
            return func(self)

    @staticmethod
    def unpack_dict(node):
        keys = [item[0] for item in node.data]
        dups = Counter(keys) - Counter(set(keys))
        if len(dups) > 0:
            raise ValueError(
                "Duplicate keys: {}".format(
                    ", ".join("'{}' ({} times)".format(key, dups[key]) for key in dups)
                )
            )
        return dict(node.data)

    def unpack(self):
        return self.map({Node.Type.DICTIONARY: lambda node: Node.unpack_dict(node)})

    @staticmethod
    def full_unpack_default(node):
        return {"type": node.type.name, "value": node.data}

    def full_unpack(self):
        return self.map({}, lambda node: Node.full_unpack_default(node))

    def __str__(self):
        return "Node({}, {})".format(
            str(self.type), self.map({}, lambda node: str(node.data))
        )


class NodeTransformer(lark.Transformer):
    def __init__(self):
        super().__init__()

    kvpairs = lambda self, children: Node(Node.Type.DICTIONARY, children)
    array = lambda self, children: Node(Node.Type.ARRAY, list(children))
    null = lambda self, _: Node(Node.Type.NULL, None)
    bool = lambda self, children: Node(Node.Type.BOOL, children[0] == "true")
    key = lambda self, children: str(children[0])
    kvpair = tuple
    integer = lambda self, children: Node(Node.Type.INTEGER, int(children[0], 0))
    float = lambda self, children: Node(Node.Type.FLOAT, float(children[0]))
    string = lambda self, children: Node(Node.Type.STRING, children[0][1:-1])


def get_parser():
    if not hasattr(get_parser, "parser"):
        get_parser.parser = lark.Lark(grammar, parser="earley", debug=True,)
    return get_parser.parser


def loads(s: str):
    try:
        tree = get_parser().parse(s)
        return NodeTransformer().transform(tree)
    except lark.exceptions.UnexpectedInput as exc:
        raise ParseError(exc, s) from exc


def load(file):
    return loads(file.read())
