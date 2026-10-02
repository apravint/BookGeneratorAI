"""
BookGenerator AI (Tamil & English Edition) - Streamlit Dashboard
Launch with: streamlit run streamlit_app.py
"""

import os
import sys
import time
import json
from pathlib import Path
import streamlit as st

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generator.blueprint import BLUEPRINTS, get_blueprint_for_genre, TAMIL_GENRES
from generator.llm_client import LLMClient
from generator.docx_compiler import compile_book_to_docx
from agents.world_builder import WorldBuilderAgent
from agents.character_architect import CharacterArchitectAgent
from agents.master_outliner import MasterOutlinerAgent
from agents.prose_drafter import ProseDrafterAgent
from agents.slop_editor import AntiSlopEditorAgent
from agents.adversarial_reviewer import MasterAdversarialReviewer

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

        num_chapters = st.slider("Target Chapters", min_value=1, max_value=12, value=4)

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

        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        docx_filename = output_dir / f"{title.replace(' ', '_')}_streamlit.docx"

        try:
            # Initialize Client
            llm_client = LLMClient(
                provider=provider,
                api_key=api_key,
                model=model_name,
                ollama_url=ollama_url
            )

            blueprint = get_blueprint_for_genre(genre)

            # Step 1: World Building
            status_text.info("🌐 Step 1/5: World Builder Agent constructing world bible...")
            progress_bar.progress(15)
            log_container.write("► Launching World Builder Agent...")
            world_agent = WorldBuilderAgent(llm_client)
            world_bible = world_agent.generate(concept, blueprint, language=language)
            log_container.success("✓ World Bible created successfully.")

            # Step 2: Character Architecture
            status_text.info("👤 Step 2/5: Character Architect Agent crafting profiles...")
            progress_bar.progress(35)
            log_container.write("► Launching Character Architect Agent...")
            char_agent = CharacterArchitectAgent(llm_client)
            characters = char_agent.generate(concept, world_bible, blueprint, language=language)
            log_container.success(f"✓ Character Profiles generated ({len(characters)} main characters).")

            # Step 3: Master Outlining
            status_text.info("📜 Step 3/5: Master Outliner generating chapter beats...")
            progress_bar.progress(50)
            log_container.write(f"► Launching Master Outliner Agent for {num_chapters} chapters...")
            outliner = MasterOutlinerAgent(llm_client)
            outline = outliner.generate(concept, world_bible, characters, blueprint, num_chapters=num_chapters, language=language)
            log_container.success("✓ Master Outline completed.")

            # Step 4: Prose Drafting & Anti-Slop Editing
            status_text.info("✍️ Step 4/5: Drafting & Editing Chapters...")
            drafter = ProseDrafterAgent(llm_client)
            editor = AntiSlopEditorAgent(llm_client)
            reviewer = MasterAdversarialReviewer(llm_client)

            completed_chapters = []
            total = len(outline)

            for idx, item in enumerate(outline, 1):
                c_title = item.get("chapter_title", f"Chapter {idx}")
                c_summary = item.get("summary", "")
                c_beats = item.get("beats", [])

                status_text.info(f"✍️ Drafting Chapter {idx}/{total}: {c_title}...")
                log_container.write(f"► Drafting Chapter {idx}: {c_title}...")

                raw_prose = drafter.draft_chapter(
                    chapter_number=idx,
                    chapter_title=c_title,
                    summary=c_summary,
                    beats=c_beats,
                    world_bible=world_bible,
                    characters=characters,
                    language=language
                )

                log_container.write(f"► Running Anti-Slop Editor on Chapter {idx}...")
                edited_prose = editor.edit_chapter(raw_prose, language=language)

                log_container.write(f"► Master Reviewer auditing Chapter {idx}...")
                review_result = reviewer.review_chapter(edited_prose, language=language)

                completed_chapters.append({
                    "chapter_number": idx,
                    "title": c_title,
                    "content": edited_prose,
                    "score": review_result.get("score", 9.0) if isinstance(review_result, dict) else 9.0
                })

                prog_pct = 50 + int((idx / total) * 40)
                progress_bar.progress(prog_pct)
                log_container.success(f"✓ Chapter {idx} finalized.")

            # Step 5: Compilation
            status_text.info("📄 Step 5/5: Compiling Publishing-Grade DOCX...")
            progress_bar.progress(95)

            book_dict = {
                "metadata": {
                    "title": title,
                    "author": author,
                    "genre": genre,
                    "language": language
                },
                "chapters": completed_chapters
            }

            compile_book_to_docx(book_dict, str(docx_filename), language=language)
            progress_bar.progress(100)
            status_text.success("🎉 Book Generation Complete!")

            st.balloons()
            st.divider()
            st.subheader("📥 Export & Read Book")

            # Reading Tabs
            tab_docx, tab_read, tab_json = st.tabs(["📄 Download DOCX", "📖 Read Manuscript", "🔍 Raw JSON Data"])

            with tab_docx:
                with open(docx_filename, "rb") as f:
                    st.download_button(
                        label=f"⬇️ Download '{title}' (.docx)",
                        data=f,
                        file_name=os.path.basename(docx_filename),
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                st.info("The exported DOCX includes custom Tamil typography (Mukta Malar / Noto Sans Tamil), localized cover page, title block, and formatted headers.")

            with tab_read:
                for ch in completed_chapters:
                    with st.expander(f"Chapter {ch['chapter_number']}: {ch['title']}"):
                        st.markdown(ch["content"])

            with tab_json:
                st.json(book_dict)

        except Exception as e:
            status_text.error(f"Error during generation: {str(e)}")
            st.exception(e)

if __name__ == "__main__":
    main()
