import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from flask import Flask, jsonify, request

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
_AGENT_CACHE: Dict[str, Any] = {}


def _error_response(message: str, status_code: int = 400):
    return jsonify({"error": message}), status_code


def _normalize_movies(movies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized_movies: List[Dict[str, Any]] = []

    for movie in movies:
        if not isinstance(movie, dict):
            continue

        cleaned = {str(k): ("" if v is None else v) for k, v in movie.items()}
        if not str(cleaned.get("combined_text", "")).strip():
            combined_text = " ".join(
                str(cleaned.get(field, ""))
                for field in ("Name", "Year", "Review")
            ).strip()
            cleaned["combined_text"] = combined_text or str(cleaned)

        normalized_movies.append(cleaned)

    return normalized_movies


def _cache_key(provider: str, movies: List[Dict[str, Any]]) -> str:
    payload = json.dumps(movies, sort_keys=True, default=str)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"{provider.lower()}:{digest}"


def _build_agent(
    provider: str,
    movies: List[Dict[str, Any]],
    loader_stats: Dict[str, Any],
):
    from src.agent import MovieChatbotAgent
    from src.rag_engine import MovieRAGEngine
    from src.utils import create_llm_provider
    from src.vector_store import MovieVectorStore

    persist_dir = os.getenv("VECTOR_STORE_DIR", "/tmp/chroma_db")

    vector_store = MovieVectorStore(persist_dir=persist_dir)
    vector_store.create_collection(name="movies", reset=True)
    vector_store.add_movies(movies)

    llm = create_llm_provider(provider)
    rag_engine = MovieRAGEngine(vector_store, llm)
    return MovieChatbotAgent(rag_engine, llm, loader_stats)


def _get_or_create_agent(
    provider: str,
    movies: List[Dict[str, Any]],
    loader_stats: Dict[str, Any],
):
    key = _cache_key(provider, movies)
    cached_agent = _AGENT_CACHE.get(key)

    if cached_agent is not None:
        return cached_agent

    agent = _build_agent(provider, movies, loader_stats)
    _AGENT_CACHE.clear()
    _AGENT_CACHE[key] = agent
    return agent


@app.route("/", methods=["GET"])
@app.route("/api/chat", methods=["GET"])
def healthcheck():
    return jsonify({"status": "ok", "endpoint": "/api/chat"})


@app.route("/", methods=["POST"])
@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _error_response("Request body must be valid JSON.", 400)

    message = data.get("message", "")
    if not isinstance(message, str) or not message.strip():
        return _error_response("`message` must be a non-empty string.", 400)

    movies_payload = data.get("movies")
    if not isinstance(movies_payload, list) or not movies_payload:
        return _error_response("`movies` must be a non-empty array of movie objects.", 400)

    provider = data.get("provider", "groq")
    if not isinstance(provider, str) or not provider.strip():
        return _error_response("`provider` must be a non-empty string.", 400)

    loader_stats = data.get("loader_stats")
    if loader_stats is not None and not isinstance(loader_stats, dict):
        return _error_response("`loader_stats` must be an object when provided.", 400)

    try:
        movies = _normalize_movies(movies_payload)
        if not movies:
            return _error_response("`movies` must contain at least one valid object.", 400)

        agent = _get_or_create_agent(provider.strip(), movies, loader_stats or {})
        result = agent.execute(message.strip())

        return jsonify(
            {
                "response": result.get("response", ""),
                "action": result.get("action"),
                "movies": result.get("movies", []),
                "conversation_turn": result.get("conversation_turn"),
            }
        )
    except (ImportError, ValueError) as exc:
        logger.error("Chat request validation/runtime error: %s", exc)
        return _error_response(str(exc), 400)
    except Exception as exc:
        logger.exception("Unhandled chat request error")
        return jsonify(
            {
                "error": "Failed to process chat request.",
            }
        ), 500
