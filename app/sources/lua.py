"""A tiny parser for the Lua table literals used by the Inazuma Eleven wiki's data modules
(Module:PlayerData/*, Module:WazaData). Supports: tables {…} with array items and key=value /
["key"]=value fields, strings ("…" / '…' / [[…]]), numbers, true/false/nil, and comments."""
import re

_TOKEN = re.compile(r"""
    (?P<ws>\s+|--\[\[.*?\]\]|--[^\n]*)
  | (?P<lstr>\[\[.*?\]\])
  | (?P<str>"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')
  | (?P<num>-?\d+(?:\.\d+)?)
  | (?P<name>[A-Za-z_][A-Za-z0-9_]*)
  | (?P<sym>[{}=,;\[\]])
""", re.S | re.X)


def _tokens(src):
    pos = 0
    while pos < len(src):
        m = _TOKEN.match(src, pos)
        if not m:
            raise ValueError(f"Unexpected character at {pos}: {src[pos:pos+30]!r}")
        pos = m.end()
        kind = m.lastgroup
        if kind == "ws":
            continue
        yield kind, m.group()


class _Parser:
    def __init__(self, src):
        self.gen = _tokens(src)          # lazy: we stop as soon as the table literal ends
        self.buf = []

    def _fill(self, n):
        while len(self.buf) <= n:
            nxt = next(self.gen, None)
            if nxt is None:
                self.buf.append((None, None))
                break
            self.buf.append(nxt)

    def peek(self, k=0):
        self._fill(k)
        return self.buf[k] if k < len(self.buf) else (None, None)

    def take(self):
        self._fill(0)
        return self.buf.pop(0)

    def value(self):
        kind, v = self.take()
        if kind == "sym" and v == "{":
            return self.table()
        if kind == "str":
            body = v[1:-1]
            return re.sub(r"\\(.)", r"\1", body)
        if kind == "lstr":
            return v[2:-2]
        if kind == "num":
            return float(v) if "." in v else int(v)
        if kind == "name":
            return {"true": True, "false": False, "nil": None}.get(v, v)
        raise ValueError(f"Unexpected token {v!r}")

    def table(self):
        arr, obj = [], {}
        while True:
            kind, v = self.peek()
            if kind == "sym" and v == "}":
                self.take()
                break
            if kind == "sym" and v in ",;":
                self.take()
                continue
            if kind == "name" and self.peek(1) == ("sym", "="):
                self.take(); self.take()
                obj[v] = self.value()
            elif kind == "sym" and v == "[":
                self.take()
                key = self.value()
                self.take()  # ]
                self.take()  # =
                obj[key] = self.value()
            else:
                arr.append(self.value())
        if obj and arr:
            obj["_items"] = arr
            return obj
        return obj if obj else arr


def parse_module(src: str, var: str = None):
    """Return a table literal assigned in a module, e.g. `local PLAYERS={…}` (var="PLAYERS").
    Without `var`, the first non-empty `name={` assignment is used."""
    if var:
        m = re.search(r"\b" + re.escape(var) + r"\s*=\s*\{", src)
    else:
        m = re.search(r"\b[A-Za-z_]\w*\s*=\s*\{(?!\s*\})", src)
    start = m.end() - 1
    p = _Parser(src[start:])
    p.take()
    return p.table()
