import re
from pathlib import Path

POLICY_DIR = Path(__file__).resolve().parent.parent / "data" / "policies"

STOP_WORDS = {
    "a", "an", "the", "is", "are", "can", "i", "we",
    "to", "of", "for", "and", "in", "it", "our",
    "what", "how", "does", "do", "with", "be",
}


def keywords(text):
    words = re.findall(r"[a-z0-9]+", text.lower())
    return set(words) - STOP_WORDS


def search_policies(question, limit=3):
    query_words = keywords(question)
    matches = []

    for path in sorted(POLICY_DIR.glob("*.md")):
        document = path.read_text(encoding="utf-8")
        title = document.splitlines()[0].lstrip("# ").strip()

        for section in document.split("\n## ")[1:]:
            heading, _, body = section.partition("\n")
            passage = f"## {heading}\n{body}".strip()
            score = len(query_words & keywords(passage))

            if score:
                matches.append({
                    "source": path.name,
                    "title": title,
                    "passage": passage,
                    "score": score,
                })

    matches.sort(key=lambda item: item["score"], reverse=True)
    return matches[:limit]
