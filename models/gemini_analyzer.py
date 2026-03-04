import google.generativeai as genai
import json
import re
import random
from config import GOOGLE_API_KEY, MOCK_MODE, GEMINI_MODEL
from utils.prompts import RESUME_ANALYSIS_PROMPT, COVER_LETTER_PROMPT, INTERVIEW_PREP_PROMPT
from utils.scoring import calculate_advanced_score

# Universal Question Bank — All Professional Fields
QUESTION_BANK = {
    "behavioral": [
        {"question": "Tell me about a time you handled a conflict within your team.", "talking_point": "Use STAR method.", "sample_answer": "In my previous role, I noticed a tension between two developers regarding code style. I scheduled a brief sit-down where we agreed on a shared linting configuration. This resolved the immediate friction and improved our overall code consistency."},
        {"question": "Describe a time you failed and what you learned from it.", "talking_point": "Own the failure, emphasize recovery.", "sample_answer": "I once missed a deployment deadline due to poor task estimation. I learned to build in 20% buffer time and communicate delays immediately. Since then, I have met 100% of my delivery targets."},
        {"question": "How do you handle working under tight deadlines?", "talking_point": "Mention prioritization, transparent communication with supervisors, and calm focus on deliverables."},
        {"question": "Describe a time you went above and beyond for a project.", "talking_point": "Tell a story of taking genuine ownership — doing more than what was explicitly required."},
        {"question": "Tell me about a time you had to quickly adapt to a major change.", "talking_point": "Highlight flexibility and problem-solving — how you restructured your approach efficiently."},
        {"question": "How do you handle critical feedback or a difficult review?", "talking_point": "Show emotional intelligence: you listen carefully, thank the person, and actively implement the feedback."},
        {"question": "Tell me about your biggest professional achievement so far.", "talking_point": "Use quantifiable metrics: lives improved, cases won, money saved, students taught, projects delivered."},
        {"question": "Describe a situation where you had to make a difficult decision with limited information.", "talking_point": "Talk about gathering available data, consulting relevant people, and making a calculated decision."},
    ],
    "career": [
        {"question": "Why do you want to work at this organization specifically?", "talking_point": "Reference their mission, reputation, recent work, or values. Connect it to your personal goals."},
        {"question": "Where do you see yourself in 5 years?", "talking_point": "Align your career growth with the organization's needs. Mention deepening expertise or taking on leadership."},
        {"question": "Why are you leaving your current role?", "talking_point": "Stay positive. Frame it as moving toward growth and new challenges, not escaping a problem."},
        {"question": "How do you stay current in your field?", "talking_point": "Name specific journals, conferences, courses, certifications, or professional bodies relevant to your industry."},
        {"question": "What attracted you to this specific field or profession?", "talking_point": "Share a personal story — a defining moment, a passion, or a mentors influence on your career path."},
        {"question": "What do you plan to do in your first 30, 60, and 90 days here?", "talking_point": "Show structure: learn the systems and people, identify quick wins, then contribute meaningfully."},
        {"question": "What motivates you in your professional work?", "talking_point": "Be specific and authentic: solving problems, helping people, creating impact, continuous learning."},
    ],
    "soft_skills": [
        {"question": "How do you prioritize competing tasks and responsibilities?", "talking_point": "Mention frameworks like the Eisenhower Matrix or MoSCoW method, aligned to business/clinical/organizational impact."},
        {"question": "How do you explain complex concepts to someone without your expertise?", "talking_point": "Use analogies, avoid jargon, focus on what matters most to the other person's role or concern."},
        {"question": "How do you handle a situation where you disagree with a superior?", "talking_point": "Show professionalism: data-backed viewpoint, respectful communication, and willingness to defer when needed."},
        {"question": "What is your approach to mentoring or supporting less experienced colleagues?", "talking_point": "Focus on asking questions rather than giving all answers, building confidence, and providing safe learning environments."},
        {"question": "How do you manage stress and maintain performance under pressure?", "talking_point": "Mention focus strategies, breaking tasks into smaller steps, and recognizing when to ask for support."},
        {"question": "Describe how you collaborate effectively across different departments or teams.", "talking_point": "Mention clear communication, understanding others' goals, and finding shared objectives."},
    ],
    "professional_general": [
        {"question": "What methodologies or best practices do you follow in your work?", "talking_point": "Name field-specific standards (e.g., clinical guidelines, legal precedent, financial frameworks, agile, lean). Show discipline."},
        {"question": "How do you ensure accuracy and quality in your deliverables?", "talking_point": "Describe your checking and review process — peer reviews, double-checking, using checklists or standard protocols."},
        {"question": "Tell me about a complex case, project, or problem you solved.", "talking_point": "Walk through the full journey: diagnosis/analysis, your approach, challenges, and the final outcome."},
        {"question": "How do you handle ethical dilemmas in your work?", "talking_point": "Mention adherence to professional codes of conduct, escalation procedures, and documentation."},
        {"question": "What is the most challenging aspect of your field right now?", "talking_point": "Show industry awareness. Reference a genuine current challenge and your perspective on how it should be addressed."},
        {"question": "How do you handle working with difficult clients, patients, or stakeholders?", "talking_point": "Focus on empathy, active listening, setting clear expectations, and documenting everything."},
        {"question": "Tell me about a time you had to learn a new system, tool, or process quickly.", "talking_point": "Highlight your learning strategy: structured approach, asking the right people, hands-on practice."},
        {"question": "How do you ensure you comply with regulations and standards in your field?", "talking_point": "Mention specific compliance bodies, documentation habits, and how you stay updated on regulatory changes."},
        {"question": "What do you consider the most important skill for someone in your field?", "talking_point": "Give a specific, thoughtful answer tied to your own experience and the demands of the role."},
        {"question": "How do you ensure continuous professional development?", "talking_point": "Mention CPD hours, certifications, journals, conferences, or professional memberships relevant to your field."},
    ],
}


def _extract_top_keywords(text, n=8):
    """Extracts meaningful keywords from text."""
    stop = {
        "the","and","for","with","that","this","from","your","will","are","was","were",
        "been","has","have","had","but","not","what","all","their","they","can","who",
        "which","about","how","when","where","there","any","these","those","must",
        "should","could","would","a","an","to","of","in","is","it","be","do","at",
        "by","we","our","use","using","experience","skills","role","team","required",
        "responsibilities","knowledge","ability","preferred","work","working",
    }
    words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9\+\#]{2,15}\b', text)
    freq = {}
    for w in words:
        wl = w.lower()
        if wl not in stop:
            freq[wl] = freq.get(wl, 0) + 1
    return sorted(freq, key=freq.get, reverse=True)[:n]


def _score_to_tier(score):
    if score >= 85: return "🟢 Excellent Match"
    if score >= 70: return "🟡 Strong Match"
    if score >= 50: return "🟠 Fair Match"
    return "🔴 Weak Match"


class GeminiAnalyzer:
    def __init__(self):
        self.mock_mode = MOCK_MODE
        if not self.mock_mode:
            if not GOOGLE_API_KEY or "your-gemini-api-key" in GOOGLE_API_KEY:
                print("WARNING: GOOGLE_API_KEY not found. Switching to MOCK_MODE.")
                self.mock_mode = True
            else:
                genai.configure(api_key=GOOGLE_API_KEY)
                self.model = genai.GenerativeModel(GEMINI_MODEL)

    def analyze_resume(self, resume_text, jd_text):
        """Dataset-powered multi-dimensional resume analysis."""
        if self.mock_mode:
            result = calculate_advanced_score(resume_text, jd_text)
            score   = result["overall"]
            matched = result["matched_skills"] or ["General Professional Skills"]
            missing = result["missing_skills"] or ["Advanced Role-Specific Skills"]
            breakdown = result["breakdown"]
            tier = _score_to_tier(score)
            dataset_powered = result.get("dataset_powered", False)

            # Auto-generate improvement suggestions
            suggestions = []
            if breakdown["Skills Match"] < 60:
                if missing:
                    suggestions.append(f"Priority skills to add: **{', '.join(missing[:3])}** (high-demand in real job market).")
                suggestions.append("Consider adding certifications that validate your key skills.")
            if breakdown["Domain Keywords"] < 60:
                suggestions.append("Mirror the job description's language more closely in your CV bullet points.")
            if breakdown["Experience Level"] < 70:
                suggestions.append("Emphasize leadership, ownership, or mentoring to boost seniority signals.")
            if breakdown["Education & Certs"] < 60:
                suggestions.append("Adding a relevant certification could significantly strengthen your application.")
            if not suggestions:
                suggestions.append("Strong profile! Focus on quantifying your achievements with specific metrics and numbers.")

            source = "Dataset-Powered Analysis (50k+ resumes)" if dataset_powered else "Rule-Based Analysis"
            explanation = (
                f"[{tier}] ({source}) Your CV scores **{score}%** against this job description. "
                f"Skills match: {breakdown['Skills Match']}% · "
                f"Domain keywords: {breakdown['Domain Keywords']}% · "
                f"Experience level: {breakdown['Experience Level']}%."
            )

            return {
                "match_score":    score,
                "score_breakdown": breakdown,
                "matched_skills": matched[:10],
                "missing_skills": missing[:8],
                "improvement_suggestions": suggestions,
                "human_explanation": explanation,
                "tier": tier,
                "dataset_powered": dataset_powered,
                "rewritten_bullets": [
                    {
                        "original": "Worked on various projects.",
                        "rewritten": (
                            f"Led 3+ high-impact projects utilizing {', '.join(matched[:2]) if len(matched) >= 2 else 'core expertise'}, "
                            f"delivering measurable improvements in performance and team productivity."
                        )
                    }
                ]
            }

        prompt = RESUME_ANALYSIS_PROMPT.format(resume_text=resume_text, jd_text=jd_text)
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(response_mime_type="application/json"),
            )
            data = json.loads(response.text)
            data.setdefault("match_score", 0)
            return data
        except Exception as e:
            print(f"Gemini Error: {e}")
            return {"error": str(e), "match_score": 0}

    def generate_cover_letter(self, resume_text, jd_text):
        """Generates a tailored cover letter."""
        if self.mock_mode:
            cv_kw  = _extract_top_keywords(resume_text, 3)
            jd_kw  = _extract_top_keywords(jd_text, 2)
            
            # Generate a verbose mock to meet the 250 word minimum and formal format
            return (
                f"[MOCK GENERATED TEXT]\n\n"
                f"[Your Full Name]\n"
                f"[Your Phone Number] | [Your Email Address] | [Your LinkedIn Profile]\n"
                f"[Your City, State Zip Code]\n\n"
                f"[Current Date]\n\n"
                f"Hiring Manager\n"
                f"[Company Name]\n"
                f"[Company Address]\n"
                f"[City, State Zip Code]\n\n"
                f"Dear Hiring Manager,\n\n"
                f"I am writing to express my strong interest in the {' '.join(jd_kw[:2]).title()} position at your esteemed organization. "
                f"With a proven track record of success and comprehensive hands-on experience in {', '.join(cv_kw)}, "
                f"I am confident in my ability to deliver exceptional results and immediately become a highly valued contributor to your team. "
                f"My career to date has been defined by a deep commitment to excellence, strategic problem-solving, and driving impactful outcomes in demanding environments.\n\n"
                f"My technical background and professional expertise in {', '.join(cv_kw[:2])} directly align with the core requirements outlined in your job description. "
                f"Throughout my previous roles, I have consistently demonstrated a strong capacity to manage complex projects, foster cross-functional collaboration, and implement innovative solutions that optimize performance. "
                f"For example, I have actively leveraged my skills in {', '.join(jd_kw)} to streamline processes, improve operational efficiency, and significantly enhance overall deliverable quality. "
                f"I thrive in dynamic, fast-paced environments where I can apply my analytical capabilities and industry knowledge to overcome challenges and exceed organizational goals.\n\n"
                f"Furthermore, I am particularly drawn to your company's mission and its reputation as an industry leader. "
                f"I am highly motivated by the prospect of bringing my dedication, diverse skill set, and proactive approach to your collaborative work culture. "
                f"I strongly believe that my background not only meets but exceeds the criteria you are looking for, making me an ideal fit for this role. "
                f"I am eager to contribute fresh perspectives, boundless energy, and an unwavering commitment to achieving excellence in every endeavor I undertake.\n\n"
                f"Thank you very much for considering my application. "
                f"I have attached my resume, which provides further details regarding my professional journey and key accomplishments. "
                f"I would welcome the opportunity to discuss how my expertise, enthusiasm, and strategic vision can formally align with the goals of your team. "
                f"I look forward to the possibility of an interview and hope to hear from you soon.\n\n"
                f"Sincerely,\n\n"
                f"[Your Name]"
            )
        prompt = COVER_LETTER_PROMPT.format(resume_text=resume_text, jd_text=jd_text)
        try:
            return self.model.generate_content(prompt).text
        except Exception as e:
            return f"Error: {e}"

    def generate_interview_prep(self, resume_text, jd_text):
        """Generates personalized interview questions from CV and JD content — works for ALL fields."""
        if self.mock_mode:
            cv_kw = _extract_top_keywords(resume_text, 8)
            jd_kw = _extract_top_keywords(jd_text, 8)
            cv_set = set(cv_kw)
            jd_set = set(jd_kw)
            gap_skills = jd_set - cv_set

            questions = []

            # Type 1: JD-specific skill / domain questions
            for skill in list(jd_kw)[:5]:
                questions.append({
                    "question": f"Can you describe your experience or background with {skill.title()}?",
                    "talking_point": f"Give a concrete real-world example where {skill.title()} was central.",
                    "sample_answer": f"I have extensive experience with {skill.title()}, having used it in multiple key projects to drive efficiency and solve complex domain-specific challenges."
                })

            # Type 2: Skill/knowledge gap questions (JD needs it, CV doesn't mention it)
            for skill in list(gap_skills)[:3]:
                questions.append({
                    "question": f"This role requires solid experience with {skill.title()}. How would you rate yourself and how would you bridge any gap quickly?",
                    "talking_point": f"Be honest — show growth mindset.",
                    "sample_answer": f"While my primary focus has been on related areas, I am currently taking an advanced course in {skill.title()} and have already begun implementing its core principles in my side projects."
                })

            # Type 3: Strength highlight from CV keywords
            for skill in list(cv_kw)[:3]:
                questions.append({
                    "question": f"What is your strongest accomplishment related to {skill.title()}?",
                    "talking_point": "Use the STAR method.",
                    "sample_answer": f"My biggest win with {skill.title()} was when I refactored a legacy module, reducing processing time by 40% and improving overall system reliability."
                })

            # Type 4: Curated universal bank questions (shuffled per run)
            banked = (
                random.sample(QUESTION_BANK["behavioral"],            min(5, len(QUESTION_BANK["behavioral"]))) +
                random.sample(QUESTION_BANK["professional_general"],  min(6, len(QUESTION_BANK["professional_general"]))) +
                random.sample(QUESTION_BANK["career"],                min(4, len(QUESTION_BANK["career"]))) +
                random.sample(QUESTION_BANK["soft_skills"],           min(4, len(QUESTION_BANK["soft_skills"])))
            )
            questions.extend(banked)

            return questions[:35]

        prompt = INTERVIEW_PREP_PROMPT.format(resume_text=resume_text, jd_text=jd_text)
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(response_mime_type="application/json"),
            )
            return json.loads(response.text)
        except Exception as e:
            return [{"question": "Error generating questions", "talking_point": str(e)}]