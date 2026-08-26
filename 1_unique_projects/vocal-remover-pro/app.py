"""
VocalRemover Pro - Main Streamlit Application
Run with: streamlit run app.py
"""
import streamlit as st

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="VocalRemover Pro",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS Design System ──────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

  /* App background */
  .stApp { background: #0e0e16; }

  /* Sidebar */
  section[data-testid="stSidebar"] { background: #13131f; border-right: 1px solid #1f1f2e; }

  /* Tabs */
  .stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: #13131f;
    border-radius: 12px;
    padding: 6px;
  }
  .stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 8px 20px;
    font-weight: 600;
    color: #888;
    background: transparent;
  }
  .stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #ff4b4b, #ff8f00) !important;
    color: #fff !important;
  }

  /* Buttons */
  .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #ff4b4b, #ff8f00);
    border: none;
    border-radius: 10px;
    font-weight: 700;
    letter-spacing: 0.3px;
    transition: opacity .2s;
  }
  .stButton > button[kind="primary"]:hover { opacity: 0.88; }

  .stButton > button[kind="secondary"] {
    background: #1f1f2e;
    border: 1px solid #2d2d3f;
    border-radius: 10px;
    color: #ccc;
  }

  /* Cards / expanders */
  div[data-testid="stExpander"] {
    background: #13131f;
    border: 1px solid #1f1f2e;
    border-radius: 12px;
    margin-bottom: 8px;
  }

  /* Text input */
  div[data-baseweb="input"] > div {
    background: #13131f !important;
    border: 1px solid #2d2d3f !important;
    border-radius: 10px !important;
  }

  /* Progress bar */
  div[data-testid="stProgress"] > div { background: #1f1f2e; border-radius: 99px; }
  div[data-testid="stProgress"] > div > div {
    background: linear-gradient(90deg, #ff4b4b, #ff8f00);
    border-radius: 99px;
  }

  /* Divider */
  hr { border-color: #1f1f2e; }

  /* Audio player */
  audio { width: 100%; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# ── Imports (after page config) ───────────────────────────────────────────────
from src.ui.sidebar       import render_sidebar
from src.ui.search_tab    import render_search_tab
from src.ui.queue_manager import render_queue_tab, load_persisted_queue
from src.ui.explorer      import render_library_tab

# ── Sidebar ───────────────────────────────────────────────────────────────────
settings = render_sidebar()

# ── Session state init (from persistent disk storage) ──────────────────────────
if "queue" not in st.session_state or st.session_state.queue is None:
    st.session_state.queue = load_persisted_queue(settings["library_dir"])

# ── Hero header ───────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding: 1.6rem 0 0.4rem;">
  <h1 style="font-size:2.4rem;font-weight:800;margin:0;
             background:linear-gradient(90deg,#ff4b4b,#ff8f00);
             -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
    🎙️ VocalRemover Pro
  </h1>
  <p style="color:#666;margin:4px 0 0;font-size:1rem;">
    Professional acapella extraction powered by UVR · AMD DirectML · iTunes + Deezer discovery
  </p>
</div>
""", unsafe_allow_html=True)

# Queue badge in header
q_count = len(st.session_state.queue)
if q_count:
    st.markdown(
        f'<span style="background:#ff4b4b;color:#fff;padding:3px 12px;'
        f'border-radius:99px;font-size:0.8rem;font-weight:700">'
        f'Queue: {q_count} track{"s" if q_count != 1 else ""}</span>',
        unsafe_allow_html=True,
    )

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_search, tab_queue, tab_library = st.tabs([
    "🔍  Search & Discover",
    f"📋  Queue Manager  {'· ' + str(q_count) if q_count else ''}",
    "📁  Library",
])

with tab_search:
    render_search_tab(settings)

with tab_queue:
    render_queue_tab(settings)

with tab_library:
    render_library_tab(settings)
