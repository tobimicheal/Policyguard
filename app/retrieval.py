import json
import math
from pathlib import Path
from urllib.request import Request, urlopen

POLICY_DIR = Path(__file__).resolve().parent.parent / "data" / "policies"
EMBED_URL = "http://127.0.0.1:11434/api/embed"
EMBED_MODEL = "nomic-embed-text"


def embed(texts):
    payload = {
        "model": EMBED_MODEL,
        "input": texts,
        "truncate": False,
    }

    request = Request(
        EMBED_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request, timeout=180) as response:
        result = json.load(response)

    vectors = result["embeddings"]

    if len(vectors) != len(texts):
        raise ValueError("Unexpected number of embeddings returned.")

    return vectors


def cosine_similarity(first, second):
    if len(first) != len(second):
        raise ValueError("Embedding dimensions do not match.")

    dot_product = sum(a * b for a, b in zip(first, second))
    first_norm = math.sqrt(sum(a * a for a in first))
    second_norm = math.sqrt(sum(b * b for b in second))

    if not first_norm or not second_norm:
        return 0.0

    return dot_product / (first_norm * second_norm)


def search_policies(question, limit=3):
    if not question.strip() or limit <= 0:
        return []

    passages = []

    for path in sorted(POLICY_DIR.glob("*.md")):
        document = path.read_text(encoding="utf-8")
        lines = document.splitlines()

        if not lines:
            continue

        title = lines[0].lstrip("# ").strip()

        for section in document.split("\n## ")[1:]:
            heading, _, body = section.partition("\n")
            passages.append({
                "source": path.name,
                "title": title,
                "passage": f"## {heading}\n{body}".strip(),
            })

    if not passages:
        return []

    texts = ["search_query: " + question]
    texts.extend(
        "search_document: " + item["title"] + "\n" + item["passage"]
        for item in passages
    )

    vectors = embed(texts)
    query_vector = vectors[0]

    for item, vector in zip(passages, vectors[1:]):
        item["score"] = cosine_similarity(query_vector, vector)

    passages.sort(key=lambda item: item["score"], reverse=True)
    return passages[:limit]
