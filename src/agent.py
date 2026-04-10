from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        # TODO: store references to store and llm_fn
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        # TODO: retrieve chunks, build prompt, call llm_fn
        # raise NotImplementedError("Implement KnowledgeBaseAgent.answer")
        # 1. Truy xuất các đoạn văn bản liên quan từ vector store
        results = self.store.search(question, top_k=top_k)

        # 2. Xử lý trường hợp không tìm thấy context (store trống hoặc không có kết quả phù hợp)
        if not results:
            context_text = "No relevant information found in the knowledge base."
        else:
            # Gộp nội dung các chunk tìm được thành một khối context
            context_parts = [res["content"] for res in results]
            context_text = "\n\n".join(context_parts)

        # 3. Xây dựng Prompt với kỹ thuật grounding
        # Chúng ta chỉ dẫn LLM chỉ trả lời dựa trên context được cung cấp
        prompt = (
            "You are a helpful assistant. Use the following pieces of retrieved context "
            "to answer the question. If the context does not contain the answer, "
            "honestly state that you don't know based on the provided data.\n\n"
            f"Context:\n{context_text}\n\n"
            f"Question: {question}\n\n"
            "Answer:"
        )

        # 4. Gọi LLM và trả về kết quả
        return self.llm_fn(prompt)
