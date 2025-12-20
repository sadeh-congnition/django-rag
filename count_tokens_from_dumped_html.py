# Coded by the VS Code Agent using GPT-5 mini model
# No human editing needed to run successfully
from pathlib import Path
from html.parser import HTMLParser
import sys

from utils import dumped_html_path


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._texts = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag.lower() in ("script", "style"):
            self._skip = True

    def handle_endtag(self, tag):
        if tag.lower() in ("script", "style"):
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            text = data.strip()
            if text:
                self._texts.append(text)

    def get_text(self):
        return "\n".join(self._texts)


def extract_text_from_file(path: Path) -> str:
    parser = TextExtractor()
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        content = path.read_text(encoding="latin-1", errors="ignore")
    parser.feed(content)
    return parser.get_text()


def main():
    base = dumped_html_path()
    if not isinstance(base, Path):
        base = Path(str(base))

    if not base.exists() or not base.is_dir():
        print(f"dumped_html_path {base} does not exist or is not a directory", file=sys.stderr)
        sys.exit(1)

    all_texts = []
    for p in sorted(base.iterdir()):
        if p.is_file():
            txt = extract_text_from_file(p)
            all_texts.append(txt)

    combined = "\n\n".join(all_texts)

    try:
        import tiktoken
    except Exception:
        print("tiktoken not installed. Please run: pip install tiktoken", file=sys.stderr)
        print("TOTAL_CHARS:\t" + str(len(combined)))
        sys.exit(2)

    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(combined)
    print("TOTAL_TOKENS:\t" + str(len(tokens)))
    print("TOTAL_CHARS:\t" + str(len(combined)))


if __name__ == "__main__":
    main()
