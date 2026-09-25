import csv
import json
import re
import statistics
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = PROJECT_ROOT / "BUP_RAG_Test_Questions.csv"
API_URL = "http://127.0.0.1:8000/query"
OUTPUT_CSV_PATH = PROJECT_ROOT / "Backend" / "tests" / "results" / "BUP_RAG_Test_Questions_evaluated.csv"
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


@dataclass
class EvalResult:
    question: str
    expected_answer: str
    source_document: str
    actual_answer: str
    retrieval_hit: bool
    f1_score: float
    semantic_similarity: float = 0.0
    bertscore_f1: float = 0.0


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def token_overlap_score(prediction: str, reference: str) -> float:
    pred_tokens = normalize_text(prediction).split()
    ref_tokens = normalize_text(reference).split()
    if not pred_tokens and not ref_tokens:
        return 1.0
    if not pred_tokens or not ref_tokens:
        return 0.0

    common = set(pred_tokens) & set(ref_tokens)
    if not common:
        return 0.0

    precision = len(common) / len(set(pred_tokens))
    recall = len(common) / len(set(ref_tokens))
    return 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0


def add_semantic_similarity(results: list[EvalResult]) -> None:
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    references = model.encode(
        [item.expected_answer for item in results],
        normalize_embeddings=True,
    )
    predictions = model.encode(
        [item.actual_answer for item in results],
        normalize_embeddings=True,
    )
    scores = cosine_similarity(predictions, references).diagonal()
    for item, score in zip(results, scores):
        item.semantic_similarity = float(score)


def add_bertscore(results: list[EvalResult]) -> None:
    try:
        from bert_score import score
    except ImportError as exc:
        raise RuntimeError(
            "BERTScore is not installed. Run: pip install bert-score==0.3.13"
        ) from exc

    _, _, f1_scores = score(
        [item.actual_answer for item in results],
        [item.expected_answer for item in results],
        lang="en",
        verbose=True,
    )
    for item, score_value in zip(results, f1_scores):
        item.bertscore_f1 = float(score_value)


def call_query_api(question: str, top_k: int = 4, timeout_seconds: int = 300):
    payload = {
        "user_id": "rag-eval-runner",
        "question": question,
        "top_k": top_k,
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(API_URL, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
        body = response.read().decode("utf-8")
        if not body:
            return {}
        return json.loads(body)


def evaluate_row(row: dict) -> EvalResult:
    question = (row.get("question") or "").strip()
    expected_answer = (row.get("answer") or "").strip()
    source_document = (row.get("source_document") or "").strip()

    if not question:
        raise ValueError("CSV row is missing a question")

    try:
        data = call_query_api(question, top_k=4, timeout_seconds=300)
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Failed to reach API for question: {question!r} | {exc}") from exc

    actual_answer = str(data.get("answer") or "")
    sources = data.get("sources") or []
    source_names = []
    for source in sources:
        if isinstance(source, dict):
            source_names.append(str(source.get("source_name") or "").lower())
            source_names.append(str(source.get("doc_id") or "").lower())
        else:
            source_names.append(str(source).lower())

    normalized_expected_source = source_document.lower()
    retrieval_hit = any(normalized_expected_source in name for name in source_names) or any(
        name in normalized_expected_source for name in source_names
    )

    f1 = token_overlap_score(actual_answer, expected_answer)

    return EvalResult(
        question=question,
        expected_answer=expected_answer,
        source_document=source_document,
        actual_answer=actual_answer,
        retrieval_hit=retrieval_hit,
        f1_score=f1,
    )


def read_csv_rows(csv_path: Path):
    with csv_path.open("r", encoding="utf-8", newline="") as fp:
        reader = csv.DictReader(fp)
        rows = list(reader)
    if not rows:
        raise ValueError(f"No rows found in {csv_path}")
    return rows


def print_summary(results):
    f1_values = [item.f1_score for item in results]
    retrieval_hits = [1 if item.retrieval_hit else 0 for item in results]
    semantic_values = [item.semantic_similarity for item in results]
    bertscore_values = [item.bertscore_f1 for item in results]

    print("\n=== RAG Evaluation Summary ===")
    print(f"Total questions: {len(results)}")
    print(f"Average F1: {statistics.mean(f1_values):.3f}")
    print(f"Retrieval hit rate: {statistics.mean(retrieval_hits):.3f}")
    print(f"Average semantic similarity: {statistics.mean(semantic_values):.3f}")
    print(f"Average BERTScore F1: {statistics.mean(bertscore_values):.3f}")
    print("\nDetailed results:")
    for i, item in enumerate(results, start=1):
        print(f"{i}. Q: {item.question[:80]}")
        print(
            f"   F1: {item.f1_score:.3f} | Retrieval hit: {item.retrieval_hit} "
            f"| Semantic: {item.semantic_similarity:.3f} "
            f"| BERTScore F1: {item.bertscore_f1:.3f}"
        )
        print(f"   Generated: {item.actual_answer[:200]}")
        print(f"   Expected:  {item.expected_answer[:200]}")
        print()


def save_evaluated_csv(rows: list[dict], results: list[EvalResult]) -> Path:
    OUTPUT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    output_rows = []
    for row, result in zip(rows, results):
        output_row = dict(row)
        output_row.update(
            {
                "ollama_answer": result.actual_answer,
                "f1_score": f"{result.f1_score:.6f}",
                "retrieval_hit": result.retrieval_hit,
                "semantic_similarity": f"{result.semantic_similarity:.6f}",
                "bertscore_f1": f"{result.bertscore_f1:.6f}",
            }
        )
        output_rows.append(output_row)

    fieldnames = list(output_rows[0])
    with OUTPUT_CSV_PATH.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)
    return OUTPUT_CSV_PATH


def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV file not found: {CSV_PATH}")

    rows = read_csv_rows(CSV_PATH)
    results = [evaluate_row(row) for row in rows]
    add_semantic_similarity(results)
    add_bertscore(results)
    print_summary(results)
    output_path = save_evaluated_csv(rows, results)
    print(f"Saved evaluated table: {output_path}")


if __name__ == "__main__":
    main()
