import streamlit as st
import google.generativeai as genai
import fitz

# ── SECRETS MANAGEMENT ────────────────────────────────────────
# Fixed: Switched from os.environ to st.secrets for Streamlit Cloud deployment
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Missing GEMINI_API_KEY in Streamlit Secrets!")

model = genai.GenerativeModel("gemini-2.5-flash")  # free tier model

st.set_page_config(page_title="ResearchLens", page_icon="🔬", layout="wide")
st.title("🔬 ResearchLens")
st.caption("Upload research papers → Gemini summarizes, compares & finds research gaps")

def extract_pdf_text(uploaded_file):
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text[:6000]

def analyze_papers(papers):
    paper_list = "\n\n".join([f"--- PAPER {i+1} ---\n{p}" for i, p in enumerate(papers)])
    prompt = f"""You are a research analyst helping engineering students.
Analyze the following {len(papers)} research papers:

{paper_list}

Provide your response in these exact sections:

SUMMARIES:
Write a 3-4 sentence summary for each paper covering objective, method, findings.

COMPARISON:
2-3 sentences on how the papers relate, agree, or differ.

RESEARCH GAPS:
List 5 specific research gaps not addressed by these papers. Number each one.

THESIS TOPICS:
Suggest 3 concrete project or thesis titles a student could pursue.
"""
    response = model.generate_content(prompt)
    return response.text

# ── Upload PDFs ──────────────────────────────────────────────
st.subheader("📄 Upload Your Papers")
uploaded_files = st.file_uploader(
    "Upload 2–6 research papers (PDF)",
    type=["pdf"],
    accept_multiple_files=True
)

# ── Or paste manually ────────────────────────────────────────
st.subheader("✏️ Or Paste Abstracts Manually")
col1, col2 = st.columns(2)
with col1:
    manual1 = st.text_area("Paper 1 Abstract", height=150)
with col2:
    manual2 = st.text_area("Paper 2 Abstract", height=150)

# ── Analyze ──────────────────────────────────────────────────
if st.button("🚀 Analyze Papers", type="primary"):
    papers = []
    for f in uploaded_files:
        papers.append(f"[From: {f.name}]\n{extract_pdf_text(f)}")
    for text in [manual1, manual2]:
        if text.strip():
            papers.append(text.strip())

    if len(papers) < 2:
        st.error("Please provide at least 2 papers.")
    else:
        with st.spinner(f"Gemini is analyzing {len(papers)} papers..."):
            try:
                result = analyze_papers(papers)
                st.success("Analysis complete!")

                # Parse sections
                sections = {"summaries": "", "comparison": "", "gaps": "", "thesis": ""}
                current = None
                for line in result.split("\n"):
                    l = line.lower()
                    if "summaries" in l:       current = "summaries"
                    elif "comparison" in l:    current = "comparison"
                    elif "research gap" in l:  current = "gaps"
                    elif "thesis" in l:        current = "thesis"
                    elif current:              sections[current] += line + "\n"

                tab1, tab2, tab3, tab4 = st.tabs([
                    "📋 Summaries", "🔄 Comparison", "🔍 Research Gaps", "💡 Thesis Topics"
                ])
                with tab1: st.markdown(sections["summaries"] or result[:600])
                with tab2: st.markdown(sections["comparison"])
                with tab3: st.markdown(sections["gaps"])
                with tab4: st.markdown(sections["thesis"])

                st.download_button(
                    "⬇ Download Full Analysis",
                    data=result,
                    file_name="research_analysis.txt",
                    mime="text/plain"
                )
            except Exception as e:
                st.error(f"An error occurred during analysis: {e}")
