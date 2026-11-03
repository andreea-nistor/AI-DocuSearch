# Step 3: Embedding & Indexing

This step turns the text chunks produced by [Step 2](STEP_2_PREPROCESS.md) into vectors and makes them searchable by meaning. The implementation lives in [src/embed_index.py](../src/embed_index.py) and is called from [src/pipeline.py](../src/pipeline.py). When embeddings cannot be produced, the step degrades to keyword-style scoring instead of failing the request.

## Goal

For a document that has been split into chunks, answer the question "which chunks are most relevant to this question?" quickly and without an external API. The step:

- Encodes each chunk with a pre-trained sentence-embedding model.
- Stores the vectors in a nearest-neighbour index (FAISS when available, NumPy otherwise).
- Returns the top-k chunk indices and scores for a query.

## Design Decisions

- **Local embedding model.** The default model is `all-MiniLM-L6-v2` from sentence-transformers. It is small enough for a low-memory Streamlit Cloud container and produces 384-dimensional vectors (a property of the model, not enforced in code).
- **Lazy model loading.** `EmbedIndex()` does not load the model. The model is loaded on the first `build_index()` or `search()` call, so constructing the object is cheap and tests can inspect state before any download.
- **Cosine similarity via inner product.** Vectors are L2-normalized, so an inner-product index (`IndexFlatIP`) returns cosine similarity.
- **Two search backends.** FAISS is preferred. If FAISS is missing or fails, a NumPy matrix product gives the same ranking.
- **Graceful degradation.** Memory errors, a missing `sentence-transformers` package, or a model that cannot be loaded never crash the pipeline. The caller falls back to lite mode (see [Error Handling and Fallbacks](#error-handling-and-fallbacks)).
- **Chunks are always kept.** Even when no vectors are built, the chunk list is stored so keyword retrieval still works.

## How the Flow Works

1. **Construction.** `EmbedIndex(model_name="all-MiniLM-L6-v2")` stores the model name and sets `model`, `embeddings`, `index`, and `chunks` to empty values. `disabled` starts as `False`.
2. **Model loading (`_ensure_model`).** On first need, the model is loaded with `SentenceTransformer(model_name)`. If the model is already loaded or `disabled` is set, nothing happens. A `MemoryError` during loading sets `disabled` to `True`. Any other failure, including a missing package or a failed download, is raised as a `RuntimeError`.
3. **Build (`build_index`).** The chunks are stored first. The model is then loaded. If loading fails or leaves the model unset, the embeddings and index are cleared and the method returns. Otherwise all chunks are encoded in one call with `convert_to_numpy=True` and without a progress bar. A `MemoryError` during encoding clears the state and sets `disabled`.
4. **FAISS index.** The embeddings are L2-normalized in place and added to an `IndexFlatIP` sized to the vector dimension. If FAISS cannot be imported or fails, `index` is set to `None` and the NumPy path is used later. The embeddings are kept in both cases.
5. **Query (`search`).** The model is loaded if needed. If the index is disabled, the model is missing, or no embeddings exist, the query is scored by token overlap instead. Otherwise the query is encoded, normalized, and searched in FAISS for the top-k results.
6. **NumPy fallback.** If FAISS is unavailable or raises, the query and the stored embeddings are normalized again and scored with a matrix product. The results are sorted and the top k are returned.
7. **Result.** `search()` always returns a dictionary with `indices` (chunk positions) and `scores`. The scores come from the active backend, so their scale depends on it: cosine values for FAISS and NumPy, and raw token-overlap counts for the text fallback.

### Pipeline Integration

[src/pipeline.py](../src/pipeline.py) decides whether to build an index at all. The `build_pipeline_from_text()` function:

- Returns lite mode immediately when embeddings are disabled by configuration or by the caller.
- Checks available system memory and returns lite mode when it is below the threshold.
- Creates `EmbedIndex()`, calls `build_index()`, and returns lite mode if the object is `disabled` or has no embeddings.
- Otherwise returns the index together with the chunks.

`answer_question()` then uses `index.search(question, k=top_k)` with the default `top_k` of 3, or the token-overlap helper in the pipeline when no index exists.

## Configuration

| Variable | Default | Effect in this step |
|----------|---------|---------------------|
| `DOCUSEARCH_LITE_MODE` | `true` | Read only when the caller does not pass `use_embeddings`, such as the CLI. `true` means no embeddings are built. |
| `MIN_AVAILABLE_MEMORY_GB` | `2.0` | If detected free memory is below this value, the pipeline skips `EmbedIndex` and uses lite mode. Unknown memory does not trigger the fallback. |

The model name is a constructor argument of `EmbedIndex` and is not read from an environment variable. The Streamlit app always passes `use_embeddings=True`, so `DOCUSEARCH_LITE_MODE` does not affect it. See [README.md](../README.md) for the full list of settings.

## Error Handling and Fallbacks

| Situation | Behaviour |
|-----------|-----------|
| `sentence-transformers` not installed, or model download fails | `_ensure_model()` raises `RuntimeError`. `build_index()` and `search()` catch it and set `disabled`, so the pipeline returns lite mode. The error message names the package, but a download failure is reported the same way. |
| `MemoryError` while loading the model | Logged to stderr, `disabled` is set, and lite mode is used. |
| `MemoryError` while encoding chunks or the query | Logged to stderr. Chunk encoding clears the index and disables the object. Query encoding returns empty results. |
| FAISS missing or failing during build | `index` is `None` and search uses NumPy. |
| FAISS failing during search | The exception is swallowed and search uses NumPy. |
| Model unavailable at query time | Token-overlap search over the stored chunks. |
| Low available memory before building | Pipeline returns lite mode without creating the model. |

The lite-mode path is handled in [STEP_5_PIPELINE.md](STEP_5_PIPELINE.md).

## Tests

There is no dedicated test module for `src/embed_index.py`, and no test in `test_src/` imports `EmbedIndex` directly. Embedding code is exercised indirectly:

- `python -m test_src.test_ingest` runs pipeline cases, including one that calls `build_pipeline_from_text(..., use_embeddings=True)`. That path builds an index when the model is available and otherwise exercises the fallback.
- Most other tests use `use_embeddings=False`, so they cover lite mode only.

The module can also be smoke-tested directly with `python -m src.embed_index`, which builds a three-chunk index and runs one search.

## Limitations

- **Model download on first use.** The first build downloads the model, which can take a long time and requires network access. The model is not bundled with the repository.
- **Full in-memory encoding.** All chunks are encoded in a single `encode()` call and held in memory. Very large documents rely on the size guard in Step 5 and on the memory check.
- **No model configuration from the environment.** Changing the model requires code changes.
- **Flat index.** `IndexFlatIP` is an exact search. It is simple and accurate for typical document sizes, but it does not scale to very large collections, and no quantization or GPU path is implemented.
- **FAISS padding is filtered in the pipeline.** When `k` is larger than the number of chunks, FAISS returns `-1` for the missing slots. `answer_question()` drops any index outside the chunk range before selecting chunks, so the padding is ignored instead of selecting the last chunk.
- **Scores are not comparable across backends.** Cosine values from the vector backends and token-overlap counts from the fallback use different scales.
- **Keyword fallback is crude.** Token overlap compares whole lowercase words, so it ignores punctuation, stemming, and synonyms.
- **No persistence.** Embeddings and indexes are rebuilt for each uploaded document and are not cached on disk.

## Related

- [STEP_1_INGEST.md](STEP_1_INGEST.md): extracts the raw text.
- [STEP_2_PREPROCESS.md](STEP_2_PREPROCESS.md): cleans and chunks the text that this step embeds.
- [STEP_4_AI_QUERY.md](STEP_4_AI_QUERY.md): sends the retrieved chunks to the language model.
- [STEP_5_PIPELINE.md](STEP_5_PIPELINE.md): decides between embedding and lite mode and applies the size and memory guards.
