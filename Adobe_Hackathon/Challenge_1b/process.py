import fitz  # PyMuPDF
import re
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from datetime import datetime

# -------------------- CONFIG --------------------
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
INPUT_JSON_PATH = "input1.json"
OUTPUT_JSON_PATH = "output.json"
TOP_K_SECTIONS = 5
TOP_K_SENTENCES = 3

# ------------------ SECTION HEADERS ------------------
KNOWN_HEADERS = [
    "Introduction", "Conclusion", "Festivals and Celebrations",
    "Culinary Traditions", "Traditional Sports and Games",
    "Coastal Adventures", "Cultural Experiences", "Outdoor Activities",
    "Wine Tasting", "Packing for All Seasons", "Packing for Kids",
    "Tips and Tricks for Packing", "Special Considerations",
    "Family-Friendly Activities", "Music and Dance", "Historical Sites",
    "Nightlife and Entertainment", "Religious and Spiritual Traditions",
    "Comprehensive Guide to Major Cities in the South of France",
    "General Packing Tips and Tricks", "Culinary Experiences"
]

# -------------------- PARSER --------------------
class PDFParser:
    def __init__(self, filepath):
        self.filepath = filepath
        self.doc = fitz.open(filepath)
        self.text = "\n".join(page.get_text() for page in self.doc)

    def extract_sections_by_headers(self):
        sections = []
        pattern = '|'.join(re.escape(h) for h in KNOWN_HEADERS)
        regex = re.compile(rf'(?P<header>{pattern})\s*\n', re.IGNORECASE)

        matches = list(regex.finditer(self.text))
        for i, match in enumerate(matches):
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(self.text)
            content = self.text[start:end].strip()
            sections.append({
                "title": match.group('header'),
                "content": content,
                "page": 1  # approximate
            })

        return sections

# -------------------- RANKING --------------------
def compute_similarity(query_emb, embeddings):
    return np.dot(embeddings, query_emb)

# -------------------- MAIN --------------------
def process():
    with open(INPUT_JSON_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)

    persona = config['persona']['role']
    job = config['job_to_be_done']['task']
    pdf_list = config['documents']
    query = f"Persona: {persona}. Job: {job}."

    model = SentenceTransformer(MODEL_NAME)
    query_emb = model.encode(query, normalize_embeddings=True)

    all_sections = []
    for doc in pdf_list:
        filepath = doc['filename']
        title = doc['title']
        print(f"[INFO] Parsing {filepath}")
        parser = PDFParser(filepath)
        sections = parser.extract_sections_by_headers()
        if not sections:
            print(f"[WARNING] No sections found in {filepath}")
        for sec in sections:
            sec["document"] = filepath
            sec["full_title"] = title
            all_sections.append(sec)

    if not all_sections:
        print("Error: No section text to encode. Exiting.")
        return

    section_texts = [s["title"] + ". " + s["content"] for s in all_sections]
    section_embeddings = model.encode(section_texts, normalize_embeddings=True)
    similarities = compute_similarity(query_emb, section_embeddings)
    doc_best = {}
    for idx, sec in enumerate(all_sections):
        doc = sec["document"]
        sim = similarities[idx]
        if doc not in doc_best or sim > doc_best[doc][1]:
            doc_best[doc] = (idx, sim)

    # Get top scoring section from each document
    top_indices = [v[0] for v in sorted(doc_best.values(), key=lambda x: x[1], reverse=True)[:TOP_K_SECTIONS]]


    extracted_sections = []
    subsection_analysis = []

    for rank, idx in enumerate(top_indices, start=1):
        sec = all_sections[idx]
        extracted_sections.append({
            "document": sec["document"],
            "section_title": sec["title"],
            "importance_rank": rank,
            "page_number": sec["page"]
        })

        sentences = re.split(r'(?<=[.!?]) +', sec["content"])
        sent_embeddings = model.encode(sentences, normalize_embeddings=True)
        sent_scores = compute_similarity(query_emb, sent_embeddings)
        top_sent_idx = np.argsort(sent_scores)[::-1][:TOP_K_SENTENCES]

        refined_text = " ".join([sentences[i] for i in top_sent_idx])
        subsection_analysis.append({
            "document": sec["document"],
            "refined_text": refined_text,
            "page_number": sec["page"]
        })

    output = {
        "metadata": {
            "input_documents": [doc["filename"] for doc in pdf_list],
            "persona": persona,
            "job_to_be_done": job,
            "timestamp": datetime.utcnow().isoformat()
        },
        "extracted_sections": extracted_sections,
        "subsection_analysis": subsection_analysis
    }

    with open(OUTPUT_JSON_PATH, "w", encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"[SUCCESS] Output written to {OUTPUT_JSON_PATH}")

# ------------------- ENTRY -------------------
if __name__ == "__main__":
    process()
