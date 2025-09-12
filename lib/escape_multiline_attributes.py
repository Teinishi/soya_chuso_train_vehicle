import re
import random
import string
import html

# 出力後の属性値の改行を保持するための処理


def _random_string(length: int) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=length))


# 改行を1個以上含む属性値
_pattern = re.compile(
    r'=((?P<content1>"[^"\n]*\n[^"]*")|(?P<content2>\'[^\'\n]*\n[^\']*\'))')


class EscapeMultilineAttributes:
    items: dict[str, str]

    def __init__(self):
        self.items = {}

    def escape(self, xml_text: str) -> str:
        # ランダム文字列のIDに置換
        def repl(m: re.Match[str]) -> str:
            content = m.group("content1") or m.group("content2")
            while True:
                identifier = _random_string(16)
                if identifier not in self.items and identifier not in xml_text:
                    break
            self.items[identifier] = content
            return f'="{identifier}"'

        return _pattern.sub(repl, xml_text)

    def restore(self, xml_text: str) -> str:
        # ランダム文字列のIDを戻す
        for k, v in self.items.items():
            xml_text = xml_text.replace(f'"{k}"', v, 1)
        return xml_text

    def restore_value(self, value_text: str, unescape=True) -> str:
        if value_text in self.items:
            value = self.items[value_text][1:-1]
            if unescape:
                value = html.unescape(value)
            return value
        else:
            return value_text
