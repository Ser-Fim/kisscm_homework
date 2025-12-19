import sys
import lark

grammar = r"""
start: (var_decl | top_value)*

var_decl: "set" NAME "=" value

top_value: NAME "=" value

value: dict
     | array
     | const_ref
     | BINARY
     | STRING

dict: "{" [pair ("," pair)* [","] ] "}"

pair: NAME ":" value

array: "array" "(" [value ("," value)* [","] ] ")"

const_ref: "#[" NAME "]"

BINARY: /0[bB][01]+/
STRING: /"[^"]*"/
NAME: /[_a-z][_a-z0-9]*/

%import common.WS
%ignore WS
%ignore /--.*?(?=\n)/
"""

class TOMLTransformer(lark.Transformer):
    def __init__(self):
        super().__init__()
        self.constants = {}

    def BINARY(self, token):
        return int(str(token), 2)

    def STRING(self, token):
        return str(token)[1:-1]

    def NAME(self, token):
        return str(token)

    def value(self, items):
        return items[0]

    def pair(self, items):
        return (items[0], items[1])

    def dict(self, items):
        d = {}
        for name, val in items:
            d[name] = val
        return d

    def array(self, items):
        return list(items)

    def const_ref(self, items):
        name = items[0]
        if name not in self.constants:
            raise ValueError(f"Неизвестная константа: {name}")
        return self.constants[name]

    def var_decl(self, items):
        name, val = items
        self.constants[name] = val
        return None

    def top_value(self, items):
        name, val = items
        return {name: val}

    def start(self, items):
        result = {}
        for item in items:
            if item is not None:

                result.update(item)
        return result


def to_toml(obj):
    if isinstance(obj, dict):
        parts = []
        for k, v in obj.items():
            parts.append(f"{k} = {to_toml(v)}")
        return "{ " + ", ".join(parts) + " }"
    elif isinstance(obj, list):
        parts = [to_toml(x) for x in obj]
        return "[ " + ", ".join(parts) + " ]"
    elif isinstance(obj, str):
        return f'"{obj}"'
    else:
        return str(obj)


def main():
    if len(sys.argv) != 2:
        print("Использование: python main.py <input_file>", file=sys.stderr)
        sys.exit(1)

    path = sys.argv[1]
    try:
        with open(path, encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        print(f"Файл не найден: {path}", file=sys.stderr)
        sys.exit(1)

    try:
        parser = lark.Lark(grammar, parser='lalr')
        tree = parser.parse(text)
        result = TOMLTransformer().transform(tree)
        print(to_toml(result))
    except lark.LarkError as e:
        print(f"Синтаксическая ошибка: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()