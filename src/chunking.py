from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start: start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        # TODO: split into sentences, group into chunks
        # raise NotImplementedError("Implement SentenceChunker.chunk")
        if not text:
            return []

        # Sử dụng lookbehind để giữ lại dấu câu tại ranh giới câu (fixed-width: 2 chars)
        # Các ranh giới: ". ", "! ", "? ", ".\n"
        sentence_boundaries = r'(?<=\. |! |\? |\.\n)'
        sentences = [s.strip() for s in re.split(sentence_boundaries, text) if s.strip()]

        chunks: list[str] = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            chunk_sentences = sentences[i: i + self.max_sentences_per_chunk]
            chunks.append(" ".join(chunk_sentences))
        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        # TODO: implement recursive splitting strategy
        # raise NotImplementedError("Implement RecursiveChunker.chunk")
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        # TODO: recursive helper used by RecursiveChunker.chunk
        # raise NotImplementedError("Implement RecursiveChunker._split")
        if len(current_text) <= self.chunk_size:
            return [current_text]

        if not remaining_separators:
            # Base case: không còn separator nào, chia nhỏ theo độ dài chunk_size
            return [current_text[i: i + self.chunk_size] for i in range(0, len(current_text), self.chunk_size)]

        separator = remaining_separators[0]
        next_separators = remaining_separators[1:]

        # Thực hiện chia nhỏ dựa trên separator hiện tại
        if separator == "":
            splits = list(current_text)
        else:
            splits = current_text.split(separator)

        final_chunks = []
        current_buffer = []
        current_len = 0

        for part in splits:
            if len(part) > self.chunk_size:
                # Nếu một phần con vẫn quá lớn, xả buffer và đệ quy với các separator tiếp theo
                if current_buffer:
                    final_chunks.append(separator.join(current_buffer))
                    current_buffer, current_len = [], 0
                final_chunks.extend(self._split(part, next_separators))
            else:
                # Kiểm tra xem có thể gộp phần này vào chunk hiện tại không
                added_len = len(part)
                if current_buffer:
                    added_len += len(separator)

                if current_len + added_len > self.chunk_size:
                    final_chunks.append(separator.join(current_buffer))
                    current_buffer, current_len = [], 0

                if current_buffer: current_len += len(separator)
                current_buffer.append(part)
                current_len += len(part)

        if current_buffer:
            final_chunks.append(separator.join(current_buffer))
        return final_chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    # TODO: implement cosine similarity formula
    # raise NotImplementedError("Implement compute_similarity")
    dot_product = _dot(vec_a, vec_b)
    norm_a = math.sqrt(_dot(vec_a, vec_a))
    norm_b = math.sqrt(_dot(vec_b, vec_b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        # TODO: call each chunker, compute stats, return comparison dict
        # raise NotImplementedError("Implement ChunkingStrategyComparator.compare")
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=0),
            #"by_sentences": SentenceChunker(max_sentences_per_chunk=3),
            #"recursive": RecursiveChunker(chunk_size=chunk_size)
        }

        comparison = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            count = len(chunks)
            avg_len = sum(len(c) for c in chunks) / count if count > 0 else 0
            comparison[name] = {
                "count": count,
                "avg_length": avg_len,
                "chunks": chunks
            }
        return comparison
