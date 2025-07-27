# Challenge 1B – Approach Explanation

This solution focuses on extracting and ranking the most relevant sections from a collection of PDF travel documents to help a travel planner quickly design a 4-day itinerary for a group of college friends. The pipeline combines structural PDF parsing, semantic search using sentence embeddings, and task-persona-driven relevance scoring.

---

## 1. Problem Understanding

The input includes a set of documents (PDFs), a user persona (e.g., Travel Planner), and a job to be done (e.g., "Plan a trip for a group of friends"). The goal is to identify the top 5 document sections that are most relevant to the job and extract the most informative sentences from them.

---

## 2. PDF Parsing with PyMuPDF

We used `PyMuPDF` to extract structured text from each PDF page. Instead of flat page-wise extraction, we leverage font size and layout metadata to identify section headers. Sections are segmented based on text spans that appear in significantly larger fonts than the body text. This enables grouping text into meaningful sections like “Nightlife and Entertainment” or “Coastal Adventures”.

---

## 3. Known Header Normalization (Optional)

To improve the consistency of section detection across varying formatting styles, we optionally cross-reference section headers with a curated list of `KNOWN_HEADERS`. This helps ensure that semantically meaningful sections like “Culinary Experiences” or “Travel Tips” are reliably captured even if the document format varies slightly.

---

## 4. Semantic Ranking using Sentence Embeddings

Each section’s content is transformed into a vector using the `sentence-transformers/all-MiniLM-L6-v2` model. The query is constructed from both the persona and task, e.g., “Persona: Travel Planner. Job: Plan a trip of 4 days for 10 college friends.” This query is also embedded and compared against all section vectors using cosine similarity.

To ensure diversity in the output, we optionally select the top-ranking section from each document instead of purely top-5 global matches. This avoids output being dominated by one document and improves overall relevance.

---

## 5. Subsection Sentence Refinement

For each selected section, the content is further split into sentences. These are scored individually for relevance using the same embedding-based similarity scoring. The top 2–3 sentences are extracted to provide a concise summary or highlight from the section.

---

## 6. Output Structure

The final output is a structured JSON containing:

- Metadata about the request and documents,
- Top 5 extracted sections with source page and document info,
- Refined text summaries for each section.

---

## 7. Deployment

The solution is packaged into a Docker container (AMD64, CPU-only) with no external network access. It reads PDFs and input JSON from the `/input` directory and `input1.json` respectively, and writes the output JSON to `output.json`, fully compliant with the evaluation constraints.
