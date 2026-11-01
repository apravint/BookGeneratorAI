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
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pipeline import book_dir_for, slugify

PORT = 8080
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

## Global Jobs Storage
JOBS = {}
JOB_COUNTER = 0
JOB_LOCK = threading.Lock()

class BookGeneratorHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        parsed_url = urllib.parse.urlparse(path)
        clean_path = urllib.parse.unquote(parsed_url.path)
        
        if clean_path in ["/", "/index.html"]:
            return os.path.join(WEB_DIR, "index.html")
        elif clean_path in ["/styles.css", "/app.js"]:
            return os.path.join(WEB_DIR, clean_path.lstrip("/"))
            
        target_path = os.path.abspath(os.path.join(WEB_DIR, clean_path.lstrip("/")))
        if not target_path.startswith(os.path.abspath(WEB_DIR) + os.sep):
            return os.path.join(WEB_DIR, "index.html")
        return target_path

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query_params = urllib.parse.parse_qs(parsed.query)

        if path in ["/api/status", "/api/jobs"]:
            jobs_list = list(JOBS.values())
            running_jobs = [j for j in jobs_list if j.get("status") == "running"]
            latest_job = jobs_list[-1] if jobs_list else {
                "status": "idle", "phase": "world", "progress_percent": 0,
                "message": "Ready to generate books.", "active_title": "", "docx_path": "", "chapters": []
            }
            response_data = {
                "active_job": latest_job,
                "running_count": len(running_jobs),
                "total_jobs": len(jobs_list),
                "jobs": jobs_list
            }
            response_data.update(latest_job)
            self.send_json_response(response_data)
            return

        elif path.startswith("/api/chapters/"):
            chap_num_str = path.replace("/api/chapters/", "").strip()
            try:
                chap_num = int(chap_num_str)
                filename = f"chapter_{chap_num:02d}.md"
                job = JOBS.get(query_params.get("job_id", [""])[0]) or (list(JOBS.values())[-1] if JOBS else {})
                filepath = os.path.join(job.get("manuscript_dir", OUTPUT_DIR), filename)
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
            job_id = query_params.get("job_id", [None])[0]
            target_job = JOBS.get(job_id) if job_id else (list(JOBS.values())[-1] if JOBS else None)
            
            docx_file = target_job.get("docx_path") if target_job else os.path.join(OUTPUT_DIR, "Generated_Book.docx")
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
        global JOB_COUNTER
        if self.path == "/api/generate":
            # Browsers cannot send this type cross-site without a CORS approval, which this server never grants
            if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
                self.send_json_response({"error": "Content-Type must be application/json"}, status=415)
                return
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            
            try:
                data = json.loads(body)
            except Exception:
                self.send_json_response({"error": "Invalid JSON body"}, status=400)
                return

            with JOB_LOCK:
                JOB_COUNTER += 1
                job_id = f"job_{JOB_COUNTER}"
                data["job_id"] = job_id

            # Launch concurrent generation thread
            t = threading.Thread(target=run_generation_task, args=(job_id, data), daemon=True)
            t.start()

            self.send_json_response({"status": "started", "job_id": job_id, "message": f"Book generation job '{job_id}' launched successfully."})
            return

        self.send_json_response({"error": "Endpoint not found"}, status=404)

    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))


def run_generation_task(job_id, params):
    global JOBS
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

    book_dir = os.path.join(BASE_DIR, book_dir_for(title))
    output_docx_path = os.path.join(book_dir, f"{slugify(title)}.docx")

    job_record = {
        "job_id": job_id,
        "title": title,
        "author": author,
        "genre": genre,
        "language": language,
        "provider": provider,
        "status": "running",
        "phase": "world",
        "progress_percent": 10,
        "message": f"World Builder Agent: Generating World Bible for '{title}'...",
        "active_title": title,
        "docx_path": output_docx_path,
        "manuscript_dir": os.path.join(book_dir, "manuscript"),
        "error": "",
        "chapters": []
    }
    JOBS[job_id] = job_record


    chapters = str(params.get("chapters", "12"))
    cmd = [
        sys.executable, "-u", "main.py",
        "--title", title,
        "--concept", concept,
        "--author", author,
        "--language", language,
        "--genre", genre,
        "--provider", provider,
        "--chapters", chapters,
        "--output", output_docx_path
    ]
    if model:
        cmd.extend(["--model", model])
    if ollama_url:
        cmd.extend(["--ollama-url", ollama_url])

    print(f"\n[Web Server] Launching Book Generator process for '{title}' (Job: {job_id}): {' '.join(cmd)}")

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
            print(f"  [AI Engine - {job_id}] {line_str}")

            if "Agent: World Builder" in line_str:
                job_record["phase"] = "world"
                job_record["progress_percent"] = 15
                job_record["message"] = "World Builder Agent: Creating setting and cultural rules..."
            elif "Agent: Character Architect" in line_str:
                job_record["phase"] = "char"
                job_record["progress_percent"] = 25
                job_record["message"] = "Character Architect Agent: Building voice fingerprints & profiles..."
            elif "Agent: Master Outliner" in line_str:
                job_record["phase"] = "outline"
                job_record["progress_percent"] = 35
                job_record["message"] = "Master Outliner Agent: Planning chapters and scenes..."
            elif line_str.startswith("CHAPTER "):
                job_record["phase"] = "draft"
                try:
                    num, total = line_str.split("CHAPTER ")[1].split(":")[0].split("/")
                    num, total = int(num), int(total)
                    job_record["progress_percent"] = 35 + int((num / total) * 55)
                    job_record["message"] = f"Prose Drafter & Adversarial Critics: Drafting Chapter {num}/{total}..."
                    
                    chap_file = f"chapter_{num:02d}.md"
                    if chap_file not in job_record["chapters"]:
                        job_record["chapters"].append(chap_file)
                except Exception:
                    pass
            elif "PHASE 4" in line_str or "PHASE 5" in line_str:
                job_record["phase"] = "docx"
                job_record["progress_percent"] = 95
                job_record["message"] = "Release review, publishing kit and DOCX/EPUB compilation..."

        proc.wait()

        if proc.returncode == 0:
            job_record.update({
                "status": "completed",
                "phase": "completed",
                "progress_percent": 100,
                "message": f"Generated '{title}'. Read publishing/release_report.md before publishing."
            })
        else:
            job_record.update({
                "status": "failed",
                "message": "Engine run returned non-zero exit code.",
                "error": "Pipeline execution stopped unexpectedly."
            })

    except Exception as ex:
        print(f"[Web Server Error - {job_id}] {ex}")
        job_record.update({
            "status": "failed",
            "message": f"Execution error: {ex}",
            "error": str(ex)
        })



def scan_existing_output_books():
    """Scans output/ directory for existing .docx manuscripts and populates JOBS."""
    global JOBS, JOB_COUNTER
    docx_files = glob.glob(os.path.join(OUTPUT_DIR, "*.docx"))
    md_files = glob.glob(os.path.join(OUTPUT_DIR, "chapter_*.md"))
    
    if not docx_files and not md_files:
        return

    for idx, fpath in enumerate(sorted(docx_files, key=os.path.getmtime), start=1):
        filename = os.path.basename(fpath)
        title = filename.replace(".docx", "").replace("_", " ")
        job_id = f"existing_{idx}"
        
        JOBS[job_id] = {
            "job_id": job_id,
            "title": title,
            "author": "பிரவின் தமிழன்",
            "genre": "தமிழ் இலக்கியம்",
            "language": "tamil",
            "provider": "OLLAMA / GEMINI",
            "status": "completed",
            "phase": "completed",
            "progress_percent": 100,
            "message": f"ஏற்கனவே உருவாக்கப்பட்ட புத்தகம்: '{title}'",
            "active_title": title,
            "docx_path": fpath,
            "error": "",
            "chapters": [os.path.basename(m) for m in md_files]
        }
        JOB_COUNTER = max(JOB_COUNTER, idx)

    print(f"  ✓ [Disk Scanner] Found {len(JOBS)} existing book manuscript(s) in output/ directory.")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(WEB_DIR, exist_ok=True)
    scan_existing_output_books()

    # Loopback only: this API starts paid LLM jobs and has no authentication
    server = ThreadingHTTPServer(("127.0.0.1", PORT), BookGeneratorHandler)
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

