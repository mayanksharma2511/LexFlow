"""Hybrid Extractive-Abstractive NLP Summarization Service.

Combines TF-IDF sentence scoring (Extractive NLP) with LLM abstractive synthesis
for high-density legal document processing. Operates with strict Python 3.13 type safety.
"""

import math
import re

from pydantic import BaseModel, Field

from app.services.ai.openai_service import openai_service


class ExtractiveSentence(BaseModel):
    """Data model representing an extracted key sentence and its TF-IDF score."""

    sentence: str
    score: float
    original_index: int


class HybridSummaryResult(BaseModel):
    """Data model representing the combined result of hybrid NLP summarization."""

    extractive_sentences: list[ExtractiveSentence]
    abstractive_summary: str
    original_char_count: int
    condensed_char_count: int
    compression_ratio: float = Field(ge=0.0, le=1.0)


class HybridNLPService:
    """Academic-grade Hybrid NLP service combining TF-IDF and LLM pipelines."""

    def __init__(self, stopwords: set[str] | None = None) -> None:
        """Initialize the hybrid NLP service with default English legal stopwords."""
        self._stopwords = stopwords or {
            "a", "an", "the", "and", "or", "but", "if", "because", "as", "until",
            "while", "of", "at", "by", "for", "with", "about", "against", "between",
            "into", "through", "during", "before", "after", "above", "below", "to",
            "from", "up", "upon", "down", "in", "out", "on", "off", "over", "under",
            "again", "further", "then", "once", "here", "there", "when", "where",
            "why", "how", "all", "any", "both", "each", "few", "more", "most",
            "other", "some", "such", "no", "nor", "not", "only", "own", "same",
            "so", "than", "too", "very", "s", "t", "can", "will", "just", "don",
            "should", "now", "d", "ll", "m", "o", "re", "ve", "y", "is", "it",
            "this", "that", "these", "those", "am", "are", "was", "were",
            "be", "been", "being", "have", "has", "had", "having", "do", "does",
            "did", "doing", "shall", "may", "must", "her", "his", "their", "its",
        }

    def _tokenize_sentences(self, text: str) -> list[str]:
        """Split document text into clean sentence tokens.

        Args:
            text: Raw input text.

        Returns:
            List of non-empty sentence strings.
        """
        raw_sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 10]
        return sentences if sentences else ([text.strip()] if text.strip() else [])

    def _tokenize_words(self, sentence: str) -> list[str]:
        """Extract normalized words from a sentence.

        Args:
            sentence: Sentence text string.

        Returns:
            List of lowercase alphanumeric word tokens.
        """
        words = re.findall(r"\b[a-zA-Z0-9]+\b", sentence.lower())
        return [w for w in words if w not in self._stopwords and len(w) > 1]

    def extract_key_sentences(
        self,
        text: str,
        top_n: int = 5,
        ratio: float | None = None,
    ) -> list[ExtractiveSentence]:
        """Perform TF-IDF sentence extraction on text.

        Args:
            text: Input document text.
            top_n: Maximum number of sentences to extract.
            ratio: Optional target ratio of sentences to select (e.g. 0.3 for 30%).

        Returns:
            List of ExtractiveSentence instances ordered chronologically.
        """
        sentences = self._tokenize_sentences(text)
        num_sentences = len(sentences)

        if num_sentences == 0:
            return []

        if ratio is not None:
            target_count = max(1, math.ceil(num_sentences * ratio))
            limit = min(top_n, target_count)
        else:
            limit = min(top_n, num_sentences)

        # Step 1: Calculate Word Frequencies across all sentences
        tokenized_sentences = [self._tokenize_words(s) for s in sentences]
        doc_count_per_word: dict[str, int] = {}
        for words in tokenized_sentences:
            unique_words = set(words)
            for word in unique_words:
                doc_count_per_word[word] = doc_count_per_word.get(word, 0) + 1

        # Step 2: Compute IDF for each word
        num_docs = float(num_sentences)
        word_idf: dict[str, float] = {
            word: math.log((1.0 + num_docs) / (1.0 + float(count))) + 1.0
            for word, count in doc_count_per_word.items()
        }

        # Step 3: Compute Sentence TF-IDF Scores
        scored_sentences: list[ExtractiveSentence] = []
        for idx, (sentence, words) in enumerate(zip(sentences, tokenized_sentences, strict=False)):
            if not words:
                continue

            word_counts: dict[str, int] = {}
            for w in words:
                word_counts[w] = word_counts.get(w, 0) + 1

            total_words = float(len(words))
            score = 0.0
            for w, count in word_counts.items():
                tf = float(count) / total_words
                idf = word_idf.get(w, 1.0)
                score += tf * idf

            # Normalize by length to prevent bias towards long sentences
            normalized_score = score / math.sqrt(float(len(words)))
            scored_sentences.append(
                ExtractiveSentence(
                    sentence=sentence,
                    score=round(normalized_score, 4),
                    original_index=idx,
                )
            )

        if not scored_sentences:
            return [
                ExtractiveSentence(
                    sentence=s,
                    score=1.0,
                    original_index=i,
                )
                for i, s in enumerate(sentences[:limit])
            ]

        # Rank by score descending, pick top_n, then re-sort by original_index
        top_ranked = sorted(scored_sentences, key=lambda x: x.score, reverse=True)[:limit]
        top_ranked.sort(key=lambda x: x.original_index)
        return top_ranked

    def summarize_hybrid(
        self,
        text: str,
        max_extractive_sentences: int = 7,
    ) -> HybridSummaryResult:
        """Run hybrid NLP summarization (TF-IDF extraction -> LLM abstraction).

        Args:
            text: Raw input legal document text.
            max_extractive_sentences: Max sentences to extract via TF-IDF before LLM.

        Returns:
            HybridSummaryResult instance containing extractive excerpts and LLM summary.
        """
        original_char_count = len(text)
        if not text.strip():
            return HybridSummaryResult(
                extractive_sentences=[],
                abstractive_summary="No document text available to summarize.",
                original_char_count=0,
                condensed_char_count=0,
                compression_ratio=0.0,
            )

        # Extract top TF-IDF sentences
        extractive = self.extract_key_sentences(
            text=text,
            top_n=max_extractive_sentences,
            ratio=0.35,
        )

        condensed_payload = "\n".join(item.sentence for item in extractive)
        condensed_char_count = len(condensed_payload)

        # Pass condensed payload to LLM abstractive summarizer
        try:
            abstractive = openai_service.summarize(condensed_payload)
        except Exception:  # noqa: BLE001
            abstractive = f"Extractive Summary Highlights:\n\n{condensed_payload}"

        ratio = (
            round(float(condensed_char_count) / float(original_char_count), 4)
            if original_char_count > 0
            else 1.0
        )

        return HybridSummaryResult(
            extractive_sentences=extractive,
            abstractive_summary=abstractive,
            original_char_count=original_char_count,
            condensed_char_count=condensed_char_count,
            compression_ratio=min(ratio, 1.0),
        )


hybrid_nlp_service = HybridNLPService()
