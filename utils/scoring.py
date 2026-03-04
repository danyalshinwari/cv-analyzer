"""
Dataset-Powered Universal Resume Scoring Engine
================================================
Uses resume_data.csv (50k+ real resumes) to power accurate scoring.
Falls back to manual taxonomy if dataset is unavailable.
"""

import re
from utils.dataset_loader import (
    load_dataset_index,
    get_all_known_skills,
    get_global_skill_freq,
    is_dataset_loaded,
)

# ─── Manual fallback taxonomy (used when dataset not available) ───────────────
MANUAL_SKILLS = {
    "tech":       ["python","java","javascript","typescript","c++","c#","go","rust","ruby","php","swift","kotlin","scala","r","matlab",
                   "react","angular","vue","django","flask","fastapi","spring","nodejs","express","nextjs","tensorflow","pytorch","scikit",
                   "aws","azure","gcp","docker","kubernetes","terraform","ansible","jenkins","linux","nginx","ci/cd","devops",
                   "git","sql","mysql","postgresql","mongodb","redis","kafka","graphql","rest","api","microservices","agile","scrum"],
    "medicine":   ["clinical","diagnosis","patient care","surgery","pharmacology","anatomy","physiology","pathology","radiology","oncology",
                   "cardiology","neurology","pediatrics","psychiatry","emergency medicine","ecg","ultrasound","mri","cpr","triage","icu",
                   "epidemiology","public health","vaccination","nursing","pharmacy","rehabilitation"],
    "law":        ["litigation","contract","legal research","compliance","regulatory","corporate law","criminal law","civil law",
                   "intellectual property","arbitration","mediation","due diligence","legal drafting","statute","gdpr","employment law",
                   "family law","tax law","immigration","paralegal","attorney","counsel"],
    "finance":    ["financial modeling","valuation","investment","portfolio","equity","derivatives","risk management","accounting",
                   "gaap","ifrs","audit","tax","financial reporting","budgeting","forecasting","excel","bloomberg","trading",
                   "asset management","private equity","venture capital","banking","credit analysis","corporate finance","cfa","acca","cpa"],
    "business":   ["strategy","operations","project management","stakeholder management","business development","market research",
                   "product management","supply chain","procurement","logistics","kpi","okr","six sigma","lean","change management",
                   "business analysis","crm","salesforce","negotiation","consulting","erp","sap","oracle"],
    "marketing":  ["seo","sem","ppc","social media","content marketing","email marketing","brand management","digital marketing",
                   "google analytics","facebook ads","campaign management","copywriting","hubspot","mailchimp","conversion rate","roi"],
    "education":  ["curriculum development","lesson planning","classroom management","pedagogy","assessment","e-learning","moodle",
                   "canvas","instructional design","tutoring","mentoring","teaching","academic research","stem","higher education"],
    "engineering":["autocad","solidworks","catia","ansys","mechanical design","structural analysis","fea","cfd","thermodynamics",
                   "fluid mechanics","manufacturing","iso","civil engineering","structural engineering","plc","scada","pcb design",
                   "embedded systems","control systems","hvac","lean manufacturing"],
    "science":    ["laboratory","research","data analysis","statistics","hypothesis","experiment","biology","chemistry","physics",
                   "genomics","pcr","microscopy","spectroscopy","clinical trials","literature review","grant writing","r&d","spss"],
    "design":     ["figma","sketch","adobe xd","photoshop","illustrator","indesign","after effects","premiere pro","ux design",
                   "ui design","user research","prototyping","wireframing","graphic design","typography","branding","3d modeling"],
    "hr":         ["recruitment","talent acquisition","onboarding","performance management","employee relations","payroll","hris",
                   "workday","bamboohr","compensation","benefits","training","learning and development","diversity","workforce planning"],
    "soft":       ["leadership","communication","teamwork","collaboration","problem solving","analytical","critical thinking",
                   "adaptable","organized","proactive","initiative","ownership","presentation","negotiation","planning","strategic",
                   "mentoring","decision making","time management","creativity","conflict resolution","emotional intelligence"],
}
MANUAL_FLAT = {s for skills in MANUAL_SKILLS.values() for s in skills}

SENIORITY = {
    "senior": ["senior","lead","principal","architect","head of","director","vp ","manager","cto","cfo","ceo",
                "10+ years","8+ years","7+ years","9+ years"],
    "mid":    ["mid","3+ years","4+ years","5+ years","6+ years","intermediate"],
    "junior": ["junior","graduate","entry level","0-2 years","1+ year","intern","trainee","fresher"],
}

EDU_SIGNALS = {
    "degree": ["bachelor","master","phd","b.sc","m.sc","b.eng","m.eng","mba","llb","mbbs","md","bds","bba","bcom","mcom",
               "degree","university","college","graduate","postgraduate"],
    "certs":  ["certified","certification","pmp","cfa","acca","cpa","cka","aws certified","comptia","cisco","chartered",
               "google certified","microsoft certified","oracle","prince2","scrum master"],
}

STOP_WORDS = {
    "the","and","for","with","that","this","from","your","will","are","was","were","been","has","have","had",
    "but","not","what","all","their","they","can","who","which","about","how","when","where","there","any",
    "these","those","must","should","could","would","a","an","to","of","in","is","it","be","do","at","by",
    "we","our","you","use","using","work","working","include","able","good","strong","excellent","experience",
    "skills","role","team","required","responsibilities","knowledge","ability","preferred","candidate","duties",
}


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _norm(text): return text.lower()

def _token_set(text):
    tokens = re.findall(r'\b[a-z][a-z0-9+#/\-\.]{1,25}\b', _norm(text))
    return {t.strip() for t in tokens if t.strip() not in STOP_WORDS and len(t.strip()) > 2}


def _extract_skills(text: str) -> set:
    """
    Extract skills from text using:
    1. Dataset skill vocabulary (if loaded) — 50k+ real resume skills
    2. Manual taxonomy fallback
    Uses whole-phrase matching for multi-word skills.
    """
    tl = _norm(text)
    found = set()

    # Priority 1: dataset known skills
    if is_dataset_loaded():
        all_known = get_all_known_skills()
        for skill in all_known:
            if skill and len(skill) > 2:
                pattern = r'\b' + re.escape(skill) + r'\b'
                if re.search(pattern, tl):
                    found.add(skill)
    
    # Priority 2: manual taxonomy (always apply for reliability)
    for skills in MANUAL_SKILLS.values():
        for skill in skills:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, tl):
                found.add(skill)

    return found


def _skill_weight(skill: str) -> float:
    """
    Returns a weight for a skill based on how common it is in real resumes.
    Rare skills (low freq) are worth more — they signal specialization.
    Common skills (very high freq) are baseline.
    """
    if not is_dataset_loaded():
        return 1.0
    freq = get_global_skill_freq()
    count = freq.get(skill, 1)
    total = sum(freq.values()) or 1
    # IDF-inspired: rarer skills get higher weight
    import math
    idf = math.log((total + 1) / (count + 1)) + 1
    return min(max(idf, 0.5), 3.0)  # clamp between 0.5x and 3x


def _detect_seniority(text):
    tl = _norm(text)
    for level, signals in SENIORITY.items():
        if any(s in tl for s in signals):
            return level
    return "junior"


def _detect_education(text):
    tl = _norm(text)
    return {
        "has_degree": any(s in tl for s in EDU_SIGNALS["degree"]),
        "has_cert":   any(s in tl for s in EDU_SIGNALS["certs"]),
    }


# ─── Main Scoring Function ────────────────────────────────────────────────────

def calculate_advanced_score(resume_text: str, jd_text: str) -> dict:
    """
    Dataset-powered multi-dimensional weighted scoring.
    Works for ALL professional fields.
    """

    # ── 1. Skills Match (35%) — weighted by real-world rarity
    jd_skills  = _extract_skills(jd_text)
    cv_skills  = _extract_skills(resume_text)
    matched_sk = cv_skills & jd_skills
    missing_sk = jd_skills - cv_skills

    if jd_skills:
        jd_weight_total = sum(_skill_weight(s) for s in jd_skills)
        matched_weight  = sum(_skill_weight(s) for s in matched_sk)
        tech_score = round((matched_weight / jd_weight_total) * 100)
    else:
        tech_score = 55

    # ── 2. Domain Keyword Coverage (25%)
    jd_tokens    = _token_set(jd_text)
    cv_tokens    = _token_set(resume_text)
    jd_domain    = jd_tokens - MANUAL_FLAT
    cv_domain    = cv_tokens - MANUAL_FLAT
    matched_dom  = cv_domain & jd_domain
    domain_score = round((len(matched_dom) / len(jd_domain)) * 100) if jd_domain else 55
    domain_score = min(domain_score, 100)

    # ── 3. Experience Level Match (15%)
    cv_level = _detect_seniority(resume_text)
    jd_level = _detect_seniority(jd_text)
    level_map = {"junior": 1, "mid": 2, "senior": 3}
    diff = abs(level_map.get(cv_level, 1) - level_map.get(jd_level, 2))
    exp_score = 100 if diff == 0 else (70 if diff == 1 else 40)

    # ── 4. Soft Skills (10%)
    soft_list = MANUAL_SKILLS.get("soft", [])
    jd_soft = {s for s in soft_list if re.search(r'\b' + re.escape(s) + r'\b', _norm(jd_text))}
    cv_soft = {s for s in soft_list if re.search(r'\b' + re.escape(s) + r'\b', _norm(resume_text))}
    matched_soft = cv_soft & jd_soft
    soft_score = round((len(matched_soft) / len(jd_soft)) * 100) if jd_soft else 60

    # ── 5. Education & Certifications (15%)
    cv_edu = _detect_education(resume_text)
    jd_edu = _detect_education(jd_text)
    edu_score = 50
    if cv_edu["has_degree"]: edu_score += 25
    if cv_edu["has_cert"]:   edu_score += 25
    if jd_edu["has_degree"] and not cv_edu["has_degree"]: edu_score -= 20
    edu_score = max(10, min(100, edu_score))

    # ── Weighted Final Score
    final = (
        tech_score   * 0.35 +
        domain_score * 0.25 +
        exp_score    * 0.15 +
        soft_score   * 0.10 +
        edu_score    * 0.15
    )
    final = round(min(98, max(10, final)))

    return {
        "overall": final,
        "breakdown": {
            "Skills Match":      tech_score,
            "Domain Keywords":   domain_score,
            "Experience Level":  exp_score,
            "Soft Skills":       soft_score,
            "Education & Certs": edu_score,
        },
        "matched_skills": sorted(matched_sk)[:10],
        "missing_skills": sorted(missing_sk, key=lambda s: -_skill_weight(s))[:8],
        "matched_soft":   sorted(matched_soft),
        "cv_level":  cv_level,
        "jd_level":  jd_level,
        "dataset_powered": is_dataset_loaded(),
    }


# ─── Backward Compat ─────────────────────────────────────────────────────────
def calculate_simple_score(resume_text: str, jd_text: str) -> int:
    return calculate_advanced_score(resume_text, jd_text)["overall"]

def get_skill_gap(matched, missing):
    return {"labels": ["Matched", "Missing"], "values": [len(matched), len(missing)]}