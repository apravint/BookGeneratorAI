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
from generator.llm_client import LlmClient, LLMClient
from generator.docx_compiler import compile_book, compile_book_to_docx
from tools.file_writer import FileWriterTool
from schemas.models import StoryState
from agents.world_builder import WorldBuilderAgent
from agents.character_architect import CharacterArchitectAgent
from agents.master_outliner import MasterOutlinerAgent
from agents.prose_drafter import ProseDrafterAgent
from agents.critics import MasterAdversarialReviewer, AntiSlopEditorAgent

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
            llm_client = LlmClient(
                provider=provider,
                api_key=api_key if api_key else None,
                model=model_name,
                ollama_url=ollama_url
            )

            # Step 1: World Building
            status_text.info("🌐 Step 1/5: World Builder Agent constructing World Bible...")
            progress_bar.progress(15)
            log_container.write("► Launching World Builder Agent...")
            world_agent = WorldBuilderAgent(llm_client)
            world_bible = world_agent.build_world(seed_title=title, seed_concept=concept, genre=genre, language=language)
            log_container.success(f"✓ World Bible created: '{world_bible.title}' ({len(world_bible.rules)} hard rules defined).")

            # Step 2: Character Architecture
            status_text.info("👤 Step 2/5: Character Architect Agent crafting profiles...")
            progress_bar.progress(35)
            log_container.write("► Launching Character Architect Agent...")
            char_agent = CharacterArchitectAgent(llm_client)
            character_registry = char_agent.build_characters(world_bible, author_name=author, language=language)
            log_container.success(f"✓ Character Profiles generated ({len(character_registry.characters)} characters initialized).")

            # Step 3: Master Outlining
            status_text.info("📜 Step 3/5: Master Outliner generating chapter beats...")
            progress_bar.progress(50)
            log_container.write(f"► Launching Master Outliner Agent for {num_chapters} chapters...")
            outliner = MasterOutlinerAgent(llm_client)
            master_outline = outliner.build_outline(world_bible, character_registry, language=language)
            target_chapters = master_outline.chapters[:num_chapters]
            log_container.success(f"✓ Master Outline scaffolded: {len(target_chapters)} chapters ready.")

            # Step 4: Prose Drafting & Adversarial Revision Loop
            status_text.info("✍️ Step 4/5: Drafting & Reviewing Chapters...")
            drafter = ProseDrafterAgent(llm_client)
            reviewer = MasterAdversarialReviewer(llm_client)
            story_state = StoryState()
            file_writer = FileWriterTool(output_dir=str(output_dir))
            file_writer.ensure_front_matter(title=title, domain=concept, author=author, language=language)

            completed_chapters = []
            total = len(target_chapters)

            for idx, chapter_beat in enumerate(target_chapters, 1):
                c_num = chapter_beat.chapter_number
                c_title = chapter_beat.title

                status_text.info(f"✍️ Drafting Chapter {c_num}/{total}: {c_title}...")
                log_container.write(f"► Drafting Chapter {c_num}: {c_title}...")

                draft_text = drafter.draft_chapter(
                    chapter_beat=chapter_beat,
                    world_bible=world_bible,
                    registry=character_registry,
                    story_state=story_state,
                    revision_brief=None
                )

                log_container.write(f"► Adversarial Critics auditing Chapter {c_num}...")
                revision_brief = reviewer.evaluate_chapter(
                    chapter_beat=chapter_beat,
                    chapter_text=draft_text,
                    world_bible=world_bible,
                    registry=character_registry,
                    story_state=story_state
                )

                if revision_brief.passed_audit:
                    log_container.success(f"✓ Chapter {c_num} passed adversarial audit clean!")
                else:
                    log_container.warning(f"⚠️ Chapter {c_num}: Found {len(revision_brief.continuity_issues)} continuity issue(s) & {len(revision_brief.slop_violations)} slop violation(s).")

                # Persist chapter markdown
                file_writer.write_markdown_chapter(c_num, draft_text)

                # Update rolling story state
                summary_prompt = f"Provide a concise 3-bullet narrative recap of Chapter {c_num}: {c_title}.\nText snippet:\n{draft_text[:1500]}"
                try:
                    chap_summary = llm_client.generate_text(summary_prompt, system_prompt="You are a narrative continuity summarizer. Write in " + ("Tamil" if language in ["tamil", "ta"] else "English") + ".")
                except Exception:
                    chap_summary = f"- Chapter {c_num} ({c_title}): Key events unfolded as planned."

                story_state.story_so_far_summary += f"\n- Chapter {c_num} ({c_title}): {chap_summary.strip()}"
                story_state.current_chapter = c_num

                completed_chapters.append({
                    "chapter_number": c_num,
                    "title": c_title,
                    "content": draft_text,
                    "score": 9.5 if revision_brief.passed_audit else 8.5
                })

                prog_pct = 50 + int((idx / total) * 45)
                progress_bar.progress(prog_pct)
                log_container.success(f"✓ Chapter {c_num} finalized.")

            # Step 5: Compilation
            status_text.info("📄 Step 5/5: Compiling Publishing-Grade DOCX...")
            book_dict = {
                "metadata": {
                    "title": title,
                    "author": author,
                    "genre": genre,
                    "language": language
                },
                "chapters": completed_chapters
            }

            file_writer.compile_docx(
                title=title,
                domain=concept,
                author=author,
                docx_path=str(docx_filename),
                language=language
            )
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
