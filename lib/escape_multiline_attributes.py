import re
import random
import string
import html

# 出力後の属性値の改行を保持するための処理


# 改行を1個以上含む属性値
_pattern = re.compile(
    r'=((?P<content1>"[^"\n]*\n[^"]*")|(?P<content2>\'[^\'\n]*\n[^\']*\'))')

def _random_string(length: int) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=length))

class EscapeMultilineAttributes:
    _original_text: list[str]
    items: dict[str, str]

    def __init__(self):
        self._original_text = []
        self.items = {}

    def add(self, text: str, escape: bool = True) -> str:
        if escape:
            text = f'"{html.escape(text)}"'

        while True:
            identifier = _random_string(16)
            if identifier not in self.items and not any([identifier in o for o in self._original_text]):
                break
        self.items[identifier] = text
        return identifier


    def escape(self, xml_text: str) -> str:
        self._original_text.append(xml_text)
        # ランダム文字列のIDに置換
        def repl(m: re.Match[str]) -> str:
            identifier = self.add(m.group("content1") or m.group("content2"), escape=False)
            return f'="{identifier}"'

        return _pattern.sub(repl, xml_text)

    def restore(self, xml_text: str) -> str:
        # ランダム文字列のIDを戻す
        for k, v in self.items.items():
            xml_text = xml_text.replace(f'"{k}"', v).replace(f"'{k}'", v)
        return xml_text

    def restore_value(self, value_text: str, unescape=True) -> str:
        if value_text in self.items:
            value = self.items[value_text][1:-1]
            if unescape:
                value = html.unescape(value)
            return value
        else:
            return value_text
