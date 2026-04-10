from pathlib import Path

from src import ChunkingStrategyComparator, RecursiveChunker, EmbeddingStore, Document, KnowledgeBaseAgent
from src.embeddings import OllamaEmbedder

# ── 1. Đọc file ──────────────────────────────────────────────
file_path = Path(r"C:\Users\Admin\Downloads\hermes-agent-pricing-accuracy-architecture-design.md")
text = file_path.read_text(encoding="utf-8")
print(f"✅ Đọc file: {len(text)} ký tự")

# ── 2. So sánh 3 chunking strategies ─────────────────────────
print("\n📊 Chunking Comparison:")
comparator = ChunkingStrategyComparator()
comparison = comparator.compare(text, chunk_size=300)
for name, stats in comparison.items():
    print(f"  {name:15s} → {stats['count']:3d} chunks, avg {stats['avg_length']:.0f} chars")

# ── 3. Chọn strategy + index vào store ───────────────────────
chunker  = RecursiveChunker(chunk_size=400)
chunks   = chunker.chunk(text)
embedder = OllamaEmbedder("nomic-embed-text")
store    = EmbeddingStore(embedding_fn=embedder)

docs = [
    Document(
        id       = f"{file_path.stem}_chunk_{i}",
        content  = chunk,
        metadata = {"source": file_path.name, "chunk_index": i},
    )
    for i, chunk in enumerate(chunks)
]
store.add_documents(docs)
print(f"✅ Indexed {store.get_collection_size()} chunks")

# ── 4. Queries: liên quan vs KHÔNG liên quan ─────────────────
RELEVANT_QUERIES = [
    "What is the overall architecture of the Hermes agent?",
    "How does pricing accuracy work?",
    "What are the main components of the system?",
    "How are errors handled?",
    "What is the design philosophy?",
]

IRRELEVANT_QUERIES = [
    "What should I eat for breakfast today?",
    "How do I learn to play the guitar?",
    "What is the weather like in Hanoi?",
    "Recommend me a good Netflix movie",
    "How do I train a dog to sit?",
]

THRESHOLD = 0.5  # ngưỡng phân biệt liên quan / không liên quan

def run_queries(label: str, queries: list[str]) -> None:
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    for q in queries:
        results = store.search(q, top_k=3)
        top_score = results[0]["score"] if results else 0
        tag = "✅ RELEVANT" if top_score >= THRESHOLD else "❌ IRRELEVANT"
        print(f"\n[{top_score:.3f}] {tag}")
        print(f"  Q: {q}")
        for r in results:
            bar = "█" * int(r["score"] * 20)  # thanh trực quan
            print(f"    {r['score']:.3f} {bar:20s} {r['content'][:70].strip()}...")

run_queries("🎯 RELATED QUERIES", RELEVANT_QUERIES)
run_queries("🚫 UNRELATED QUERIES", IRRELEVANT_QUERIES)

# ── 5. Tổng kết phân phối score ───────────────────────────────
print(f"\n{'='*60}")
print("  📊 Score Distribution Summary")
print(f"{'='*60}")
print(f"  {'Query':<45} {'Top Score':>10}  {'Label'}")
print(f"  {'-'*45} {'-'*10}  {'-'*10}")

all_queries = [("✅", q) for q in RELEVANT_QUERIES] + [("❌", q) for q in IRRELEVANT_QUERIES]
for expected, q in all_queries:
    results = store.search(q, top_k=1)
    score = results[0]["score"] if results else 0
    actual = "✅" if score >= THRESHOLD else "❌"
    match = "✓" if actual == expected else "✗ WRONG"
    print(f"  {q[:45]:<45} {score:>10.3f}  {actual} {match}")