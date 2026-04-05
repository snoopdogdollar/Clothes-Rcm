"""
Outfit chat: Ollama + Chroma RAG + wardrobe matching, with offline fallback.
"""
from __future__ import annotations

import json
import logging
import random
import re
from typing import Any, Dict, List, Optional, Tuple

import httpx

from config import Config

logger = logging.getLogger(__name__)

SLOT_CATEGORIES = {
    "top": ["t-shirt", "shirt", "hoodie", "sweater", "jacket"],
    "bottom": ["jeans", "trousers", "shorts"],
    "shoes": ["casual_shoe", "formal_shoe", "sport shoes"],
}


def _looks_vietnamese(text: str) -> bool:
    return bool(re.search(r"[\u00C0-\u1EF9]", text))


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
    """
    Embeddings via Ollama — must match ingest/Langflow (e.g. nomic-embed-text).
    POST /api/embeddings
    """
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


def chroma_query_rules(user_message: str, k: int = 5) -> List[str]:
    """Retrieve top-k rule chunks using same embeddings as indexed data (Ollama nomic-embed-text)."""
    if not Config.CHROMA_PERSIST_DIR:
        return []
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
            return []
        return [d for d in docs[0] if d]
    except Exception as e:
        logger.warning("Chroma query failed: %s", e)
        return []


def _wardrobe_compact(items: List[Any], max_items: int = 48) -> List[Dict[str, Any]]:
    """Keep prompt small for CPU / faster generation."""
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


def _pick_first_slot(
    items: List[Any], slot: str
) -> Optional[Any]:
    cats = set(SLOT_CATEGORIES[slot])
    for it in items:
        if it.category in cats:
            return it
    return None


def _fallback_outfit(
    all_items: List[Any], user_message: str, offline: bool = True
) -> Tuple[str, Optional[int], Optional[int], Optional[int], List[str]]:
    """Rule-based when Ollama is unreachable (offline=True) or LLM failed after connect (offline=False)."""
    tops = [i for i in all_items if i.category in SLOT_CATEGORIES["top"]]
    bottoms = [i for i in all_items if i.category in SLOT_CATEGORIES["bottom"]]
    shoes = [i for i in all_items if i.category in SLOT_CATEGORIES["shoes"]]

    msg_l = user_message.lower()
    shopping: List[str] = []

    # Very light keyword bias (VN + EN)
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


def _call_ollama_generate(prompt: str) -> str:
    url = f"{Config.OLLAMA_BASE_URL.rstrip('/')}/api/generate"
    payload = {
        "model": Config.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.35, "num_predict": 512},
    }
    timeout = httpx.Timeout(
        connect=15.0,
        read=Config.OLLAMA_GENERATE_TIMEOUT,
        write=15.0,
        pool=15.0,
    )
    with httpx.Client(timeout=timeout) as client:
        r = client.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
        return (data.get("response") or "").strip()


def _parse_json_from_llm(text: str) -> Optional[Dict[str, Any]]:
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) >= 2:
            inner = parts[1]
            if inner.lstrip().startswith("json"):
                inner = inner.lstrip()[4:]
            text = inner.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
    return None


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
    """
    Returns dict: reply, top_id, bottom_id, shoes_id, shopping_hints, used_rag, used_llm
    """
    by_id = {i.id: i for i in all_items}
    wardrobe_json = json.dumps(_wardrobe_compact(all_items), ensure_ascii=False)[:8000]

    rag_chunks = chroma_query_rules(user_message, k=Config.CHROMA_QUERY_K)
    used_rag = len(rag_chunks) > 0
    rag_text = "\n---\n".join(rag_chunks) if rag_chunks else "(no retrieved rules; use general good taste)"

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

    lang_hint = (
        "Reply in Vietnamese."
        if _looks_vietnamese(user_message)
        else "Reply in English."
    )

    prompt = f"""You are a fashion assistant. {lang_hint}

Fashion rules (from knowledge base):
{rag_text}

User wardrobe (JSON array of items with id, category, primary_color, material):
{wardrobe_json}

User request:
{user_message}

Instructions:
1) Give practical styling advice in 2-4 short paragraphs.
2) Pick item ids from the wardrobe JSON ONLY for top, bottom, shoes slots when possible. Categories must match:
   - top: t-shirt, shirt, hoodie, sweater, jacket
   - bottom: jeans, trousers, shorts
   - shoes: casual_shoe, formal_shoe, sport shoes
3) If a slot cannot be filled from wardrobe, set that id to null and add a short shopping hint to shopping_hints array.
4) Respond with ONLY valid JSON (no markdown), exactly this shape:
{{"reply":"...","top_id":null,"bottom_id":null,"shoes_id":null,"shopping_hints":[]}}

Optional regenerate hint: {"user asked for another option" if regenerate else "first suggestion"}
"""

    try:
        raw = _call_ollama_generate(prompt)
        parsed = _parse_json_from_llm(raw)
        if not parsed:
            raise ValueError("LLM did not return JSON")

        reply = str(parsed.get("reply") or "Here is a suggestion.").strip()
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

        # Fill missing slots with first available if LLM left null but we have stock
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
