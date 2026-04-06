"""
Outfit chat: Ollama + Chroma RAG + wardrobe matching, with offline fallback.
"""
from __future__ import annotations

import json
import logging
import random
import re
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx

from config import Config

logger = logging.getLogger(__name__)

SLOT_CATEGORIES = {
    "top": ["t-shirt", "shirt", "hoodie", "sweater", "jacket"],
    "bottom": ["jeans", "trousers", "shorts"],
    "shoes": ["casual_shoe", "formal_shoe", "sport shoes"],
}

MAX_RAG_TEXT_CHARS = 1000
MAX_WARDROBE_JSON_CHARS = 800


def _looks_vietnamese(text: str) -> bool:
    return bool(re.search(r"[\u00C0-\u1EF9]", text))


def _sanitize_reply_text(s: str) -> str:
    """Strip top_id/bottom_id/shoes_id mentions from natural-language reply."""
    if not s:
        return s
    s = re.sub(
        r"\s*[\(\[]\s*(?:top|bottom|shoes)_id\s*:\s*\d+\s*[\)\]]",
        "",
        s,
        flags=re.IGNORECASE,
    )
    s = re.sub(
        r"\s*,?\s*\b(?:top|bottom|shoes)_id\s*:\s*\d+\b",
        "",
        s,
        flags=re.IGNORECASE,
    )
    s = re.sub(r"\s{2,}", " ", s)
    s = re.sub(r"\s+,", ",", s)
    s = re.sub(r",\s*,", ",", s)
    return s.strip()


def ollama_available(timeout: float = 2.0) -> bool:
    try:
        r = httpx.get(
            f"{Config.OLLAMA_BASE_URL.rstrip('/')}/api/tags",
            timeout=timeout,
        )
        return r.status_code == 200
    except Exception as e:
        logger.warning("Ollama health check failed: %s", e)
        return False


def ollama_embed(text: str) -> List[float]:
    """Embeddings via Ollama — must match ingest/Langflow (e.g. nomic-embed-text)."""
    url = f"{Config.OLLAMA_BASE_URL.rstrip('/')}/api/embeddings"
    payload = {"model": Config.OLLAMA_EMBED_MODEL, "prompt": text}
    with httpx.Client(timeout=Config.OLLAMA_EMBED_TIMEOUT) as client:
        r = client.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
        emb = data.get("embedding")
        if not emb:
            raise ValueError("Ollama embeddings response missing 'embedding'")
        return emb


def chroma_query_rules(user_message: str, k: int) -> Tuple[List[str], float]:
    """Retrieve top-k rule chunks; returns (chunks, elapsed_seconds)."""
    t0 = time.perf_counter()
    if not Config.CHROMA_PERSIST_DIR:
        return [], time.perf_counter() - t0
    try:
        import chromadb

        embedding = ollama_embed(user_message)
        client = chromadb.PersistentClient(path=Config.CHROMA_PERSIST_DIR)
        col = client.get_collection(name=Config.CHROMA_COLLECTION_NAME)
        res = col.query(
            query_embeddings=[embedding],
            n_results=k,
            include=["documents"],
        )
        docs = res.get("documents") or []
        if not docs or not docs[0]:
            return [], time.perf_counter() - t0
        chunks = [d for d in docs[0] if d]
        return chunks, time.perf_counter() - t0
    except Exception as e:
        logger.warning("Chroma query failed: %s", e)
        return [], time.perf_counter() - t0


def _wardrobe_compact(items: List[Any], max_items: int) -> List[Dict[str, Any]]:
    out = []
    for i in items[:max_items]:
        out.append(
            {
                "id": i.id,
                "category": i.category,
                "primary_color": i.primary_color,
                "material": i.material,
            }
        )
    return out


def _wardrobe_json_limited(all_items: List[Any]) -> str:
    for n in (16, 12, 8, 6, 4, 3):
        s = json.dumps(_wardrobe_compact(all_items, n), ensure_ascii=False)
        if len(s) <= MAX_WARDROBE_JSON_CHARS:
            return s
    return json.dumps(_wardrobe_compact(all_items, 2), ensure_ascii=False)[
        :MAX_WARDROBE_JSON_CHARS
    ]


def _rag_text_limited(chunks: List[str]) -> str:
    if not chunks:
        return ""
    raw = "\n".join(chunks)
    if len(raw) <= MAX_RAG_TEXT_CHARS:
        return raw
    return raw[: MAX_RAG_TEXT_CHARS - 3] + "..."


def _pick_first_slot(items: List[Any], slot: str) -> Optional[Any]:
    cats = set(SLOT_CATEGORIES[slot])
    for it in items:
        if it.category in cats:
            return it
    return None


def _fallback_outfit(
    all_items: List[Any], user_message: str, offline: bool = True
) -> Tuple[str, Optional[int], Optional[int], Optional[int], List[str]]:
    tops = [i for i in all_items if i.category in SLOT_CATEGORIES["top"]]
    bottoms = [i for i in all_items if i.category in SLOT_CATEGORIES["bottom"]]
    shoes = [i for i in all_items if i.category in SLOT_CATEGORIES["shoes"]]

    msg_l = user_message.lower()
    shopping: List[str] = []

    def prefer_light(items):
        for w in ("nóng", "summer", "nắng", "hot", "beach"):
            if w in msg_l or w in user_message:
                return [x for x in items if x.primary_color and "white" in x.primary_color.lower()] or items
        return items

    tops = prefer_light(tops) if tops else tops
    bottoms = bottoms or []
    shoes = shoes or []

    t = random.choice(tops) if tops else None
    b = random.choice(bottoms) if bottoms else None
    s = random.choice(shoes) if shoes else None

    if offline:
        if _looks_vietnamese(user_message):
            reply = (
                "Không kết nối được tới Ollama (máy chủ LLM). "
                "Đây là gợi ý đơn giản từ tủ đồ. Hãy mở Ollama rồi thử lại."
            )
        else:
            reply = (
                "Can't reach Ollama (LLM server). Here's a simple pick from your wardrobe. "
                "Start Ollama and try again."
            )
    else:
        if _looks_vietnamese(user_message):
            reply = (
                "Mô hình AI trả lời quá lâu hoặc lỗi. "
                "Đây là gợi ý đơn giản từ tủ đồ; bạn có thể thử lại hoặc giảm số món trong tủ."
            )
        else:
            reply = (
                "The AI model timed out or returned an error. "
                "Here's a simple outfit from your wardrobe — try again or use a smaller/faster model in .env."
            )

    if not t and SLOT_CATEGORIES["top"]:
        shopping.append("lightweight top (e.g. cotton t-shirt)")
    if not b and SLOT_CATEGORIES["bottom"]:
        shopping.append("versatile bottoms (e.g. jeans or chinos)")
    if not s and SLOT_CATEGORIES["shoes"]:
        shopping.append("neutral sneakers or casual shoes")

    return (
        reply,
        t.id if t else None,
        b.id if b else None,
        s.id if s else None,
        shopping,
    )


def _call_ollama_generate(prompt: str) -> Tuple[str, float]:
    url = f"{Config.OLLAMA_BASE_URL.rstrip('/')}/api/generate"
    payload = {
        "model": Config.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": Config.OLLAMA_GENERATE_TEMPERATURE,
            "num_predict": Config.OLLAMA_NUM_PREDICT,
        },
    }
    timeout = httpx.Timeout(
        connect=10.0,
        read=Config.OLLAMA_GENERATE_TIMEOUT,
        write=10.0,
        pool=10.0,
    )
    t0 = time.perf_counter()
    with httpx.Client(timeout=timeout) as client:
        r = client.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
        text = (data.get("response") or "").strip()
    elapsed = time.perf_counter() - t0
    return text, elapsed


def _balanced_json_object(text: str) -> Optional[str]:
    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def _regex_fallback_outfit(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    reply_m = re.search(r'"reply"\s*:\s*"((?:[^"\\]|\\.)*)"', text, re.DOTALL)
    reply = reply_m.group(1) if reply_m else None
    if reply is None:
        reply_m2 = re.search(r'"reply"\s*:\s*"([^"]*)"', text)
        reply = reply_m2.group(1) if reply_m2 else None
    if not reply:
        return None

    def _id_field(name: str) -> Optional[int]:
        m = re.search(rf'"{re.escape(name)}"\s*:\s*(null|\d+)', text)
        if not m:
            return None
        if m.group(1) == "null":
            return None
        try:
            return int(m.group(1))
        except ValueError:
            return None

    hints: List[str] = []
    hm = re.search(r'"shopping_hints"\s*:\s*\[(.*?)\]', text, re.DOTALL)
    if hm:
        for qm in re.finditer(r'"((?:[^"\\]|\\.)*)"', hm.group(1)):
            hints.append(qm.group(1))
    return {
        "reply": reply.replace("\\n", "\n").replace('\\"', '"'),
        "top_id": _id_field("top_id"),
        "bottom_id": _id_field("bottom_id"),
        "shoes_id": _id_field("shoes_id"),
        "shopping_hints": hints[:5],
    }


def _parse_json_from_llm(text: str) -> Optional[Dict[str, Any]]:
    text = (text or "").strip()
    if not text:
        return None
    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) >= 2:
            inner = parts[1]
            if inner.lstrip().startswith("json"):
                inner = inner.lstrip()[4:]
            text = inner.strip()

    candidates: List[str] = [text]
    bal = _balanced_json_object(text)
    if bal:
        candidates.append(bal)
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        candidates.append(m.group(0))

    seen: set[str] = set()
    for cand in candidates:
        if cand in seen:
            continue
        seen.add(cand)
        try:
            obj = json.loads(cand)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue

    return _regex_fallback_outfit(text)


def _validate_ids(
    top_id: Optional[int],
    bottom_id: Optional[int],
    shoes_id: Optional[int],
    by_id: Dict[int, Any],
) -> Tuple[Optional[int], Optional[int], Optional[int]]:
    def ok(slot: str, iid: Optional[int]) -> Optional[int]:
        if iid is None:
            return None
        it = by_id.get(int(iid))
        if not it or it.category not in SLOT_CATEGORIES[slot]:
            return None
        return int(iid)

    return ok("top", top_id), ok("bottom", bottom_id), ok("shoes", shoes_id)


def build_outfit_suggestion(
    user_message: str,
    all_items: List[Any],
    regenerate: bool = False,
) -> Dict[str, Any]:
    by_id = {i.id: i for i in all_items}
    wardrobe_json = _wardrobe_json_limited(all_items)

    k = Config.CHROMA_QUERY_K
    rag_chunks, rag_s = chroma_query_rules(user_message, k=k)
    used_rag = len(rag_chunks) > 0
    rag_text = _rag_text_limited(rag_chunks)
    if not rag_text:
        rag_text = "(none)"

    logger.info("outfit_chat rag_retrieval_ms=%.1f", rag_s * 1000)

    if not ollama_available():
        reply, tid, bid, sid, shop = _fallback_outfit(all_items, user_message, offline=True)
        return {
            "reply": reply,
            "top_id": tid,
            "bottom_id": bid,
            "shoes_id": sid,
            "shopping_hints": shop,
            "used_rag": used_rag,
            "used_llm": False,
            "fallback": True,
        }

    lang = "VI" if _looks_vietnamese(user_message) else "EN"
    reg = "alt" if regenerate else "1st"

    prompt = (
        f"Fashion assistant. Lang:{lang}. Reg:{reg}.\n"
        f"Rules:\n{rag_text}\n\n"
        f"Wardrobe JSON:\n{wardrobe_json}\n\n"
        f"User: {user_message}\n\n"
        "Reply: 1 short paragraph of natural styling advice only. Do NOT mention item ids, "
        "top_id, bottom_id, shoes_id, or numbers in parentheses in the reply text.\n"
        "Pick top_id,bottom_id,shoes_id from wardrobe JSON only "
        "(categories: top=t-shirt,shirt,hoodie,sweater,jacket; bottom=jeans,trousers,shorts; "
        "shoes=casual_shoe,formal_shoe,sport shoes). null+shopping_hints if missing.\n"
        'JSON only: {"reply":"...","top_id":null,"bottom_id":null,"shoes_id":null,"shopping_hints":[]}'
    )

    try:
        raw, llm_s = _call_ollama_generate(prompt)
        logger.info("outfit_chat llm_generate_ms=%.1f", llm_s * 1000)

        parsed = _parse_json_from_llm(raw)
        if not parsed:
            raise ValueError("LLM did not return parseable JSON")

        reply = _sanitize_reply_text(
            str(parsed.get("reply") or "Here is a suggestion.").strip()
        )
        tid, bid, sid = _validate_ids(
            parsed.get("top_id"),
            parsed.get("bottom_id"),
            parsed.get("shoes_id"),
            by_id,
        )
        hints = parsed.get("shopping_hints") or []
        if not isinstance(hints, list):
            hints = []
        hints = [str(h) for h in hints][:5]

        if tid is None:
            t = _pick_first_slot(all_items, "top")
            tid = t.id if t else None
        if bid is None:
            b = _pick_first_slot(all_items, "bottom")
            bid = b.id if b else None
        if sid is None:
            s = _pick_first_slot(all_items, "shoes")
            sid = s.id if s else None

        return {
            "reply": reply,
            "top_id": tid,
            "bottom_id": bid,
            "shoes_id": sid,
            "shopping_hints": hints,
            "used_rag": used_rag,
            "used_llm": True,
            "fallback": False,
        }
    except Exception as e:
        logger.exception("LLM path failed: %s", e)
        reply, tid, bid, sid, shop = _fallback_outfit(all_items, user_message, offline=False)
        return {
            "reply": reply,
            "top_id": tid,
            "bottom_id": bid,
            "shoes_id": sid,
            "shopping_hints": shop,
            "used_rag": used_rag,
            "used_llm": False,
            "fallback": True,
        }
