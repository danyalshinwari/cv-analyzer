"""
Dataset Loader — resume_data.csv Integration
=============================================
Parses the uploaded resume dataset to build:
1. A real-world skill frequency index (what skills appear most across resumes)
2. A field-to-skills mapping (what skills are common per field of study)
3. A position-to-skills mapping (what skills recruiters expect per job title)

This is loaded ONCE at startup and used to boost scoring accuracy.
"""

import csv
import re
import ast
import os

DATASET_PATH = os.path.join(os.path.dirname(__file__), "..", "resume_data.csv")

_cache = None


def _parse_list_field(raw: str) -> list:
    """Safely parse a Python list string like "['Python', 'SQL']" into a list."""
    if not raw or not raw.strip():
        return []
    raw = raw.strip()
    # Try ast.literal_eval first
    try:
        parsed = ast.literal_eval(raw)
        if isinstance(parsed, list):
            return [str(s).strip().lower() for s in parsed if str(s).strip()]
    except Exception:
        pass
    # Fallback: strip brackets and split by comma
    raw = re.sub(r"[\[\]'\"]", "", raw)
    return [s.strip().lower() for s in raw.split(",") if s.strip()]


def _clean_token(s: str) -> str:
    return s.strip().lower()


def load_dataset_index() -> dict:
    """
    Reads resume_data.csv and returns:
    {
        "skill_freq":     {skill: count},       # global skill frequency
        "field_skills":   {field: {skills}},     # skills per study field
        "position_skills":{position: {skills}},  # skills per job title
        "all_known_skills": set(),               # all skills seen in dataset
        "loaded": bool
    }
    """
    global _cache
    if _cache is not None:
        return _cache

    index = {
        "skill_freq": {},
        "field_skills": {},
        "position_skills": {},
        "all_known_skills": set(),
        "loaded": False,
    }

    if not os.path.exists(DATASET_PATH):
        print("[Dataset] resume_data.csv not found — using manual taxonomy only.")
        return index

    try:
        with open(DATASET_PATH, encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            rows_processed = 0

            for row in reader:
                if rows_processed >= 5000:   # 5k rows = fast startup & rich index
                    break

                # Parse skills columns
                skills_raw     = _parse_list_field(row.get("skills", ""))
                job_skills_raw = _parse_list_field(row.get("related_skils_in_job", ""))
                all_skills     = skills_raw + job_skills_raw

                # Parse position/field
                positions = _parse_list_field(row.get("positions", ""))
                fields    = _parse_list_field(row.get("major_field_of_studies", ""))

                # Update global skill frequency
                for skill in all_skills:
                    if skill and 2 < len(skill) < 40:
                        index["skill_freq"][skill] = index["skill_freq"].get(skill, 0) + 1
                        index["all_known_skills"].add(skill)

                # Map skills to fields of study
                for field in fields:
                    field = _clean_token(field)
                    if field and len(field) > 2:
                        if field not in index["field_skills"]:
                            index["field_skills"][field] = {}
                        for skill in all_skills:
                            if skill:
                                index["field_skills"][field][skill] = \
                                    index["field_skills"][field].get(skill, 0) + 1

                # Map skills to job positions
                for pos in positions:
                    pos = _clean_token(pos)
                    if pos and len(pos) > 2:
                        if pos not in index["position_skills"]:
                            index["position_skills"][pos] = {}
                        for skill in all_skills:
                            if skill:
                                index["position_skills"][pos][skill] = \
                                    index["position_skills"][pos].get(skill, 0) + 1

                rows_processed += 1

        index["loaded"] = True
        print(f"[Dataset] Loaded {rows_processed} rows. "
              f"{len(index['all_known_skills'])} unique skills indexed. "
              f"{len(index['field_skills'])} fields. "
              f"{len(index['position_skills'])} positions.")

    except Exception as e:
        print(f"[Dataset] Error loading dataset: {e}")

    _cache = index
    return index


def get_top_skills_for_field(field_hint: str, n: int = 20) -> list:
    """Returns the top N skills most common for a given field of study."""
    index = load_dataset_index()
    field_hint = field_hint.lower()

    # Find best matching field key
    best_key = None
    for key in index["field_skills"]:
        if field_hint in key or key in field_hint:
            best_key = key
            break

    if not best_key:
        return []

    skill_counts = index["field_skills"][best_key]
    sorted_skills = sorted(skill_counts, key=skill_counts.get, reverse=True)
    return sorted_skills[:n]


def get_top_skills_for_position(position_hint: str, n: int = 20) -> list:
    """Returns top N skills most common for a given job position/title."""
    index = load_dataset_index()
    position_hint = position_hint.lower()

    best_key = None
    best_score = 0
    for key in index["position_skills"]:
        # Simple overlap scoring
        words_in_hint = set(position_hint.split())
        words_in_key  = set(key.split())
        score = len(words_in_hint & words_in_key)
        if score > best_score:
            best_score = score
            best_key = key

    if not best_key:
        return []

    skill_counts = index["position_skills"][best_key]
    sorted_skills = sorted(skill_counts, key=skill_counts.get, reverse=True)
    return sorted_skills[:n]


def get_global_skill_freq() -> dict:
    """Returns the global skill frequency dictionary."""
    return load_dataset_index()["skill_freq"]


def get_all_known_skills() -> set:
    """Returns all skills seen in the dataset."""
    return load_dataset_index()["all_known_skills"]


def is_dataset_loaded() -> bool:
    return load_dataset_index()["loaded"]
