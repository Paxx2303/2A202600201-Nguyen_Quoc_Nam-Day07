from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot, compute_similarity
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
            self,
            collection_name: str = "documents",
            embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb  # noqa: F401

            # Sử dụng EphemeralClient để lưu trữ tạm thời trong bộ nhớ (phù hợp cho Lab/Testing)
            client = chromadb.EphemeralClient()
            self._collection = client.get_or_create_collection(name=collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        embedding = self._embedding_fn(doc.content)
        metadata = doc.metadata.copy()
        # Đảm bảo luôn có doc_id trong metadata để phục vụ việc xóa
        if "doc_id" not in metadata:
            metadata["doc_id"] = doc.id

        return {
            "id": doc.id,
            "content": doc.content,
            "metadata": metadata,
            "embedding": embedding,
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        if not records:
            return []

        query_vec = self._embedding_fn(query)
        scored_results = []

        for rec in records:
            # Sử dụng hàm compute_similarity đã triển khai ở src/chunking.py
            score = compute_similarity(query_vec, rec["embedding"])
            scored_results.append({
                "content": rec["content"],
                "metadata": rec["metadata"],
                "score": score
            })

        # Sắp xếp theo score giảm dần
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        for doc in docs:
            record = self._make_record(doc)
            self._store.append(record)

            if self._use_chroma and self._collection:
                self._collection.add(
                    ids=[f"{doc.id}_{self._next_index}"],
                    documents=[doc.content],
                    embeddings=[record["embedding"]],
                    metadatas=[record["metadata"]]
                )
                self._next_index += 1

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if not metadata_filter:
            return self.search(query, top_k=top_k)

        # Pre-filtering: lọc metadata trước khi tính similarity
        filtered_records = []
        for rec in self._store:
            is_match = True
            for key, value in metadata_filter.items():
                if rec["metadata"].get(key) != value:
                    is_match = False
                    break
            if is_match:
                filtered_records.append(rec)

        return self._search_records(query, filtered_records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        initial_count = len(self._store)
        self._store = [rec for rec in self._store if rec["metadata"].get("doc_id") != doc_id]

        if self._use_chroma and self._collection:
            self._collection.delete(where={"doc_id": doc_id})

        return len(self._store) < initial_count
