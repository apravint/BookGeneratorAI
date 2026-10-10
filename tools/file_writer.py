"""
File Writer & Document Compiler Tool
Appends intermediate markdown files and compiles final commercial .docx document.
"""

import os
import shutil
from generator.docx_compiler import compile_book


class FileWriterTool:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def write_markdown_chapter(self, chapter_number: int, content: str) -> str:
        filename = f"chapter_{chapter_number:02d}.md"
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath

    def write_front_matter(self, praise: str, epigraph: str, preface: str, foreword: str):
        files = {
            "praise.md": praise,
            "epigraph.md": epigraph,
            "preface.md": preface,
            "foreword.md": foreword
        }
        for name, text in files.items():
            path = os.path.join(self.output_dir, name)
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)

    def ensure_front_matter(self, title: str, domain: str, author: str, language: str = "english"):
        is_tamil = language.lower() in ["tamil", "ta"]
        praise_file = os.path.join(self.output_dir, "praise.md")
        if not os.path.exists(praise_file):
            if is_tamil:
                praise = f"""# பாராட்டுரைகள்: {title}\n\n> “{title} ஒரு ஒப்பற்ற காவியப் படைப்பு. {author}-ன் எழுத்து நடை வாசகர்களை மெய்சிலிர்க்க வைக்கிறது.”\n>\n> — **உலகளாவிய தமிழ் இலக்கிய விமர்சனம்**\n\n> “தமிழின் செழுமையையும் கதைக்களத்தின் கம்பீரத்தையும் ஒருங்கே கொண்ட அரிய நூல்.”\n>\n> — **முனைவர் க. சுப்பிரமணியன்**, இலக்கிய ஆய்வாளர்\n"""
                epigraph = f"""# நூல் சமர்ப்பணம்\n\n## சமர்ப்பணம்\n*தமிழைத் தாய்மொழியாகக் கொண்ட உலகெங்கும் வாழும் தமிழ் நெஞ்சங்களுக்கும், உண்மைக்கும் நீதிக்கும் போராடும் அனைத்து மாந்தர்களுக்கும்.*\n"""
                preface = f"""# முன்னுரை\n\n> “எண்ணிய முடிதல் வேண்டும், நல்லவே எண்ணல் வேண்டும்.” — மகாகவி பாரதியார்\n\n## நூலின் நோக்கம்\n**{title}** என்பது தமிழ் இலக்கியத்தின் ஆழத்தையும், பண்பாட்டையும் வெளிக்கொணரும் வகையில் எழுதப்பட்டதாகும்.\n"""
                foreword = f"""# வாழ்த்துரை\n\n> “படைப்பாற்றலின் சிகரம் தொடும் எழுத்து.”\n\n**{title}** நூல் ஒரு சிறந்த வரலாற்று/இலக்கிய ஆவணமாகத் திகழ்கிறது. ஆசிரியர் {author} அவர்களுக்கு எமது மனமார்ந்த வாழ்த்துகள்.\n"""
            else:
                praise = f"""# Praise for {title}\n\n> “A masterwork of extraordinary vision and clarity. {author} has written what will undoubtedly be remembered as a definitive achievement. Unputdownable from page one.”\n>\n> — **The Global Architecture & Literary Review**\n\n> “Required reading. Synthesizes complex concepts into an unforgettable, transformative narrative.”\n>\n> — **Enterprise Systems Review**\n"""
                epigraph = f"""# Epigraph & Dedication\n\n## Dedication\n*To curious minds, leaders, and readers everywhere who dare to explore new horizons and master the unknown.*\n\n---\n\n> “The secret of getting ahead is getting started.” — **Mark Twain**\n"""
                preface = f"""# Preface & Readers' Guide\n\n## Preface\nEvery great story or paradigm shift begins with a single realization. **{title}** was written to explore the deepest dimensions of {domain or title}.\n"""
                foreword = f"""# Foreword\n\n**{title}** represents a landmark achievement. Grounded in expertise and vivid storytelling, this volume establishes a definitive blueprint.\n"""
            self.write_front_matter(praise, epigraph, preface, foreword)

    def compile_docx(self, title: str, domain: str, author: str, docx_path: str, language: str = "english"):
        compile_book(
            title=title,
            domain=domain,
            author=author,
            chapters_dir=self.output_dir,
            output_path=docx_path,
            language=language
        )

