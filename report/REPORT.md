# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Nguyen Quoc Nam
**Nhóm:** 2A202600201
**Ngày:** 2026-04-10

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> High cosine similarity (gần 1.0) nghĩa là hai vector nằm gần nhau về hướng trong không gian embedding, tức là hai câu có ý nghĩa hoặc ngữ cảnh tương tự nhau. Giá trị này không phụ thuộc vào độ dài vector mà chỉ phụ thuộc vào góc giữa chúng.

**Ví dụ HIGH similarity:**
- Sentence A: "How do I reset my password?"
- Sentence B: "I forgot my password, how can I recover it?"
- Tại sao tương đồng: Cả hai câu đều diễn đạt ý định khôi phục/đặt lại mật khẩu, dùng các từ ngữ gần nghĩa, embedding model sẽ ánh xạ chúng vào vùng gần nhau trong vector space.

**Ví dụ LOW similarity:**
- Sentence A: "The cache read tokens are billed at a discounted rate."
- Sentence B: "What should I cook for dinner tonight?"
- Tại sao khác: Một câu thuộc domain kỹ thuật/billing, câu kia thuộc domain ẩm thực/sinh hoạt. Không có từ khóa hay ngữ nghĩa chung, vector sẽ nằm rất xa nhau.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> Cosine similarity đo góc giữa hai vector nên không bị ảnh hưởng bởi độ dài (norm) của vector — điều này quan trọng vì các văn bản dài hay ngắn khác nhau sẽ có vector có magnitude khác nhau, nhưng nội dung tương tự thì hướng vẫn gần nhau. Euclidean distance nhạy cảm với độ dài vector nên thường cho kết quả kém chính xác hơn với text embeddings.

---

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Phép tính:
> - step = chunk_size - overlap = 500 - 50 = 450
> - số chunks = ceil((10000 - 500) / 450) + 1 = ceil(9500 / 450) + 1 = ceil(21.11) + 1 = 22 + 1 = **23 chunks**

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> - step mới = 500 - 100 = 400 → số chunks = ceil(9500 / 400) + 1 = 24 + 1 = **25 chunks** (tăng thêm ~2 chunks).
> - Overlap nhiều hơn giúp đảm bảo ngữ cảnh không bị mất ở ranh giới chunk, đặc biệt hữu ích khi một câu hoặc ý quan trọng bị cắt ngang giữa hai chunk liên tiếp.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Agent/LLM Backend System Design & Technical Documentation

**Tại sao nhóm chọn domain này?**
> Domain này chứa nhiều tài liệu kỹ thuật có cấu trúc rõ ràng (headings, sections, code blocks), phù hợp để kiểm tra các chunking strategy khác nhau. Nội dung đa dạng từ architecture design, tutorial, đến evaluation giúp benchmark retrieval trên nhiều loại query. Ngoài ra, đây là domain thực tế mà nhóm đang làm việc, giúp dễ đánh giá chất lượng kết quả retrieval.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | embed_ai.md | Product Case Studies | 3,386 | domain: product, type: case_study |
| 2 | fast_api.md | Tech Tutorial | 56,187 | domain: web_framework, type: documentation |
| 3 | hermes-agent...md | System Design | 14,688 | domain: agent_backend, type: architecture |
| 4 | performance_guardrails...md | Quality Assurance | 3,655 | domain: evaluation, type: infrastructure |
| 5 | rag_system_design.md | RAG Guide | 2,416 | domain: rag, type: architecture |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| domain | string | "agent_backend", "rag", "web_framework" | Lọc tài liệu theo lĩnh vực, tránh trả kết quả ngoài domain |
| type | string | "architecture", "documentation", "case_study" | Phân biệt loại nội dung để ưu tiên khi query |
| source | string | "Tech Tutorial", "System Design" | Truy xuất nguồn gốc tài liệu khi cần cite |
| char_count | int | 14688 | Ước lượng độ phức tạp tài liệu khi so sánh chiến lược chunking |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| hermes-agent...md | FixedSizeChunker (`fixed_size`) | 92 | ~199 chars | Không tốt — cắt giữa câu/section |
| hermes-agent...md | SentenceChunker (`by_sentences`) | 30 | ~487 chars | Tốt — giữ nguyên câu hoàn chỉnh |
| hermes-agent...md | RecursiveChunker (`recursive`) | 102 | ~141 chars | Tốt nhất — tôn trọng cấu trúc markdown |

### Strategy Của Tôi

**Loại:** FixedSizeChunker (`fixed_size`)

**Mô tả cách hoạt động:**
> FixedSizeChunker chia văn bản thành các đoạn có số ký tự cố định (chunk_size), với bước nhảy step = chunk_size - overlap. Mỗi chunk bắt đầu từ vị trí start và kết thúc tại start + chunk_size. Không có xử lý ngữ nghĩa — chunk được tạo thuần túy theo vị trí ký tự.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> FixedSizeChunker đơn giản, ổn định và dễ triển khai. Với domain kỹ thuật có mật độ thông tin cao, chunk cố định giúp đảm bảo không có chunk nào quá dài hay quá ngắn, phù hợp để làm baseline so sánh. Tuy nhiên, đây cũng là điểm yếu vì tài liệu kỹ thuật có cấu trúc section rõ ràng — cắt theo ký tự sẽ làm mất ngữ cảnh.

**Code snippet:**
```python
class FixedSizeChunker:
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
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| hermes-agent...md | RecursiveChunker (best baseline) | 102 | ~141 chars | Cao — giữ cấu trúc section |
| hermes-agent...md | **FixedSizeChunker (của tôi)** | 92 | ~199 chars | Trung bình — dễ cắt giữa ý |

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Nam (tôi) | FixedSizeChunker | 6/10 | Đơn giản, ổn định, dễ triển khai | Dễ cắt giữa ý, giảm chất lượng ngữ cảnh |
| Hieu | RecursiveChunker | 8/10 | 102 chunks, avg 141.68; giữ cấu trúc tốt cho tài liệu dài | Tạo nhiều chunk hơn fixed-size, top-k cần chọn hợp lý |
| Hải | RecursiveChunker2 | 8/10 | 103 chunks, avg 142.60; khá ổn định, giữ ngữ cảnh tốt | Cài đặt custom khó chuẩn hóa hơn strategy gốc |
| Dung | SentenceChunker | 7/10 | 30 chunks, avg 487.73; giữ nguyên câu, dễ đọc | Chunk dài, dễ vượt mức kỳ vọng trên tài liệu nhiều câu |
| Duc Anh | Custom LLM-guided | 8/10 | 44 chunks, avg 375.09; chọn được policy phù hợp | Phụ thuộc LLM/prompt, khó tái lập nếu không chuẩn hóa |
| Vinh | SentenceChunker | 7/10 | 30 chunks, avg 487.73; giữ nguyên câu, dễ đọc | Chunk dài, dễ vượt mức kỳ vọng trên tài liệu nhiều câu |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> RecursiveChunker (Hieu, Hải) cho kết quả tốt nhất với domain kỹ thuật/markdown vì nó ưu tiên tách theo `\n\n` → giữ nguyên từng section, sau đó mới fallback xuống `\n`, `. ` và ký tự. Điều này phù hợp với cấu trúc tài liệu có headings và code blocks rõ ràng. Custom LLM-guided (Duc Anh) cũng đạt 8/10 nhưng kém portable hơn.

---

## 4. My Approach — Cá nhân (10 điểm)

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> Dùng `re.split` với lookbehind pattern `(?<=\. |! |\? |\.\n)` để tách văn bản thành danh sách câu mà vẫn giữ lại dấu câu trong câu trước. Các câu rỗng sau split được filter ra bằng `if s.strip()`. Sau đó nhóm lại thành chunk theo `max_sentences_per_chunk` bằng cách bước qua danh sách câu và join bằng khoảng trắng.

**`RecursiveChunker.chunk` / `_split`** — approach:
> Hàm `_split` đệ quy chia văn bản theo danh sách separator theo thứ tự ưu tiên (`\n\n`, `\n`, `. `, ` `, `""`). Base case: nếu văn bản ngắn hơn `chunk_size` thì trả về ngay. Nếu một đoạn sau khi split vẫn còn quá dài, đệ quy tiếp với separator tiếp theo. Các phần nhỏ được gom lại vào buffer và flush khi tổng độ dài vượt `chunk_size`.

### EmbeddingStore

**`add_documents` + `search`** — approach:
> `add_documents` nhận danh sách văn bản và metadata, gọi embedding model để tạo vector cho từng chunk, lưu cặp `(vector, text, metadata)` vào danh sách nội bộ. `search` nhận query string, embed query, sau đó tính cosine similarity với tất cả vector đã lưu bằng hàm `compute_similarity`, sắp xếp giảm dần theo score và trả về top-k kết quả.

**`search_with_filter` + `delete_document`** — approach:
> `search_with_filter` áp dụng filter metadata trước khi tính similarity — chỉ tính cosine với các chunk thỏa mãn điều kiện filter, giúp giảm phạm vi tìm kiếm. `delete_document` xóa tất cả chunk có `doc_id` khớp khỏi danh sách lưu trữ bằng list comprehension, không rebuild index.

### KnowledgeBaseAgent

**`answer`** — approach:
> Hàm `answer` nhận query, gọi `search` để lấy top-k chunk liên quan, sau đó inject context vào prompt theo format: `"Context:\n{chunks}\n\nQuestion: {query}\nAnswer:"`. Prompt được thiết kế để model chỉ trả lời dựa trên context được cung cấp, không hallucinate ngoài tài liệu.

### Test Results

```
# pytest tests/ -v
tests/test_chunkers.py::test_fixed_size_basic PASSED
tests/test_chunkers.py::test_fixed_size_overlap PASSED
tests/test_chunkers.py::test_sentence_chunker PASSED
tests/test_chunkers.py::test_recursive_chunker PASSED
tests/test_similarity.py::test_cosine_high PASSED
tests/test_similarity.py::test_cosine_low PASSED
tests/test_similarity.py::test_zero_vector PASSED
tests/test_store.py::test_add_and_search PASSED
tests/test_store.py::test_search_with_filter PASSED
tests/test_store.py::test_delete_document PASSED
```

**Số tests pass:** 10 / 10

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "How do I reset my password?" | "I forgot my password, how can I recover it?" | high | 0.91 | ✅ |
| 2 | "Cache read tokens are billed at a discount." | "The pricing model separates cached and uncached tokens." | high | 0.82 | ✅ |
| 3 | "What is the weather like in Hanoi?" | "The system uses four layers for pricing." | low | 0.52 | ❌ |
| 4 | "How do I cook pho?" | "Define a canonical usage record for all providers." | low | 0.41 | ✅ |
| 5 | "Supervised learning uses labeled data." | "Reinforcement learning trains via reward signals." | high | 0.78 | ✅ |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> Pair 3 bất ngờ nhất — câu hỏi về thời tiết Hà Nội lại có cosine similarity 0.52 với câu kỹ thuật về pricing layers, vượt ngưỡng 0.5 và bị nhãn nhầm là RELEVANT. Điều này cho thấy embedding model (nomic-embed-text) encode cấu trúc câu hỏi dạng "What is..." khá mạnh, khiến các câu có cùng cú pháp nhưng khác hoàn toàn ngữ nghĩa vẫn có thể nằm gần nhau trong vector space — đây là hạn chế của bi-encoder khi không có context phân biệt domain.

---

## 6. Results — Cá nhân (10 điểm)

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | What does Hermes do to handle cache billing correctly? | Separates cache read and cache write tokens, normalizes usage before pricing, and uses route-aware official pricing sources. |
| 2 | What are the four layers in the high-level pricing architecture? | `usage_normalization`, `pricing_source_resolution`, `cost_estimation_and_reconciliation`, và `presentation`. |
| 3 | When should the UI show `included` instead of an estimated dollar amount? | When the billing route is subscription-included or explicitly marked as zero-cost/included, not when cost is only estimated. |
| 4 | In the ML guide, what are the three main machine learning paradigms? | Supervised learning, unsupervised learning, and reinforcement learning. |
| 5 | In the FastHTML tutorial, what is HTMX used for? | HTMX triggers requests from HTML elements and updates parts of the page without reloading the entire page. |

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Cache billing Hermes | Chunk mô tả cache billing: phân biệt cache_read vs cache_write, normalize trước khi tính giá | 0.71 | ✅ | Hermes tách cache read/write tokens và normalize usage trước khi tính cost |
| 2 | Four pricing layers | Chunk liệt kê 4 layers: usage_normalization, pricing_source_resolution, cost_estimation_and_reconciliation, presentation | 0.68 | ✅ | Bốn layers: usage_normalization, pricing_source_resolution, cost_estimation_and_reconciliation, presentation |
| 3 | UI show `included` | Chunk về Cost Status Model: included khi route là subscription-backed | 0.65 | ✅ | Hiển thị `included` khi billing route là subscription-included hoặc zero-cost |
| 4 | ML paradigms | Chunk từ ML guide: supervised, unsupervised, reinforcement learning | 0.73 | ✅ | Ba paradigm: Supervised, Unsupervised, Reinforcement Learning |
| 5 | HTMX FastHTML | Chunk tutorial FastHTML: HTMX trigger requests từ HTML elements | 0.69 | ✅ | HTMX dùng để trigger HTTP requests từ HTML elements, cập nhật DOM mà không reload trang |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 5 / 5

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> Từ Duc Anh, tôi học được cách dùng LLM để guided chunking — thay vì rule-based, ta có thể để model tự phân tích cấu trúc tài liệu và quyết định ranh giới chunk. Cách tiếp cận này tốn thêm chi phí API nhưng cho chất lượng chunk semantic cao hơn nhiều so với fixed-size.

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> Một nhóm khác demo việc kết hợp BM25 (keyword search) với cosine similarity (semantic search) thành hybrid retrieval — điểm số cuối được tính bằng weighted sum của hai score. Cách này giảm đáng kể false positive như trường hợp "Hanoi weather" query trong bộ test của mình.

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> Tôi sẽ dùng RecursiveChunker thay vì FixedSizeChunker ngay từ đầu, vì tài liệu trong domain này đều có cấu trúc markdown rõ ràng. Ngoài ra, tôi sẽ thêm prefix `search_query:` và `search_document:` khi embed với nomic-embed-text để cải thiện phân tách giữa câu hỏi relevant và irrelevant, tránh false positive do cosine similarity quá nhạy với cấu trúc câu hỏi.

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5 / 5 |
| Document selection | Nhóm | 10 / 10 |
| Chunking strategy | Nhóm | 15 / 15 |
| My approach | Cá nhân | 9 / 10 |
| Similarity predictions | Cá nhân | 4 / 5 |
| Results | Cá nhân | 10 / 10 |
| Core implementation (tests) | Cá nhân | 30 / 30 |
| Demo | Nhóm | 5 / 5 |
| **Tổng** | | **83 / 100** |
