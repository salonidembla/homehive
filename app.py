
# app.py
import streamlit as st
import pandas as pd
import requests
import base64
import os
from typing import Optional
import streamlit.components.v1 as components

# --------------------------------
# Auto-scroll function
# --------------------------------
def scroll_to_results():
    components.html(
        """
        <script>
        try {
            const el = parent.document.querySelector('.results-header');
            if (el) {
                el.scrollIntoView({behavior: 'smooth', block: 'start'});
                parent.window.scrollBy(0, -40); // offset a little for better view
            } else {
                parent.window.scrollTo({top: parent.document.body.scrollHeight, behavior:'smooth'});
            }
        } catch (e) {
            window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});
        }
        </script>
        """,
        height=0,
    )

# Try to import PropertyRAG only if needed (heavy)
try:
    from rag_pipeline import PropertyRAG
except Exception:
    PropertyRAG = None

# --------------------------------
# CONFIG
# --------------------------------
st.set_page_config(page_title="HomeHive – Smart Property Search", layout="wide")

API_URL = "http://127.0.0.1:8000/query"

def is_api_online() -> bool:
    try:
        r = requests.get("http://127.0.0.1:8000/", timeout=1.5)
        return r.status_code == 200
    except Exception:
        return False

API_AVAILABLE = is_api_online()

# --------------------------------
# CSS (optimized & aligned)
# --------------------------------
st.markdown("""
<style>
header, footer { visibility: hidden !important; }
[data-testid="stAppViewContainer"] { background-color: #ffe6f2 !important; }
.block-container { padding-top: 0.5rem !important; padding-bottom: 1rem !important; }
.stExpander { margin-top: -11px !important; }

/* Logo */
.logo-row {
    display:flex; justify-content:center; align-items:center;
    width:100%; margin-top:8px; margin-bottom:4px;
}
.logo-row img {
    width:230px !important; max-width:230px !important;
    height:auto !important; display:block;
    border-radius:12px; box-shadow:0 6px 18px rgba(0,0,0,0.06);
}

/* API badge */
.api-badge {
    display:inline-block; margin:8px auto 8px auto;
    padding:4px 12px; background:#ffd6e6;
    color:#1c1c1c; border-radius:12px; font-weight:600; text-align:center;
}

/* Title */
.title-center {
    text-align:center; color:#ff3b7b; font-weight:800;
    margin-top:5px; margin-bottom:5px; font-size:1.9rem; letter-spacing:0.5px;
}

/* Search input */
.search-section {
    display:flex; flex-direction:column; align-items:center;
    gap:40px; margin-top:0rem; margin-bottom:0.7rem;
}
div[data-testid="stTextInputRootElement"] {
    width:56% !important; margin:0 auto !important; overflow:visible !important;
}
div[data-testid="stTextInputRootElement"] input {
    border-radius:30px !important; height:54px !important;
    line-height:54px !important; padding:0 1.4rem !important;
    text-align:center !important; border:1px solid #ff87b2 !important;
    background-color:#ffffff !important; box-shadow:0 2px 8px rgba(0,0,0,0.05);
    font-size:1rem !important; font-weight:400 !important; color:#333 !important;
    box-sizing:border-box !important;
}

/* Search button */
.stButton > button {
    display:block; margin:0 auto;
    padding:0.7rem 2.5rem; border-radius:28px;
    background:linear-gradient(90deg,#ff4f87,#ff79b0);
    color:white; font-weight:700; border:none;
    font-size:1.05rem; transition:all 0.15s ease-in-out;
}
.stButton { margin-top:18px !important; }
.stButton > button:hover {
    background:linear-gradient(90deg,#ff2e70,#ff6fa6);
    transform:translateY(-2px);
}

/* Results */
.results-header { color:#ff3b7b; font-weight:700; margin-top:2rem; }

/* Property card */
.property-card {
    border-radius:10px; background:#fff9fb; padding:14px;
    border:1px solid #f3c7da;
    box-shadow:0 4px 12px rgba(255,59,123,0.06);
}

/* Responsive */
@media (max-width:768px){
    div[data-testid="stTextInputRootElement"] { width:88% !important; }
    .logo-row img { width:100px !important; }
    .title-center { font-size:1.3rem; }
}
</style>
""", unsafe_allow_html=True)

# --------------------------------
# Logo helper
# --------------------------------
LOGO_CANDIDATES = ["logo.png"]
def find_logo_path() -> Optional[str]:
    for fname in LOGO_CANDIDATES:
        if os.path.isfile(fname):
            return fname
    for folder in ("assets", "static", "public"):
        for fname in LOGO_CANDIDATES:
            p = os.path.join(folder, fname)
            if os.path.isfile(p):
                return p
    return None

def get_logo_base64(path: str) -> str:
    with open(path, "rb") as f:
        raw = f.read()
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    mime = "png" if ext not in ("svg", "webp", "jpg", "jpeg") else ext
    return f"data:image/{mime};base64,{base64.b64encode(raw).decode()}"

logo_path = find_logo_path()
logo_b64 = get_logo_base64(logo_path) if logo_path else None

# --------------------------------
# Init session vars
# --------------------------------
if "rag" not in st.session_state:
    st.session_state["rag"] = None
if "last_results" not in st.session_state:
    st.session_state["last_results"] = pd.DataFrame()
if "last_full_results" not in st.session_state:
    st.session_state["last_full_results"] = None
if "last_query" not in st.session_state:
    st.session_state["last_query"] = ""

# instantiate RAG
if not API_AVAILABLE and st.session_state["rag"] is None:
    if PropertyRAG is None:
        st.warning("Local RAG pipeline not available.")
    else:
        try:
            st.session_state["rag"] = PropertyRAG()
        except Exception as e:
            st.error(f"Error initializing local RAG: {e}")
            st.session_state["rag"] = None

# --------------------------------
# HEADER
# --------------------------------
if logo_b64:
    st.markdown(f"<div class='logo-row'><img src='{logo_b64}' alt='HomeHive logo' /></div>", unsafe_allow_html=True)
else:
    st.markdown("<div style='text-align:center; margin-top:6px;'><strong style='font-size:22px; color:#ff3b7b;'>HomeHive</strong></div>", unsafe_allow_html=True)

badge_text = "🟢 API Connected" if API_AVAILABLE else "🔴 Offline Mode"
st.markdown(f"<div style='text-align:center;'><span class='api-badge'>{badge_text}</span></div>", unsafe_allow_html=True)
st.markdown("<div class='title-center'>Let's find your dream home 🐝</div>", unsafe_allow_html=True)

# --------------------------------
# SEARCH UI
# --------------------------------
st.markdown("<div class='search-section'>", unsafe_allow_html=True)
query = st.text_input(
    "Enter your property query:",
    placeholder="e.g. Find properties in Southampton",
    value=st.session_state.get("last_query", ""),
    label_visibility="collapsed"
)
search_button = st.button("Search", key="search_btn")
st.markdown("</div>", unsafe_allow_html=True)

with st.expander("💡 Example Queries"):
    st.markdown("""
- Show me houses with 2 bedrooms   
- Find properties in Southampton  
- What is the average price of 3-bedroom homes?  
- Which area has the most crime?  
- Compare prices between studio and 2 bed homes  
""")

# --------------------------------
# Helper to normalize RAG response
# --------------------------------
def normalize_rag_response(res):
    if res is None:
        return "No response", pd.DataFrame(), None
    if isinstance(res, (tuple, list)):
        if len(res) == 2:
            narrative, df = res
            return narrative or "", pd.DataFrame(df), None
        elif len(res) == 3:
            narrative, preview, full = res
            return narrative or "", pd.DataFrame(preview), pd.DataFrame(full)
    if isinstance(res, dict):
        narrative = res.get("narrative") or res.get("response") or ""
        rows = res.get("results") or res.get("structured_results") or res.get("rows") or []
        df = pd.DataFrame(rows)
        return narrative, df, df
    return str(res), pd.DataFrame(), None

# --------------------------------
# PROCESS QUERY
# --------------------------------
if search_button and query.strip():
    st.session_state["last_query"] = query
    try:
        if API_AVAILABLE:
            with st.spinner("Fetching from HomeHive API..."):
                resp = requests.post(API_URL, json={"query": query}, timeout=20)
                data = resp.json()
                narrative = data.get("response") or data.get("narrative") or ""
                results = data.get("results") or data.get("rows") or []
                preview_df = pd.DataFrame(results)
                full_df = preview_df.copy()
        else:
            if st.session_state["rag"] is None:
                st.error("Local RAG not initialized.")
                preview_df, full_df, narrative = pd.DataFrame(), pd.DataFrame(), "Local RAG unavailable."
            else:
                with st.spinner("Running locally..."):
                    raw = st.session_state["rag"].process_query(query)
                    narrative, preview_df, full_df = normalize_rag_response(raw)
                    if full_df is None:
                        full_df = preview_df.copy()

        if not preview_df.empty:
            st.session_state["last_results"] = preview_df
            st.session_state["last_full_results"] = full_df
            st.session_state["response_text"] = narrative
        else:
            st.session_state["last_results"] = pd.DataFrame()
            st.session_state["last_full_results"] = pd.DataFrame()
            st.session_state["response_text"] = "⚠️ No matching results found."
    except Exception as e:
        st.error(f"❌ Error during query: {e}")
        st.session_state["last_results"] = pd.DataFrame()
        st.session_state["last_full_results"] = pd.DataFrame()
        st.session_state["response_text"] = f"Error: {e}"

# --------------------------------
# DISPLAY RESULTS
# --------------------------------
df = st.session_state.get("last_results", pd.DataFrame())
full_df = st.session_state.get("last_full_results", pd.DataFrame())
response_text = st.session_state.get("response_text", "")

if not df.empty:
    st.markdown("<h3 class='results-header'>Search Results</h3>", unsafe_allow_html=True)
    scroll_to_results()  # ✅ moved here — after rendering header
    st.info(response_text)
    st.success(f"Found {len(full_df) if isinstance(full_df, pd.DataFrame) else len(df)} matching properties")

    view_mode = st.radio("View Mode:", ["🗂️ Cards", "📋 Table"], horizontal=True, key="view_mode")
    if view_mode == "🗂️ Cards":
        cols = st.columns(2)
        for i, (_, row) in enumerate(df.head(10).iterrows()):
            col = cols[i % 2]
            with col:
                st.markdown(f"""
                <div class="property-card">
                    <h5 style="color:#ff3b7b;margin-bottom:6px;">{row.get('address','Unknown')}</h5>
                    <div><b> Price:</b> {row.get('price','N/A')}</div>
                    <div><b>Bedrooms:</b>{row.get('bedrooms','N/A')}</b> | <b>Bathrooms:</b>{row.get( 'bathrooms','N/A')}</b></div>
                    <div><b>Type:</b> {row.get('property_type_full_description','N/A')}</div>
                    <div><b>Flood:</b> {row.get('flood_risk','N/A')} | <b>Crime:</b> {row.get('crime_score_weight','N/A')}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.dataframe(df.head(10), use_container_width=True, hide_index=True)

    st.markdown("### Download Results")
    col1, col2 = st.columns(2)
    top_csv = df.head(10).to_csv(index=False)
    all_csv = (full_df.to_csv(index=False)
               if (isinstance(full_df, pd.DataFrame) and not full_df.empty)
               else df.to_csv(index=False))
    with col1:
        st.download_button("Download Top 10 Results", data=top_csv,
                           file_name="homehive_top10.csv", mime="text/csv", key="dl_top10")
    with col2:
        st.download_button("Download All Results", data=all_csv,
                           file_name="homehive_all.csv", mime="text/csv", key="dl_all")
elif response_text:
    st.warning(response_text)
