# explanation.md — Multilingual Heading Extraction (Challenge 1a)

This solution addresses **Challenge 1a** of the Adobe India Hackathon, focused on parsing PDF documents and extracting their hierarchical structure (i.e., titles and section headings). The unique challenge tackled in this implementation is ensuring **multilingual robustness**, including support for scripts such as Japanese, Hindi, Chinese, and more.

---

## 🔍 Problem Understanding

Many PDF documents do not contain structured metadata or built-in bookmarks. Instead, their logical structure must be inferred from visual and textual cues. While this is already challenging in English, it becomes even more complex in multilingual documents where cues like capitalization or Latin font conventions may not apply.

---

## 🧠 Core Methodology

The script performs the following high-level steps:

1. **PDF Parsing via PyMuPDF**  
   Each PDF page is scanned for text spans using PyMuPDF’s `get_text("dict")` output. This gives access to font size, font name, and page number, which are crucial for inferring structure.

2. **Language Detection**  
   Using `langdetect`, the script determines the document’s dominant language by analyzing the first few spans of readable text. This is vital for adapting heuristics to language-specific characteristics.

3. **Body Font Size Estimation**  
   The script calculates the most frequent font size across the document to estimate the body text size. This helps identify headings that deviate significantly in size.

4. **Heading Detection via Multi-heuristic Rules**  
   To capture headings reliably across languages, the script applies a layered heuristic system:

   - **Numeric Prefixes** (e.g., `2.3.1 History`) → Used to assign heading levels H1–H3.
   - **Font Size Delta** → Large font sizes above the body size signal potential headings.
   - **Bold/Heavy Font Detection** → Uses a broader set of keywords like "Demi", "Sans", "Heavy" to capture non-English fonts.
   - **Script-Specific Rules** → For languages like Japanese or Hindi, heading detection favors short lines or bold fonts rather than capitalization.

5. **Title Extraction**  
   If a large text appears on page 1, it's assigned as the document title. Otherwise, the first `H1`-level heading is used.

6. **Output Format**  
   The result is saved as JSON with the document’s title, detected language, and an outline of heading-level structured entries with page numbers.

---

## 🌐 Multilingual Capability

This solution does **not rely on ASCII or Latin assumptions**. Instead, it intelligently adapts based on the document's script:

- Handles CJK (Chinese, Japanese, Korean) and Indic languages by avoiding capitalization checks.
- Uses universal formatting cues like font size and boldness.
- Adds language code (e.g., "ja", "hi") to the output JSON for traceability and downstream use.

---

## ✅ Advantages

- Fast and efficient, no heavy NLP or OCR dependencies.
- Works on scanned documents converted with OCR.
- Modular and extensible — easy to plug into other document intelligence systems.
