import re
import random
import string

# 出力後の属性値の改行を保持するための処理


def random_string(length: int) -> str:
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
                identifier = f'"{random_string(16)}"'
                if identifier not in self.items and identifier not in xml_text:
                    break
            self.items[identifier] = content
            return f'={identifier}'

        return _pattern.sub(repl, xml_text)

    def restore(self, xml_text: str) -> str:
        # ランダム文字列のIDを戻す
        for k, v in self.items.items():
            xml_text = xml_text.replace(k, v, 1)
        return xml_text
