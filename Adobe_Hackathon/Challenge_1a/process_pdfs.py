import os
import re
import json
import fitz  # PyMuPDF
import unicodedata
from pathlib import Path
from langdetect import detect

# Configuration
BASE_DIR = Path(__file__).parent.resolve()
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Parameters
NUM_HEADING_LEVELS = 3
BOLD_KEYWORDS = ["Bold", "Demi", "Heavy", "Black", "Sans"]  # broaden for multilingual fonts

class PDFParser:
    def __init__(self, pdf_path):
        self.doc = fitz.open(pdf_path)

    def get_spans(self):
        for page_num, page in enumerate(self.doc, start=1):
            blocks = page.get_text("dict")["blocks"]
            for b in blocks:
                if b['type'] != 0:
                    continue
                for line in b['lines']:
                    for span in line['spans']:
                        text = span['text'].strip()
                        if not text:
                            continue
                        yield {
                            'text': text,
                            'size': round(span['size'], 1),
                            'font': span.get('font', ''),
                            'flags': span.get('flags', 0),
                            'page': page_num
                        }

class OutlineExtractor:
    def __init__(self, parser: PDFParser):
        self.parser = parser
        self.spans = list(self.parser.get_spans())
        self.body_size = self._detect_body_font_size()
        self.language = self._detect_language()

    def _detect_body_font_size(self):
        size_counts = {}
        for s in self.spans:
            size_counts[s['size']] = size_counts.get(s['size'], 0) + 1
        return max(size_counts.items(), key=lambda x: x[1])[0]

    def _detect_language(self):
        for s in self.spans:
            try:
                return detect(s['text'])
            except:
                continue
        return 'unknown'

    def _is_bold(self, font_name):
        return any(kw.lower() in font_name.lower() for kw in BOLD_KEYWORDS)

    def _is_heading_candidate(self, text):
        # For non-Latin, check for CJK or Devanagari
        if self.language in ['ja', 'ko', 'zh', 'hi']:
            return len(text) <= 60  # shorter line heuristics
        if self.language == 'en':
            return text.isupper()
        return False  # fallback

    def extract(self):
        headings = []
        title = None

        for span in self.spans:
            text, size, font, page = span['text'], span['size'], span['font'], span['page']
            level = None

            # Heuristic 1: Numbered headings
            m = re.match(r"^(\d+(?:\.\d+)*)(?:[\s　]+)(.+)", text)
            if m:
                nums = m.group(1).split('.')
                level = f"H{min(len(nums), NUM_HEADING_LEVELS)}"
                text = m.group(2)

            # Heuristic 2: Font size jump
            size_diff = size - self.body_size
            if level is None and size_diff >= 2.0:
                level = "H1" if size_diff >= 4.0 else "H2" if size_diff >= 3.0 else "H3"

            # Heuristic 3: Bold or script-specific rules
            if level is None and (self._is_bold(font) or self._is_heading_candidate(text)):
                level = "H2"

            # Title detection
            if page == 1 and title is None and size_diff >= 4.0:
                title = text
                continue

            if level:
                headings.append({"level": level, "text": text, "page": page})

        if not title:
            first_h1 = next((h for h in headings if h['level'] == 'H1'), None)
            title = first_h1['text'] if first_h1 else Path(self.parser.doc.name).stem

        return {
            "title": title,
            "language": self.language,
            "outline": headings
        }

def main():
    if not INPUT_DIR.exists():
        print("Create a folder named 'input' next to this script and put your PDFs inside.")
        return

    pdf_files = list(INPUT_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDFs found in {INPUT_DIR}")
        return

    for pdf_file in pdf_files:
        try:
            parser = PDFParser(pdf_file)
            extractor = OutlineExtractor(parser)
            result = extractor.extract()

            out_path = OUTPUT_DIR / f"{pdf_file.stem}.json"
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            print(f"[✓] Processed {pdf_file.name} → {out_path.name} (lang: {result['language']})")

        except Exception as e:
            print(f"[✗] Error processing {pdf_file.name}: {e}")

if __name__ == "__main__":
    main()
