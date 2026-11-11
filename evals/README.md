# RAG Golden Dataset

`golden_dataset.jsonl` is a small benchmark containing project-README checks and retrieval cases based on the user-provided excerpt from the uploaded *Rich Dad Poor Dad* document. It is intended to smoke-test retrieval and answer generation; it is not a substitute for a broader evaluation set based on representative documents and queries.

For separate stage-wise evaluation, use `retrieval_dataset.jsonl` for retriever quality and `generation_dataset.jsonl` for the LLM answer-generation stage. The combined `golden_dataset.jsonl` is retained as a convenient mixed benchmark.

## Record format

Each JSONL record contains:

- `id`: stable example identifier.
- `question`: query to send to the RAG application.
- `reference_answer`: expected answer or expected abstention.
- `reference_contexts`: supporting passages or, for the book cases, concise paraphrases of the evidence to retrieve. Empty for unanswerable questions.
- `source_file`: repository source used to create the example.
- `category`: behavior being tested.
- `answerable`: whether the source contains an answer.

The records are designed to be easy to adapt to common RAG evaluation libraries: `question`, `reference_answer`, and `reference_contexts` correspond to query, ground truth, and ground-truth contexts/evidence. Model outputs and retrieved contexts should be added at evaluation time, not baked into this golden set. Book evidence is paraphrased rather than quoted; use human or semantic relevance judgments rather than exact string matching for those records.

## Running against this application

1. Upload the source document for the records you want to test (README or the book) and keep its document ID.
2. Send each `question` as `message` and that document ID in `documentId` to the `/chatbot/evaluation` endpoint, using the session and user headers required by the API.
3. Judge whether returned `semantic_search` passages contain the evidence described by `reference_contexts`, and compare the answer with `reference_answer`. For `answerable: false`, verify that the answer abstains rather than inventing details.

The current endpoint only searches document chunks when `documentId` is supplied. The book cases are grounded only in the excerpt provided for dataset creation, and their evidence descriptions are not verbatim chunk text. For strict Recall@k or MRR, annotate the actual retrieved chunk IDs/text from your uploaded copy; this endpoint currently returns passages but not chunk IDs. This dataset does not validate multi-document isolation, conversational memory, or production performance.

## Stage-wise retrieval and LLM evaluation

### Retrieval: `retrieval_dataset.jsonl`

Each row contains a query and a paraphrased description of the evidence that should be found. Send `query` to the retriever with the uploaded book's document ID, then judge whether the returned top-k chunks support every item in `relevant_evidence`. These labels support semantic/manual relevance checks; because chunk IDs depend on your upload and `relevant_chunk_ids` are initially empty, annotate the actual relevant chunk IDs before calculating strict Recall@k or MRR.

### LLM generation: `generation_dataset.jsonl`

Each row contains `question`, `contexts`, and `reference_answer`. The model receives the question plus `contexts`; compare its response with the reference for correctness, relevance, completeness, and faithfulness (no claims beyond the supplied context). The contexts here are short, human-written paraphrases of the provided excerpt so this set can test generation independently of retrieval.

To measure the LLM after your real retriever, replace the fixture `contexts` with the exact passages returned by `semantic_search` for the matching question, while keeping the reference answer fixed. That measures generation conditioned on actual retrieval output. The `/chatbot/evaluation` endpoint already returns both `semantic_search` and `answer`, so capture them together for an end-to-end run; stage-wise LLM testing should pass the captured contexts to the model without allowing unrelated chat history to influence the result.