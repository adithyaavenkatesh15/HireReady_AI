"""
tools/keyword_extractor.py

Lightweight keyword extraction utilities used to compare resume content
against job descriptions without needing an LLM call for every check.
"""

import re

STOPWORDS = {
    "the", "and", "for", "with", "you", "our", "are", "will", "have",
    "has", "that", "this", "from", "your", "who", "job", "role", "team",
    "work", "years", "year", "experience", "ability", "strong", "skills",
    "including", "such", "etc", "into", "using", "used", "use", "can",
    "we", "a", "an", "of", "in", "on", "to", "is", "as", "be", "or",
    "at", "by", "it", "their", "them", "they", "you'll", "we're",
}


def tokenize(text: str) -> list:
    """
    Lowercase and split text into cleaned word tokens.
    """
    words = re.findall(r"[A-Za-z][A-Za-z0-9+#.\-]*", text.lower())
    return [w.strip(".-") for w in words if len(w) > 1]


def extract_keywords(text: str, top_n: int = 40) -> list:
    """
    Extract the most frequent meaningful keywords from a block of text.

    Args:
        text: Raw text (job description or resume).
        top_n: Maximum number of keywords to return.

    Returns:
        list[str]: Ranked keywords, most frequent first.
    """
    tokens = tokenize(text)
    filtered = [t for t in tokens if t not in STOPWORDS]

    frequency = {}
    for token in filtered:
        frequency[token] = frequency.get(token, 0) + 1

    ranked = sorted(frequency.items(), key=lambda pair: pair[1], reverse=True)
    return [word for word, _ in ranked[:top_n]]


def find_missing_keywords(resume_text: str, job_description: str, top_n: int = 30) -> list:
    """
    Return job-description keywords that do not appear anywhere in the
    resume text.
    """
    if not job_description:
        return []

    job_keywords = extract_keywords(job_description, top_n=top_n)
    resume_tokens = set(tokenize(resume_text))

    return [kw for kw in job_keywords if kw not in resume_tokens]


def calculate_keyword_overlap_percent(resume_text: str, job_description: str) -> int:
    """
    Calculate a simple percentage of job-description keywords that are
    also present in the resume text. Used as a numeric baseline for the
    Job Matching Agent.
    """
    if not job_description:
        return 0

    job_keywords = set(extract_keywords(job_description, top_n=40))
    if not job_keywords:
        return 0

    resume_tokens = set(tokenize(resume_text))
    matched = job_keywords.intersection(resume_tokens)

    return round((len(matched) / len(job_keywords)) * 100)
