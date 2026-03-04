import streamlit as st
from streamlit_echarts import st_echarts
import time
import random
from streamlit_mic_recorder import mic_recorder

from models.gemini_analyzer import GeminiAnalyzer
from utils.text_extractor import extract_text_from_pdf
from utils.dataset_loader import load_dataset_index, is_dataset_loaded, get_global_skill_freq
from utils.history_db import init_db, save_analysis, get_history, delete_history_item, clear_all_history
from utils.scraper import scrape_job_description
from utils.pdf_generator import generate_pdf_report
from utils.voice_evaluator import evaluate_audio_answer

# Initialize Database
init_db()

# Pre-load dataset index at startup (cached)
if "dataset_loaded" not in st.session_state:
    with st.spinner("📊 Loading resume dataset index..."):
        load_dataset_index()
    st.session_state.dataset_loaded = is_dataset_loaded()

# ───────────────────────────────────────────────
# Page Config
# ───────────────────────────────────────────────
st.set_page_config(
    page_title="Resume Intelligence AI",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "analyzer" not in st.session_state:
    st.session_state.analyzer = GeminiAnalyzer()

# ───────────────────────────────────────────────
# CSS
# ───────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');

:root {
    --primary: #00F2FE;
    --secondary: #4FACFE;
    --accent: #92FE9D;
    --warn:  #FFB347;
    --danger:#FF6B6B;
    --bg: #09090B;
    --card: rgba(255,255,255,0.03);
    --border: rgba(255,255,255,0.07);
}

html, body, [class*="css"] { font-family: 'Outfit', sans-serif; background: var(--bg); color: #DDD; }
.stApp { background: radial-gradient(circle at 15% 10%, rgba(0,242,254,.06) 0%, transparent 45%),
                      radial-gradient(circle at 85% 90%, rgba(146,254,157,.05) 0%, transparent 45%); }

/* Cards */
.card { background: var(--card); backdrop-filter: blur(14px); border: 1px solid var(--border);
        border-radius: 22px; padding: 2rem; margin-bottom: 1.5rem; transition: .3s ease; }
.card:hover { border-color: rgba(0,242,254,.15); transform: translateY(-3px);
              box-shadow: 0 12px 40px rgba(0,242,254,.07); }

/* Hero */
.hero { font-size: 3.8rem; font-weight: 800;
        background: linear-gradient(135deg, var(--primary), var(--accent));
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-align: center; letter-spacing: -2px; line-height: 1.1; margin-bottom: .3rem; }
.hero-sub { text-align: center; color: #666; font-size: 1.2rem; font-weight: 300;
            letter-spacing: .8px; margin-bottom: 3rem; }

/* Buttons */
.stButton>button { width: 100%; border-radius: 14px;
    background: linear-gradient(90deg, var(--primary) 0%, var(--secondary) 100%);
    color: #000 !important; font-weight: 800; font-size: 1rem; height: 3.5rem; border: none;
    box-shadow: 0 4px 20px rgba(0,242,254,.2); transition: .35s; }
.stButton>button:hover { filter: brightness(1.12); transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(0,242,254,.35); }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 16px; background: transparent; }
.stTabs [data-baseweb="tab"] { background: rgba(255,255,255,.02); border-radius: 10px;
    color: #777; border: 1px solid transparent; font-weight: 600; transition: .25s; }
.stTabs [aria-selected="true"] { background: rgba(0,242,254,.08) !important;
    color: var(--primary) !important; border-color: rgba(0,242,254,.25) !important; }

/* Score pill */
.score-pill { display: inline-block; padding: .3rem 1.2rem; border-radius: 999px;
    font-weight: 700; font-size: 1rem; margin: .2rem; }
.pill-matched { background: rgba(146,254,157,.12); color: var(--accent); border: 1px solid rgba(146,254,157,.25); }
.pill-missing { background: rgba(255,107,107,.10); color: var(--danger); border: 1px solid rgba(255,107,107,.25); }

/* Metric row */
.metric-row { display: flex; justify-content: space-around; flex-wrap: wrap;
    background: rgba(255,255,255,.02); border-radius: 18px; padding: 1.2rem; margin-bottom: 1.5rem; }
.metric-item { text-align: center; padding: .5rem 1rem; }
.metric-val { font-size: 2.2rem; font-weight: 800; color: var(--primary); }
.metric-lbl { font-size: .75rem; color: #555; text-transform: uppercase; letter-spacing: 1px; }

/* Sidebar badge */
@keyframes pulse { 0%,100% { opacity:.7; } 50% { opacity:1; } }
.dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%;
    margin-right: 7px; animation: pulse 2s infinite; }

/* Question card */
.q-card { background: rgba(255,255,255,.02); padding: 1.3rem 1.5rem; border-radius: 14px;
    border-left: 4px solid var(--primary); margin-bottom: .9rem; }
.q-num { color: #555; font-size: .75rem; text-transform: uppercase; letter-spacing: 1px; }
.q-text { font-size: 1.05rem; font-weight: 600; margin: .4rem 0; }
.q-tip { color: var(--accent); font-size: .88rem; }
</style>
""", unsafe_allow_html=True)

# ───────────────────────────────────────────────
# Sidebar
# ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:20px 0 10px">
        <div style="font-size:3rem">🔮</div>
        <h3 style="background:linear-gradient(135deg,#00F2FE,#4FACFE);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:8px 0 0">
            INTELLIGENCE CORE</h3>
    </div>""", unsafe_allow_html=True)

    app_mode = st.radio("NAVIGATE", ["⚡ Analysis Engine", "🏆 Bulk Ranker", "✉️ Cover Letter", "🎙️ Interview Lab", "📜 Analysis History"], index=0)
    st.divider()

    if st.session_state.analyzer.mock_mode:
        st.markdown('<p style="color:#FFA500"><span class="dot" style="background:#FFA500"></span>MOCK ENGINE</p>', unsafe_allow_html=True)
        st.caption("No API key — using local NLP scoring.")
    else:
        st.markdown('<p style="color:#4CFF91"><span class="dot" style="background:#4CFF91"></span>LIVE AI ENGINE</p>', unsafe_allow_html=True)
        st.caption("Engine: Gemini 1.5 Flash")

    # Dataset status badge
    st.divider()
    if st.session_state.get("dataset_loaded"):
        idx = load_dataset_index()
        n_skills = len(idx["all_known_skills"])
        n_fields = len(idx["field_skills"])
        n_pos    = len(idx["position_skills"])
        st.markdown(f'''
        <div style="background:rgba(0,242,254,.07);border:1px solid rgba(0,242,254,.2);border-radius:14px;padding:14px;text-align:center">
            <div style="font-size:1.6rem">📊</div>
            <div style="color:#00F2FE;font-weight:700;font-size:.95rem">DATASET ACTIVE</div>
            <div style="color:#555;font-size:.75rem;margin-top:4px">{n_skills:,} skills · {n_fields} fields · {n_pos} roles</div>
        </div>''', unsafe_allow_html=True)
    else:
        st.markdown('<div style="color:#444;font-size:.8rem;text-align:center">📁 No dataset loaded<br>Upload resume_data.csv to activate</div>', unsafe_allow_html=True)

    st.divider()
    if st.button("🗑️ Clear Session"):
        st.session_state.clear(); st.rerun()

# ───────────────────────────────────────────────
# Hero
# ───────────────────────────────────────────────
st.markdown('<h1 class="hero">RESUME INTELLIGENCE</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-sub">Multi-Dimensional ATS Scoring · Career Optimization · Interview Intelligence</p>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════
# TAB: Analysis Engine
# ═══════════════════════════════════════════════
if "⚡ Analysis Engine" in app_mode:
    left, right = st.columns([1, 1.3], gap="large")

    with left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📄 Input Data")
        uploaded_file = st.file_uploader("Resume (PDF)", type=["pdf"])
        
        st.divider()
        st.markdown("**Job Description Sources**")
        jd_source = st.tabs(["✍️ Paste Text", "🌐 Scrape URL"])
        
        with jd_source[0]:
            jd_text_input = st.text_area("Job Description Content", height=280,
                placeholder="Paste the full job description here...", key="jd_area")
        
        with jd_source[1]:
            jd_url = st.text_input("Job URL (LinkedIn, Indeed, etc.)")
            if st.button("🕸️ SCRAPE JD"):
                if jd_url:
                    with st.spinner("Scraping..."):
                        scraped = scrape_job_description(jd_url)
                        if scraped.startswith("Error"):
                            st.error(scraped)
                        else:
                            st.session_state.scraped_jd = scraped
                            st.success("Scraped successfully! See 'Paste Text' tab for content.")
                else:
                    st.warning("Please enter a URL.")
        
        # Sync scraped text back to area if present
        jd_text = st.session_state.get("scraped_jd", jd_text_input)
        
        analyze_btn = st.button("⚡ RUN FULL ANALYSIS")
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        if analyze_btn:
            if not uploaded_file or not jd_text.strip():
                st.warning("⚠️ Please provide both a resume and job description.")
            else:
                with st.spinner("🧬 Running multi-dimensional analysis..."):
                    resume_bytes = uploaded_file.read()
                    resume_text, err = extract_text_from_pdf(resume_bytes)
                    if err:
                        st.error(f"PDF Error: {err}")
                    else:
                        time.sleep(1)
                        result = st.session_state.analyzer.analyze_resume(resume_text, jd_text)
                        st.session_state["last_result"] = result
                        st.session_state["last_jd"] = jd_text
                        
                        # Save to history DB
                        save_analysis(uploaded_file.name, jd_text, result.get("match_score", 0), result.get("tier", "N/A"), result)

        if "last_result" in st.session_state:
            result = st.session_state["last_result"]

            if "error" in result:
                st.error(result["error"])
            else:
                score    = result.get("match_score", 0)
                breakdown= result.get("score_breakdown", {})
                matched  = result.get("matched_skills", [])
                missing  = result.get("missing_skills", [])
                tier     = result.get("tier", "")
                suggestions = result.get("improvement_suggestions", [])

                # ── Score Gauge ──
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown(f"<div style='text-align:center;font-size:1.1rem;color:#888;margin-bottom:8px'>{tier}</div>", unsafe_allow_html=True)

                gauge_opts = {
                    "series": [{
                        "type": "gauge",
                        "startAngle": 200, "endAngle": -20,
                        "min": 0, "max": 100,
                        "splitNumber": 5,
                        "itemStyle": {"color": "#00F2FE"},
                        "progress": {"show": True, "width": 22},
                        "pointer": {"show": False},
                        "axisLine": {"lineStyle": {"width": 22, "color": [[1, "#1A2A2A"]]}},
                        "axisTick": {"show": False},
                        "splitLine": {"show": False},
                        "axisLabel": {"show": False},
                        "title": {"show": True, "offsetCenter": [0, "20%"],
                                  "fontSize": 14, "color": "#888"},
                        "detail": {
                            "valueAnimation": True,
                            "offsetCenter": [0, "-10%"],
                            "formatter": "{value}%",
                            "fontSize": 52,
                            "fontWeight": 800,
                            "color": "#00F2FE",
                        },
                        "data": [{"value": score, "name": "Match Score"}]
                    }]
                }
                st_echarts(gauge_opts, height="280px")
                
                # Download PDF Button
                pdf_bytes = generate_pdf_report(result, "Your Resume")
                st.download_button(
                    label="⬇️ DOWNLOAD PROFESSIONAL REPORT (PDF)",
                    data=pdf_bytes,
                    file_name=f"Resume_Report_{tier.replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )
                
                st.markdown('</div>', unsafe_allow_html=True)

                # ── Metric Row ──
                st.markdown(f"""
                <div class="metric-row">
                    <div class="metric-item">
                        <div class="metric-val">{len(matched)}</div>
                        <div class="metric-lbl">Skills Matched</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-val">{len(missing)}</div>
                        <div class="metric-lbl">Skill Gaps</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-val">{score}%</div>
                        <div class="metric-lbl">Overall Score</div>
                    </div>
                </div>""", unsafe_allow_html=True)
                
                # ── AI Branding Feature ──
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("#### 🎨 Neural Profile Branding")
                st.caption("Generate a professional visual identity based on your top skills.")
                if st.button("✨ GENERATE BRANDING PREVIEW"):
                    with st.spinner("AI is crafting your visual identity..."):
                        time.sleep(2)
                        st.success("Visual identity concept generated!")
                        # Display a symbolic "Neural Brand" icon/visual
                        st.markdown(f"""
                        <div style="background:linear-gradient(45deg, var(--primary), var(--accent)); height:120px; border-radius:15px; display:flex; align-items:center; justify-content:center; color:#000; font-weight:800; font-size:1.5rem; text-align:center; padding:20px;">
                            THE {', '.join(matched[:2]).upper()} EXPERT
                        </div>
                        """, unsafe_allow_html=True)
                        st.info("Concept: Cyber-Professional aesthetic with a focus on your expertise in " + ", ".join(matched[:3]))
                st.markdown('</div>', unsafe_allow_html=True)

                # ── Score Breakdown ──
                if breakdown:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.markdown("#### 📊 Score Breakdown")
                    dims  = list(breakdown.keys())
                    vals  = list(breakdown.values())
                    bar_opts = {
                        "tooltip": {"trigger": "axis"},
                        "grid": {"left": "3%", "right": "4%", "containLabel": True},
                        "xAxis": {"type": "value", "max": 100,
                                  "axisLabel": {"color": "#555"},
                                  "splitLine": {"lineStyle": {"color": "rgba(255,255,255,0.04)"}}},
                        "yAxis": {"type": "category", "data": dims,
                                  "axisLabel": {"color": "#999", "fontSize": 12}},
                        "series": [{
                            "type": "bar", "data": vals, "barMaxWidth": 28,
                            "itemStyle": {
                                "borderRadius": [0, 8, 8, 0],
                                "color": {
                                    "type": "linear", "x": 0, "y": 0, "x2": 1, "y2": 0,
                                    "colorStops": [
                                        {"offset": 0, "color": "#4FACFE"},
                                        {"offset": 1, "color": "#00F2FE"}
                                    ]
                                }
                            },
                            "label": {"show": True, "position": "right",
                                      "formatter": "{c}%", "color": "#888"},
                        }]
                    }
                    st_echarts(bar_opts, height=f"{max(240, len(dims)*52)}px")
                    st.markdown('</div>', unsafe_allow_html=True)

                # ── Tabs ──
                st.markdown('<div class="card">', unsafe_allow_html=True)
                tab1, tab2, tab3 = st.tabs(["💡 Insights", "🧬 Skill Map", "✍️ AI Rewrite"])

                with tab1:
                    # Dataset-powered badge
                    if result.get("dataset_powered"):
                        st.markdown('<div style="display:inline-block;background:rgba(0,242,254,.12);color:#00F2FE;border:1px solid rgba(0,242,254,.3);border-radius:999px;padding:.2rem 1rem;font-size:.75rem;font-weight:700;margin-bottom:12px">📊 DATASET-POWERED · 50k+ Real Resumes</div>', unsafe_allow_html=True)

                    st.info(result.get("human_explanation", ""))
                    st.markdown("#### 🔸 Action Items")
                    for sug in suggestions:
                        st.markdown(f"- {sug}")

                    # Show missing skills with market popularity from dataset
                    if missing and st.session_state.get("dataset_loaded"):
                        freq = get_global_skill_freq()
                        total = sum(freq.values()) or 1
                        st.markdown("#### 📈 Priority Skills to Add")
                        st.caption("Ranked by market demand in 50k+ real resumes — add the most popular gaps first.")
                        for i, sk in enumerate(missing[:6]):
                            pop = freq.get(sk, 0)
                            pct = round((pop / total) * 100 * 1000, 2)  # per-mille then %
                            bar_w = min(100, int(pop / (max(freq.values()) or 1) * 100))
                            st.markdown(f"""
                            <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
                                <span style="color:#FF6B6B;font-weight:700;min-width:18px">{i+1}.</span>
                                <span style="color:#DDD;min-width:120px">{sk}</span>
                                <div style="flex:1;background:#1a1a1a;border-radius:4px;height:6px">
                                    <div style="background:linear-gradient(90deg,#FF6B6B,#FF9B44);width:{bar_w}%;height:6px;border-radius:4px"></div>
                                </div>
                                <span style="color:#555;font-size:.75rem;min-width:70px">{pop:,} resumes</span>
                            </div>""", unsafe_allow_html=True)

                with tab2:
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("**✅ Matched Skills**")
                        if matched:
                            freq = get_global_skill_freq() if st.session_state.get("dataset_loaded") else {}
                            for sk in matched:
                                pop = freq.get(sk, 0)
                                pop_str = f" · {pop:,} resumes" if pop else ""
                                st.markdown(f'<span class="score-pill pill-matched">{sk}{pop_str}</span>', unsafe_allow_html=True)
                        else:
                            st.markdown("<em>None detected</em>", unsafe_allow_html=True)
                    with c2:
                        st.markdown("**❌ Missing Skills** *(Add these!)*")
                        if missing:
                            pills = " ".join([f'<span class="score-pill pill-missing">{s}</span>' for s in missing])
                            st.markdown(pills, unsafe_allow_html=True)
                        else:
                            st.markdown("<em style='color:#4CFF91'>No major gaps! ✅</em>", unsafe_allow_html=True)

                with tab3:
                    for item in result.get("rewritten_bullets", []):
                        st.markdown(f"**Original:** `{item['original']}`")
                        st.code(item['rewritten'], language="text")

                st.markdown('</div>', unsafe_allow_html=True)
        else:
            # Default state placeholder
            st.markdown('<div class="card" style="text-align:center;padding:3rem">', unsafe_allow_html=True)
            ds_note = ""
            if st.session_state.get("dataset_loaded"):
                idx = load_dataset_index()
                ds_note = f"<p style='color:#00F2FE;font-size:.9rem'>📊 Powered by <strong>{len(idx['all_known_skills']):,} skills</strong> from {sum(get_global_skill_freq().values()):,} real resume entries</p>"
            st.markdown(f"""
            <div style="font-size:4rem;margin-bottom:1rem">🔮</div>
            <h3>Upload your resume and paste a job description<br>to begin your Neural Analysis</h3>
            {ds_note}
            <p style="color:#444;margin-top:.8rem">
            Scores across 5 dimensions:<br>
            <strong style='color:#00F2FE'>Skills Match · Domain Keywords · Experience Level · Soft Skills · Education</strong>
            </p>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════
# TAB: Bulk Ranker
# ═══════════════════════════════════════════════
elif "🏆 Bulk Ranker" in app_mode:
    st.markdown('<h1 class="hero">BULK RANKER</h1>', unsafe_allow_html=True)
    st.markdown('<p class="hero-sub">Rank multiple candidates against a single job description.</p>', unsafe_allow_html=True)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    col_a, col_b = st.columns([1, 1.3])
    with col_a:
        bulk_files = st.file_uploader("Upload Multiple Resumes", type=["pdf"], accept_multiple_files=True)
    with col_b:
        bulk_jd = st.text_area("Target Job Description", height=200, placeholder="Paste the JD to rank against...")
    
    rank_btn = st.button("🏆 RANK ALL CANDIDATES")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if rank_btn:
        if not bulk_files or not bulk_jd.strip():
            st.warning("Please provide resumes and a JD.")
        else:
            rankings = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, f in enumerate(bulk_files):
                status_text.text(f"Processing ({i+1}/{len(bulk_files)}): {f.name}")
                text, err = extract_text_from_pdf(f.read())
                if not err:
                    res = st.session_state.analyzer.analyze_resume(text, bulk_jd)
                    rankings.append({
                        "name": f.name,
                        "score": res["match_score"],
                        "tier": res["tier"],
                        "result": res
                    })
                progress_bar.progress((i + 1) / len(bulk_files))
            
            # Sort by score
            rankings = sorted(rankings, key=lambda x: x['score'], reverse=True)
            
            st.success(f"Ranked {len(rankings)} candidates!")
            
            # Display Leaderboard
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("🏆 Candidate Leaderboard")
            
            for i, r in enumerate(rankings):
                color = "#4CFF91" if r['score'] >= 80 else ("#FFA500" if r['score'] >= 60 else "#FF6B6B")
                st.markdown(f"""
                <div style="background:rgba(255,255,255,0.02); padding:1rem; border-radius:12px; border-left:5px solid {color}; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;">
                    <div style="display:flex; align-items:center; gap:20px;">
                        <span style="font-size:1.5rem; font-weight:800; color:#555;">#{i+1}</span>
                        <div>
                            <strong style="font-size:1.1rem; color:#FFF;">{r['name']}</strong><br>
                            <span style="font-size:0.75rem; color:#888;">{r['tier']}</span>
                        </div>
                    </div>
                    <div style="text-align:right;">
                        <span style="font-size:1.8rem; font-weight:800; color:{color};">{r['score']}%</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"View Report: {r['name']}", key=f"bulk_view_{i}"):
                    st.session_state["last_result"] = r['result']
                    st.session_state["last_jd"] = bulk_jd
                    st.info(f"Report for {r['name']} loaded! Switch to '⚡ Analysis Engine' to view details.")
            st.markdown('</div>', unsafe_allow_html=True)
elif "✉️ Cover Letter" in app_mode:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("✉️ AI Cover Letter Generator")
    c1, c2 = st.columns(2)
    with c1: cv_file = st.file_uploader("Resume PDF", type=["pdf"])
    with c2: cv_jd   = st.text_area("Job Description", height=200)

    if st.button("✨ GENERATE TAILORED LETTER"):
        if cv_file and cv_jd:
            with st.spinner("Crafting your personalized cover letter..."):
                txt, _ = extract_text_from_pdf(cv_file.read())
                letter = st.session_state.analyzer.generate_cover_letter(txt, cv_jd)
            st.divider()
            st.text_area("📄 Your Cover Letter", letter, height=420)
            st.download_button("⬇️ Download .txt", letter, file_name="cover_letter.txt")
        else:
            st.warning("Please provide both a resume and job description.")
    st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════
# TAB: Interview Lab
# ═══════════════════════════════════════════════
elif "🎙️ Interview Lab" in app_mode:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🎙️ Personalized Interview Preparation")
    i1, i2 = st.columns(2)
    with i1: int_resume = st.file_uploader("Your Resume", type=["pdf"])
    with i2: int_jd     = st.text_area("Job Description", height=200)

    if st.button("🚀 GENERATE INTERVIEW QUESTIONS"):
        if int_resume and int_jd:
            with st.spinner("Building personalized question set from your CV & JD..."):
                txt, _ = extract_text_from_pdf(int_resume.read())
                st.session_state["interview_qs"] = st.session_state.analyzer.generate_interview_prep(txt, int_jd)
        else:
            st.warning("Please provide both a resume and job description.")
    st.markdown('</div>', unsafe_allow_html=True)

    if "interview_qs" in st.session_state:
        qs = st.session_state["interview_qs"]
        search = st.text_input("🔍 Search questions", placeholder="e.g. leadership, python, conflict...")
        if search:
            qs = [q for q in qs if search.lower() in q["question"].lower() or search.lower() in q["talking_point"].lower()]

        st.markdown(f"<p style='color:#555'>Showing <strong>{len(qs)}</strong> personalized questions</p>", unsafe_allow_html=True)

        for i, q in enumerate(qs):
                st.markdown(f"""
            <div class="q-card">
                <div class="q-num">QUESTION {i+1}</div>
                <div class="q-text">{q['question']}</div>
                <div class="q-tip">💡 {q['talking_point']}</div>
            </div>""", unsafe_allow_html=True)
                
                if 'sample_answer' in q:
                    with st.expander(f"✨ VIEW SUGGESTED IDEAL ANSWER (Question {i+1})"):
                        st.markdown(f"**AI Suggested Answer:**\n\n{q['sample_answer']}")
                
                # Voice Simulation for each question
                with st.expander(f"🎙️ Practice Answer (Question {i+1})"):
                    mode = st.radio("Input Method", ["Live Record", "Upload File"], key=f"mode_{i}")
                    
                    audio_bytes = None
                    audio_format = "wav"
                    
                    if mode == "Live Record":
                        st.write("Click to start recording your answer:")
                        audio_record = mic_recorder(
                            start_prompt="🎙️ Start Recording",
                            stop_prompt="⏹️ Stop Recording",
                            just_once=True,
                            key=f"recorder_{i}"
                        )
                        if audio_record:
                            audio_bytes = audio_record['bytes']
                            audio_format = "wav"
                            st.audio(audio_bytes, format="audio/wav")
                    else:
                        audio_file = st.file_uploader(f"Upload your recorded answer (WAV/MP3)", type=["wav", "mp3"], key=f"audio_{i}")
                        if audio_file:
                            audio_bytes = audio_file.read()
                            audio_format = audio_file.name.split('.')[-1]

                    if audio_bytes:
                        if st.button(f"🧠 Evaluate Answer {i+1}", key=f"eval_btn_{i}"):
                            with st.spinner("Analyzing Speech..."):
                                eval_res = evaluate_audio_answer(audio_bytes, audio_format)
                                if eval_res["success"]:
                                    st.markdown(f"**Transcription:** *\"{eval_res['transcription']}\"*")
                                    
                                    m = eval_res["metrics"]
                                    c1, c2, c3 = st.columns(3)
                                    c1.metric("Words", m["Word Count"])
                                    c2.metric("Pacing", m["Speech Rate"])
                                    c3.metric("Clarity", f"{m['Clarity Score']}%")
                                    
                                    st.info(f"**AI FEEDBACK:** {eval_res['feedback']}")
                                else:
                                    st.error(eval_res["error"])


# ═══════════════════════════════════════════════
# TAB: Analysis History
# ═══════════════════════════════════════════════
elif "📜 Analysis History" in app_mode:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📜 Analysis History")
    
    history = get_history()
    
    if not history:
        st.info("No analysis history found. Start analyzing resumes to track your progress!")
    else:
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("🗑️ Clear All"):
                if clear_all_history():
                    st.success("History cleared!")
                    st.rerun()
        
        for item in history:
            with st.container():
                # Custom CSS for history item
                st.markdown(f"""
                <div style="background:rgba(255,255,255,0.02); border-left: 4px solid var(--primary); padding:1rem; border-radius:8px; margin-bottom:12px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div style="flex:1;">
                            <h5 style="margin:0; color:#FFF;">{item['filename']}</h5>
                            <p style="margin:2px 0; font-size:0.8rem; color:#666;">{item['timestamp']} · JD: {item['jd_preview']}</p>
                        </div>
                        <div style="text-align:right; margin-left:15px;">
                            <span style="font-size:1.4rem; font-weight:800; color:var(--primary);">{item['match_score']}%</span>
                            <div style="font-size:0.6rem; color:#555; text-transform:uppercase;">{item['tier']}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                c1, c2, _ = st.columns([1, 1, 4])
                with c1:
                    if st.button(f"👁️ Load Result", key=f"view_{item['id']}"):
                        st.session_state["last_result"] = item['result']
                        st.session_state["last_jd"] = "JD loaded from history" # Metadata
                        st.success("Result loaded! Switch to '⚡ Analysis Engine' to view details.")
                with c2:
                    if st.button(f"🗑️ Delete", key=f"del_{item['id']}"):
                        if delete_history_item(item['id']):
                            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center;margin-top:80px;padding:30px;color:#333;border-top:1px solid rgba(255,255,255,0.04)">
    <p>Resume Intelligence AI v3.0 · Powered by Multi-Dimensional NLP Scoring</p>
</div>
""", unsafe_allow_html=True)