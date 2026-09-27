#!/usr/bin/env python3
"""
BookGenerator AI Web Server & REST API Bridge
Provides a sleek web interface and API endpoints for running the multi-agent Tamil AI book pipeline.
"""

import os
import sys
import json
import glob
import threading
import subprocess
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler

PORT = 8080
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# Global Job State
JOB_STATE = {
    "status": "idle",       # idle, running, completed, failed
    "phase": "world",       # world, char, outline, draft, docx, completed
    "progress_percent": 0,
    "message": "Ready to generate books.",
    "active_title": "",
    "docx_path": "",
    "error": "",
    "chapters": []
}

class BookGeneratorHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # Serve files from web/ directory if path starts with static file
        parsed_url = urllib.parse.urlparse(path)
        clean_path = parsed_url.path
        
        if clean_path in ["/", "/index.html"]:
            return os.path.join(WEB_DIR, "index.html")
        elif clean_path in ["/styles.css", "/app.js"]:
            return os.path.join(WEB_DIR, clean_path.lstrip("/"))
        return super().translate_path(path)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/status":
            self.send_json_response(JOB_STATE)
            return

        elif path.startswith("/api/chapters/"):
            chap_num_str = path.replace("/api/chapters/", "").strip()
            try:
                chap_num = int(chap_num_str)
                filename = f"chapter_{chap_num:02d}.md"
                filepath = os.path.join(OUTPUT_DIR, filename)
                if os.path.exists(filepath):
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    self.send_json_response({"chapter_number": chap_num, "content": content})
                else:
                    self.send_json_response({"error": "Chapter file not found yet."}, status=404)
            except ValueError:
                self.send_json_response({"error": "Invalid chapter number."}, status=400)
            return

        elif path == "/api/download":
            docx_file = JOB_STATE.get("docx_path") or os.path.join(OUTPUT_DIR, "Generated_Book.docx")
            if not os.path.exists(docx_file):
                docx_files = glob.glob(os.path.join(OUTPUT_DIR, "*.docx"))
                if docx_files:
                    docx_file = docx_files[0]

            if os.path.exists(docx_file):
                self.send_response(200)
                self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                self.send_header("Content-Disposition", f"attachment; filename={os.path.basename(docx_file)}")
                self.send_header("Content-Length", str(os.path.getsize(docx_file)))
                self.end_headers()
                with open(docx_file, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_json_response({"error": "No compiled DOCX manuscript available yet."}, status=404)
            return

        # Fallback to static file server
        super().do_GET()

    def do_POST(self):
        if self.path == "/api/generate":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            
            try:
                data = json.loads(body)
            except Exception:
                self.send_json_response({"error": "Invalid JSON body"}, status=400)
                return

            if JOB_STATE["status"] == "running":
                self.send_json_response({"error": "A book generation task is already in progress."}, status=400)
                return

            # Launch generation thread
            t = threading.Thread(target=run_generation_task, args=(data,), daemon=True)
            t.start()

            self.send_json_response({"status": "started", "job_id": "job_1"})
            return

        self.send_json_response({"error": "Endpoint not found"}, status=404)

    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))


def run_generation_task(params):
    global JOB_STATE
    title = params.get("title", "தமிழ் காவியம்")
    concept = params.get("concept", title)
    author = params.get("author", "பிரவின் தமிழன்")
    language = params.get("language", "tamil")
    genre = params.get("genre", "tamil_historical")
    provider = params.get("provider", "ollama")
    model = params.get("model", "deepseek-r1:latest")
    api_key = params.get("api_key", "").strip()
    ollama_url = params.get("ollama_url", "http://localhost:11434")

    # Set environment variables for API key
    env_vars = os.environ.copy()
    if api_key:
        if provider == "gemini":
            env_vars["GEMINI_API_KEY"] = api_key
        elif provider == "openai":
            env_vars["OPENAI_API_KEY"] = api_key
        elif provider == "anthropic":
            env_vars["ANTHROPIC_API_KEY"] = api_key
        elif provider in ["jev", "typesafe"]:
            env_vars["JEV_API_KEY"] = api_key
            env_vars["TYPESAFE_API_KEY"] = api_key
        env_vars["LLM_API_KEY"] = api_key

    output_filename = f"{title.replace(' ', '_')}.docx"
    output_docx_path = os.path.join(OUTPUT_DIR, output_filename)


    JOB_STATE.update({
        "status": "running",
        "phase": "world",
        "progress_percent": 10,
        "message": f"World Builder Agent: Generating World Bible for '{title}'...",
        "active_title": title,
        "docx_path": output_docx_path,
        "error": "",
        "chapters": []
    })

    cmd = [
        sys.executable, "main.py",
        "--title", title,
        "--concept", concept,
        "--author", author,
        "--language", language,
        "--genre", genre,
        "--provider", provider,
        "--model", model,
        "--ollama-url", ollama_url,
        "--output", output_docx_path,
        "--reset"
    ]


    print(f"\n[Web Server] Launching Book Generator process: {' '.join(cmd)}")

    try:
        proc = subprocess.Popen(
            cmd,
            cwd=BASE_DIR,
            env=env_vars,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )


        for line in iter(proc.stdout.readline, ""):
            line_str = line.strip()
            print(f"  [AI Engine] {line_str}")

            if "Agent: World Builder" in line_str:
                JOB_STATE["phase"] = "world"
                JOB_STATE["progress_percent"] = 15
                JOB_STATE["message"] = "World Builder Agent: Creating setting and cultural rules..."
            elif "Agent: Character Architect" in line_str:
                JOB_STATE["phase"] = "char"
                JOB_STATE["progress_percent"] = 25
                JOB_STATE["message"] = "Character Architect Agent: Building voice fingerprints & profiles..."
            elif "Agent: Master Outliner" in line_str:
                JOB_STATE["phase"] = "outline"
                JOB_STATE["progress_percent"] = 35
                JOB_STATE["message"] = "Master Outliner Agent: Scaffolding 12-chapter beat sheet..."
            elif "CHAPTER" in line_str and "CHAPTER 12/" not in line_str:
                JOB_STATE["phase"] = "draft"
                # Estimate chapter progress
                try:
                    num = int(line_str.split("CHAPTER")[1].split("/")[0].strip())
                    JOB_STATE["progress_percent"] = 35 + int((num / 12) * 55)
                    JOB_STATE["message"] = f"Prose Drafter & Adversarial Critics: Drafting Chapter {num}/12..."
                    
                    chap_file = f"chapter_{num:02d}.md"
                    if chap_file not in JOB_STATE["chapters"]:
                        JOB_STATE["chapters"].append(chap_file)
                except Exception:
                    pass
            elif "Compiling" in line_str or "Finalizing Commercial" in line_str:
                JOB_STATE["phase"] = "docx"
                JOB_STATE["progress_percent"] = 95
                JOB_STATE["message"] = "DOCX Compiler: Packaging 300-page bestseller document..."

        proc.wait()

        if proc.returncode == 0:
            JOB_STATE.update({
                "status": "completed",
                "phase": "completed",
                "progress_percent": 100,
                "message": f"Successfully generated '{title}' commercial DOCX manuscript!"
            })
        else:
            JOB_STATE.update({
                "status": "failed",
                "message": "Engine run returned non-zero exit code.",
                "error": "Pipeline execution stopped unexpectedly."
            })

    except Exception as ex:
        print(f"[Web Server Error] {ex}")
        JOB_STATE.update({
            "status": "failed",
            "message": f"Execution error: {ex}",
            "error": str(ex)
        })


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(WEB_DIR, exist_ok=True)

    server = HTTPServer(("0.0.0.0", PORT), BookGeneratorHandler)
    print("=" * 80)
    print(f"  BOOKGENERATOR AI (TAMIL ED.) - WEB APPLICATION SERVER")
    print("=" * 80)
    print(f"  ► Local Web UI: http://localhost:{PORT}")
    print(f"  ► Server root: {BASE_DIR}")
    print(f"  ► Press Ctrl+C to stop the server.")
    print("=" * 80 + "\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down BookGenerator AI web server...")
        server.server_close()

if __name__ == "__main__":
    main()
