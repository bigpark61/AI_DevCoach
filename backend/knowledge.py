import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


KNOWLEDGE_DIR = Path(__file__).with_name("knowledge")
TOKEN_PATTERN = re.compile(r"[가-힣]+|[a-zA-Z0-9_+#.-]+")


@dataclass(frozen=True)
class KnowledgeChunk:
    source_id: str
    title: str
    content: str


def _tokens(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


def _load_chunks() -> list[KnowledgeChunk]:
    chunks = []
    for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
        sections = re.split(r"(?m)^##\s+", path.read_text(encoding="utf-8"))
        document_title = sections[0].strip().removeprefix("# ").strip()
        for section_index, section in enumerate(sections[1:], start=1):
            heading, _, body = section.partition("\n")
            content = body.strip()
            if content:
                chunks.append(KnowledgeChunk(
                    source_id=f"{path.stem}-{section_index}",
                    title=f"{document_title}: {heading.strip()}",
                    content=content,
                ))
    return chunks


def search_knowledge(query: str, limit: int = 4) -> list[dict[str, str | float]]:
    query_tokens = set(_tokens(query))
    if not query_tokens:
        return []

    chunks = _load_chunks()
    tokenized = [_tokens(chunk.content + " " + chunk.title) for chunk in chunks]
    if not chunks:
        return []

    document_frequency = Counter(token for document in tokenized for token in set(document))
    average_length = sum(map(len, tokenized)) / len(tokenized) or 1
    results = []
    for chunk, document in zip(chunks, tokenized):
        frequencies = Counter(document)
        score = 0.0
        for token in query_tokens:
            frequency = frequencies[token]
            if not frequency:
                continue
            inverse_frequency = math.log1p(
                (len(chunks) - document_frequency[token] + 0.5)
                / (document_frequency[token] + 0.5)
            )
            normalization = frequency + 1.5 * (0.25 + 0.75 * len(document) / average_length)
            score += inverse_frequency * frequency * 2.5 / normalization
        if score > 0:
            results.append({
                "source_id": chunk.source_id,
                "title": chunk.title,
                "content": chunk.content,
                "score": round(score, 4),
            })
    return sorted(results, key=lambda item: float(item["score"]), reverse=True)[:limit]