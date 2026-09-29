"""Keyword search across the documents in a case.

Documents are split into overlapping passages, and passages are ranked against the query
with TF-IDF weighting and cosine similarity. This is keyword matching: it finds passages
that share words with the query (weighted by how rare those words are), not passages that
mean the same thing in different words.
"""

import math
import re
from collections import Counter

from pydantic import BaseModel

TOKEN = re.compile(r"[a-z0-9]+(?:'[a-z]+)?")
STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "by", "with", "as", "at", "be",
    "is", "are", "was", "were", "this", "that", "it", "its", "from", "any", "all", "such", "shall",
    "will", "may", "which", "who", "has", "have", "not", "no", "if", "than", "then", "these", "those",
}


class Passage(BaseModel):
    """A passage of a document that can be searched."""

    passage_id: str
    document_id: str
    file_name: str
    passage_index: int
    text: str


class SearchResult(BaseModel):
    """A passage ranked against a query."""

    passage_id: str
    document_id: str
    file_name: str
    text_snippet: str
    relevance_score: float
    passage_index: int


def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN.findall(text.lower()) if t not in STOPWORDS and len(t) > 1]


class KeywordSearchService:
    """Split documents into passages and rank them by TF-IDF cosine similarity to a query."""

    def split_into_passages(self, text: str, size: int = 400, overlap: int = 80) -> list[str]:
        """Split text into overlapping passages of about `size` characters, ending on word boundaries."""
        clean = text.strip()
        if not clean:
            return []
        if len(clean) <= size:
            return [clean]
        passages: list[str] = []
        start = 0
        while start < len(clean):
            end = min(start + size, len(clean))
            if end < len(clean):
                last_space = clean.rfind(" ", start, end)
                if last_space > start:
                    end = last_space
            piece = clean[start:end].strip()
            if piece:
                passages.append(piece)
            if end >= len(clean):
                break
            start = max(end - overlap, start + 1)
        return passages

    def search(self, query: str, passages: list[Passage], top_k: int = 5) -> list[SearchResult]:
        """Return the `top_k` passages most similar to the query. Passages sharing no
        words with the query are left out."""
        query_terms = Counter(tokenize(query))
        if not query_terms or not passages:
            return []

        passage_terms = [Counter(tokenize(p.text)) for p in passages]
        n = len(passages)
        doc_freq: Counter[str] = Counter()
        for terms in passage_terms:
            doc_freq.update(terms.keys())
        idf = {term: math.log((1 + n) / (1 + df)) + 1 for term, df in doc_freq.items()}

        def weights(terms: Counter[str]) -> dict[str, float]:
            return {t: (1 + math.log(c)) * idf.get(t, math.log(1 + n) + 1) for t, c in terms.items()}

        q = weights(query_terms)
        q_norm = math.sqrt(sum(v * v for v in q.values()))
        results: list[SearchResult] = []
        for passage, terms in zip(passages, passage_terms, strict=True):
            w = weights(terms)
            dot = sum(q[t] * w[t] for t in q if t in w)
            if dot == 0:
                continue
            norm = math.sqrt(sum(v * v for v in w.values()))
            results.append(SearchResult(
                passage_id=passage.passage_id,
                document_id=passage.document_id,
                file_name=passage.file_name,
                text_snippet=passage.text,
                relevance_score=round(dot / (q_norm * norm), 4),
                passage_index=passage.passage_index,
            ))
        results.sort(key=lambda r: r.relevance_score, reverse=True)
        return results[:top_k]


search_service = KeywordSearchService()
