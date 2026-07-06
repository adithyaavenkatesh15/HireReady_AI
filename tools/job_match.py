"""
tools/job_match.py

Computes semantic similarity between a resume and a job description
using SentenceTransformers embeddings and FAISS for similarity search.

This provides a numeric, embedding-based match score that complements
the LLM-driven qualitative analysis from the Job Matching Agent.
"""

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

_MODEL_NAME = "all-MiniLM-L6-v2"
_model = None  # Lazy-loaded singleton to avoid reloading on every call


def _get_model() -> SentenceTransformer:
    """
    Lazily load and cache the SentenceTransformer embedding model.
    """
    global _model
    if _model is None:
        _model = SentenceTransformer(_MODEL_NAME)
    return _model


def _embed(texts: list) -> np.ndarray:
    """
    Generate normalized embeddings for a list of text chunks.
    """
    model = _get_model()
    embeddings = model.encode(texts, convert_to_numpy=True)
    faiss.normalize_L2(embeddings)
    return embeddings.astype("float32")


def calculate_semantic_similarity(resume_text: str, job_description: str) -> int:
    """
    Calculate a semantic similarity score (0-100) between a resume and
    a job description using cosine similarity over sentence embeddings,
    computed via a FAISS index for consistency with the rest of the
    similarity-search pipeline.

    Args:
        resume_text: Full extracted resume text.
        job_description: Target job description text.

    Returns:
        int: Similarity percentage between 0 and 100.
    """
    if not job_description or not resume_text:
        return 0

    embeddings = _embed([job_description, resume_text])

    job_vector = embeddings[0:1]
    resume_vector = embeddings[1:2]

    index = faiss.IndexFlatIP(job_vector.shape[1])
    index.add(resume_vector)

    similarity_scores, _ = index.search(job_vector, k=1)
    similarity = float(similarity_scores[0][0])

    # Cosine similarity ranges roughly -1..1; clamp and scale to 0-100
    similarity = max(0.0, min(1.0, similarity))
    return round(similarity * 100)


def rank_resume_sections_by_relevance(sections: list, job_description: str) -> list:
    """
    Rank arbitrary resume text sections (e.g. individual project
    descriptions) by relevance to the job description using FAISS
    similarity search.

    Args:
        sections: List of text chunks (e.g. project or experience blurbs).
        job_description: Target job description text.

    Returns:
        list[tuple[str, float]]: Sections paired with similarity scores,
        sorted most relevant first.
    """
    if not sections or not job_description:
        return []

    section_embeddings = _embed(sections)
    job_embedding = _embed([job_description])

    index = faiss.IndexFlatIP(section_embeddings.shape[1])
    index.add(section_embeddings)

    scores, indices = index.search(job_embedding, k=len(sections))

    ranked = [
        (sections[idx], float(score))
        for score, idx in zip(scores[0], indices[0])
        if idx != -1
    ]

    return ranked
