"""
BookGenerator AI (Tamil & English Edition) - Streamlit Dashboard
Launch with: streamlit run streamlit_app.py
"""

import os
import sys
import contextlib
import streamlit as st

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generator.blueprint import BLUEPRINTS, TAMIL_GENRES
from generator.llm_client import LlmClient
from pipeline import BookConfig, BookPipeline

# Page Configuration
st.set_page_config(
    page_title="AI Book Studio - Tamil & English",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown("""
<style>
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
    }
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        color: #94a3b8;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .agent-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .stButton>button {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        color: white;
        font-weight: 600;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        width: 100%;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(99, 102, 241, 0.4);
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.markdown('<h1 class="main-title">📚 BookGenerator AI Studio</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Autonomous Multi-Agent Book Writing Engine with Tamil (தமிழ்) & English Support</p>', unsafe_allow_html=True)

    # Sidebar Settings
    with st.sidebar:
        st.header("⚙️ Engine Configurations")
        
        provider = st.selectbox(
            "AI Provider",
            options=["ollama", "gemini", "openai", "anthropic", "jev"],
            index=0,
            help="Select Local Ollama (Free) or Cloud API Provider"
        )

        api_key = ""
        model_name = ""
        ollama_url = "http://localhost:11434"

        if provider == "ollama":
            ollama_url = st.text_input("Ollama Endpoint", value="http://localhost:11434")
            model_name = st.selectbox("Ollama Model", options=["qwen2.5:1.5b", "deepseek-r1:latest", "llama3:latest", "mistral:latest"], index=0)
        elif provider == "gemini":
            api_key = st.text_input("Gemini API Key", type="password", help="Get free key from Google AI Studio")
            model_name = st.selectbox("Gemini Model", options=["gemini-2.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-lite"], index=0)
        elif provider == "openai":
            api_key = st.text_input("OpenAI API Key", type="password")
            model_name = st.selectbox("OpenAI Model", options=["gpt-4o", "gpt-4o-mini"], index=0)
        elif provider == "anthropic":
            api_key = st.text_input("Anthropic API Key", type="password")
            model_name = st.selectbox("Anthropic Model", options=["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"], index=0)
        elif provider == "jev":
            api_key = st.text_input("Jev API Key", type="password")
            model_name = st.selectbox("Jev Model", options=["jev-sys1-standard"], index=0)

        st.divider()
        language = st.radio("Primary Book Language", options=["tamil", "english"], format_func=lambda x: "தமிழ் (Tamil)" if x == "tamil" else "English")
        
        st.divider()
        st.caption("🚀 Powered by Multi-Agent AI (World Builder, Character Architect, Master Outliner, Prose Drafter, Anti-Slop Editor)")

    # Main Input Form
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📖 Book Specifications")
        title = st.text_input("Book Title", value="வேல்விழியின் சபதம்" if language == "tamil" else "The Obsidian Cipher")
        author = st.text_input("Author Name", value="பிரவின் தமிழன்" if language == "tamil" else "Pravin Author")
        
        # Genre Selection
        if language == "tamil":
            genre_options = list(TAMIL_GENRES.keys())
            genre_labels = [f"{k} - {TAMIL_GENRES[k]['name']}" for k in genre_options]
            selected_genre_idx = st.selectbox("Genre / Blueprint", range(len(genre_options)), format_func=lambda i: genre_labels[i])
            genre = genre_options[selected_genre_idx]
        else:
            genre_options = [k for k in BLUEPRINTS.keys() if not k.startswith("tamil_")]
            genre = st.selectbox("Genre / Blueprint", options=genre_options, index=0)

        num_chapters = st.slider("Chapters", min_value=1, max_value=60, value=24)
        target_words = st.number_input("Target Words", min_value=1000, max_value=300000, value=80000, step=5000)

    with col2:
        st.subheader("💡 Story Concept & Prompt")
        default_concept = (
            "சோழ பேரரசின் பின்னணியில் வீரம், காதல், காவிய சதி மற்றும் கடல் பயணங்களை மையமாகக் கொண்ட வரலாற்றுப் புதினம்."
            if language == "tamil"
            else "A thrill-packed sci-fi novel set in a cyberpunk metropolis where quantum memories can be stolen."
        )
        concept = st.text_area("Story Concept / Core Theme", value=default_concept, height=180)

    start_btn = st.button("🚀 Start Autonomous Book Generation")

    # Execution State
    if start_btn:
        if not title or not concept:
            st.error("Please provide both a Title and a Concept.")
            return

        st.divider()
        st.subheader("⚡ Live Multi-Agent Pipeline Execution")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Log terminal
        log_expander = st.expander("📝 Detailed Pipeline Activity Logs", expanded=True)
        log_container = log_expander.container()

        class StreamToLog:
            """Mirrors pipeline progress lines into the page."""
            def write(self, text):
                line = text.strip()
                if line:
                    log_container.text(line)
                    if line.startswith(("PHASE", "CHAPTER ")):
                        status_text.info(line)

            def flush(self):
                pass

        try:
            llm_client = LlmClient(
                provider=provider,
                api_key=api_key if api_key else None,
                model=model_name,
                ollama_url=ollama_url
            )
            config = BookConfig(
                title=title, author=author, concept=concept, genre=genre, language=language,
                chapters=num_chapters, target_words=int(target_words),
            )
            with contextlib.redirect_stdout(StreamToLog()):
                result = BookPipeline(config, llm_client).run()
            progress_bar.progress(100)

            if result["ready"]:
                status_text.success("Automated checks passed. Complete the human steps in the release report before publishing.")
            else:
                status_text.warning(f"Book generated, but NOT ready to publish: {len(result['blockers'])} blocker(s).")
                for blocker in result["blockers"]:
                    st.write(f"- {blocker}")

            st.divider()
            st.subheader("📥 Export & Read Book")
            for label, path, mime in [
                ("DOCX", result["docx"], "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
                ("EPUB", result["epub"], "application/epub+zip"),
            ]:
                with open(path, "rb") as f:
                    st.download_button(f"⬇️ Download {label}", data=f, file_name=os.path.basename(path), mime=mime)
            with open(result["report"], encoding="utf-8") as f:
                st.markdown(f.read())

        except Exception as e:
            status_text.error(f"Error during generation: {str(e)}")
            st.exception(e)

if __name__ == "__main__":
    main()
