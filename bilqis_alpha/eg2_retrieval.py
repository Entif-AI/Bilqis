"""Bounded local embedding retrieval for decision epoch 02.

The pure functions deliberately know nothing about a model.  The CLI loads the
locally supplied MLX model only after its input and output paths are validated.
"""
import argparse
import hashlib
import importlib.metadata
import json
import math
import platform
import resource
import sys
import time
from pathlib import Path


VERSION = 'eg2-retrieval-0.1.0'
MODEL_NAME = 'mlx-community/embeddinggemma-2-bf16'
QUERY_PREFIX_DEFAULT = 'task: search result | query: '
DOCUMENT_PREFIX_DEFAULT = 'title: none | text: '


def _numbers(vector):
    if not isinstance(vector, (list, tuple)) or not vector:
        raise ValueError('VECTOR_REQUIRED')
    values = []
    for value in vector:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError('VECTOR_NONFINITE')
        values.append(float(value))
    return values


def normalize(vector):
    """Return a finite L2-normalized JSON-safe vector."""
    values = _numbers(vector)
    magnitude = math.sqrt(math.fsum(value * value for value in values))
    if not math.isfinite(magnitude) or magnitude == 0:
        raise ValueError('VECTOR_ZERO_NORM')
    return [value / magnitude for value in values]


def project(vector, dimensions=256):
    """Use the normalized leading dimensions; no learned projection is implied."""
    if isinstance(dimensions, bool) or not isinstance(dimensions, int) or dimensions < 1:
        raise ValueError('PROJECTION_DIMENSIONS')
    values = _numbers(vector)
    if len(values) < dimensions:
        raise ValueError('PROJECTION_DIMENSIONS')
    return normalize(values[:dimensions])


def rank(query_vector, documents, top_k=8):
    """Rank supplied documents only; this function never adds a gold candidate."""
    if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 0:
        raise ValueError('TOP_K')
    query = normalize(query_vector)
    rows = []
    seen = set()
    for document in documents:
        if not isinstance(document, dict) or not isinstance(document.get('candidate_id'), str):
            raise ValueError('DOCUMENT_CANDIDATE_ID')
        candidate_id = document['candidate_id']
        if candidate_id in seen:
            raise ValueError('DUPLICATE_CANDIDATE_ID')
        seen.add(candidate_id)
        vector = normalize(document.get('vector'))
        if len(vector) != len(query):
            raise ValueError('VECTOR_DIMENSION_MISMATCH')
        similarity = math.fsum(left * right for left, right in zip(query, vector))
        rows.append({'candidate_id': candidate_id, 'similarity': similarity})
    rows.sort(key=lambda row: (-row['similarity'], row['candidate_id']))
    rows = rows[:top_k]
    return [dict(row, rank=index) for index, row in enumerate(rows, 1)]


def filter_retrieval(ranked, legal_candidate_ids):
    """Separate legal retrieval results from rejected rows without changing either."""
    legal = set(legal_candidate_ids)
    accepted, rejected = [], []
    for row in ranked:
        if not isinstance(row, dict) or not isinstance(row.get('candidate_id'), str):
            raise ValueError('RANKED_CANDIDATE_ID')
        if row['candidate_id'] in legal:
            accepted.append(dict(row))
        else:
            rejected.append(dict(row, rejection='ILLEGAL_CANDIDATE_ID'))
    return {'accepted': accepted, 'rejected': rejected}


def hard_negative_separation(query_vector, documents, gold_id, hard_negative_ids):
    """Grade frozen vectors without inserting gold into any retrieval panel."""
    full = {row['candidate_id']: row for row in rank(query_vector, documents, top_k=len(documents))}
    gold = full.get(gold_id)
    identities = sorted(set(hard_negative_ids) - {gold_id})
    negatives = sorted([full[identity] for identity in identities if identity in full], key=lambda r: r['rank'])
    margin = gold['similarity'] - negatives[0]['similarity'] if gold and negatives else None
    return {'gold': gold, 'hard_negatives': negatives,
            'missing_hard_negative_ids': [identity for identity in identities if identity not in full],
            'margin': margin, 'beats_all_hard_negatives': margin > 0 if margin is not None else None}


def _sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def _model_hashes(model_path):
    return {str(path.relative_to(model_path)): _sha256(path)
            for path in sorted(model_path.rglob('*')) if path.is_file()}


def _load_input(path):
    with path.open(encoding='utf-8') as source:
        payload = json.load(source)
    if not isinstance(payload, dict):
        raise ValueError('INPUT_OBJECT_REQUIRED')
    for key in ('documents', 'queries', 'curriculum'):
        if not isinstance(payload.get(key), list):
            raise ValueError('INPUT_' + key.upper() + '_REQUIRED')
    return payload


def _require_text_rows(rows, identity):
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get(identity), str) or not isinstance(row.get('text'), str):
            raise ValueError('INPUT_' + identity.upper() + '_TEXT_REQUIRED')


def _direct_url():
    try:
        distribution = importlib.metadata.distribution('mlx-vlm')
        direct = distribution.read_text('direct_url.json')
        if direct:
            return json.loads(direct)
    except importlib.metadata.PackageNotFoundError:
        pass
    return None


def _encode(model, tokenizer, mx, texts, prefix, batch_size):
    vectors, tokens, truncated = [], 0, 0
    for offset in range(0, len(texts), batch_size):
        batch = [prefix + text for text in texts[offset:offset + batch_size]]
        before_truncation = tokenizer(batch, padding=False, truncation=False)
        truncated += sum(len(ids) > 256 for ids in before_truncation['input_ids'])
        encoded = tokenizer(batch, return_tensors='np', padding=True, truncation=True, max_length=256)
        tokens += int(encoded['attention_mask'].sum())
        result = model(mx.array(encoded['input_ids']), attention_mask=mx.array(encoded['attention_mask']))
        embeddings = result.text_embeds.astype(mx.float32)
        mx.eval(embeddings)
        vectors.extend(normalize(vector) for vector in embeddings.tolist())
    return vectors, tokens, truncated


def build_retrieval(input_payload, model_path, batch_size=8):
    """Embed a complete input payload with the explicitly local MLX runtime."""
    if isinstance(batch_size, bool) or not isinstance(batch_size, int) or batch_size not in (8, 16):
        raise ValueError('BATCH_SIZE')
    _require_text_rows(input_payload['documents'], 'candidate_id')
    _require_text_rows(input_payload['queries'], 'query_id')
    _require_text_rows(input_payload['curriculum'], 'block_id')
    if len({row['candidate_id'] for row in input_payload['documents']}) != len(input_payload['documents']):
        raise ValueError('DUPLICATE_CANDIDATE_ID')
    if any(not isinstance(row.get('relationships'), list) for row in input_payload['documents']):
        raise ValueError('INPUT_RELATIONSHIPS_REQUIRED')

    model_path = model_path.expanduser().resolve()
    import mlx.core as mx
    from mlx_vlm import embedding_loader
    from mlx_vlm.embedding_loader import load_embedding_model
    from transformers import AutoTokenizer

    config_path = model_path / 'config_sentence_transformers.json'
    config = json.loads(config_path.read_text(encoding='utf-8'))
    prompts = config.get('prompts', {})
    query_prefix = prompts.get('query', QUERY_PREFIX_DEFAULT)
    document_prefix = prompts.get('document', prompts.get('doc', DOCUMENT_PREFIX_DEFAULT))
    started = time.monotonic()
    model = load_embedding_model(model_path)
    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
    loaded = time.monotonic()
    document_vectors, document_tokens, document_truncated = _encode(model, tokenizer, mx, [row['text'] for row in input_payload['documents']], document_prefix, batch_size)
    query_vectors, query_tokens, query_truncated = _encode(model, tokenizer, mx, [row['text'] for row in input_payload['queries']], query_prefix, batch_size)
    curriculum_vectors, curriculum_tokens, curriculum_truncated = _encode(model, tokenizer, mx, [row['text'] for row in input_payload['curriculum']], query_prefix, batch_size)
    encoded = time.monotonic()
    if any(len(vector) != 768 for vector in document_vectors + query_vectors + curriculum_vectors):
        raise ValueError('EMBEDDING_DIMENSION_768_REQUIRED')

    documents = [dict(row, vector_768=vector, vector_256=project(vector))
                 for row, vector in zip(input_payload['documents'], document_vectors)]
    doc_768 = [{'candidate_id': row['candidate_id'], 'vector': row['vector_768']} for row in documents]
    doc_256 = [{'candidate_id': row['candidate_id'], 'vector': row['vector_256']} for row in documents]
    queries = []
    for row, vector in zip(input_payload['queries'], query_vectors):
        queries.append(dict(row, vector_768=vector, vector_256=project(vector), rankings={
            '768': rank(vector, doc_768), '256': rank(project(vector), doc_256)}))
    curriculum = [dict(row, vector_768=vector, vector_256=project(vector))
                  for row, vector in zip(input_payload['curriculum'], curriculum_vectors)]
    retrieved = time.monotonic()
    try:
        mlx_vlm_version = importlib.metadata.version('mlx-vlm')
    except importlib.metadata.PackageNotFoundError:
        mlx_vlm_version = None
    try:
        mlx_version = importlib.metadata.version('mlx')
    except importlib.metadata.PackageNotFoundError:
        mlx_version = None
    return {
        'version': VERSION, 'input_version': input_payload.get('version'),
        'documents': documents, 'queries': queries, 'curriculum': curriculum,
        'corpus_sha256': hashlib.sha256(json.dumps(input_payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
        'model': {'name': MODEL_NAME, 'path': str(model_path), 'file_sha256': _model_hashes(model_path),
                  'direct_url': _direct_url(), 'backend': 'native MLX', 'mlx_version': mlx_version,
                  'mlx_vlm_version': mlx_vlm_version, 'documented_artifact_precision': 'bfloat16',
                  'native_loader_file_sha256': _sha256(Path(embedding_loader.__file__))},
        'prefixes': {'query': query_prefix, 'document': document_prefix},
        'runtime': {'python': sys.version, 'executable': str(Path(sys.executable).absolute()),
                    'executable_sha256': _sha256(Path(sys.executable)), 'platform': platform.platform()},
        'resource': {'wall_seconds': round(retrieved - started, 6), 'load_seconds': round(loaded - started, 6),
                     'encoding_seconds': round(encoded - loaded, 6), 'retrieval_seconds': round(retrieved - encoded, 6),
                     'rss_max': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                     'rss_unit': 'bytes on macOS; KiB on Linux',
                     'mlx_peak_memory_bytes': mx.get_peak_memory(),
                     'token_counts': {'documents': document_tokens, 'queries': query_tokens, 'curriculum': curriculum_tokens},
                     'truncation': {'policy': 'tokenizer truncation', 'max_length': 256,
                                    'documents': document_truncated, 'queries': query_truncated,
                                    'curriculum': curriculum_truncated},
                     'cache_miss': len(documents) + len(queries) + len(curriculum), 'cache_hit': 0}
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--model', required=True, type=Path)
    parser.add_argument('--batch-size', default=8, type=int, choices=(8, 16))
    args = parser.parse_args(argv)
    if args.output.exists():
        raise FileExistsError('OUTPUT_ALREADY_EXISTS')
    if not args.model.is_dir():
        raise ValueError('MODEL_PATH_REQUIRED')
    payload = build_retrieval(_load_input(args.input), args.model, args.batch_size)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as target:
        json.dump(payload, target, indent=2, sort_keys=True, allow_nan=False)
        target.write('\n')


if __name__ == '__main__':
    main()
