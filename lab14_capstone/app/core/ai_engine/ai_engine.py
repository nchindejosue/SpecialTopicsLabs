import os
import google.generativeai as genai
import requests
import json
import time

def load_env():
    # Helper to find .env file up tree
    current = os.path.dirname(os.path.abspath(__file__))
    while current != os.path.dirname(current):
        env_path = os.path.join(current, ".env")
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    if "=" in line and not line.startswith("#"):
                        key, val = line.strip().split("=", 1)
                        os.environ[key] = val
            break
        current = os.path.dirname(current)

class CeilAIEngine:
    def __init__(self, api_key=None):
        load_env()
        key = api_key or os.getenv("GEMINI_API_KEY")
        self.figma_token = os.getenv("FIGMA_ACCESS_TOKEN")
        if not key:
            print("⚠️ WARNING: GEMINI_API_KEY not found in .env")
        else:
            genai.configure(api_key=key)
            self.system_instruction = (
                "You are MarvelCode, an elite AI Orchestrator with Full Project Vision.\n"
                "You MUST strictly structure your response into these three sections:\n\n"
                "1. CHAT: Any greetings, explanations, or conversational context.\n"
                "2. PLAN: A high-level bulleted list of the steps you will take.\n"
                "3. COMMANDS: The CEIL automation code. THIS IS MANDATORY for execution.\n\n"
                "CEIL SYNTAX RULES (STRICT):\n"
                "- Every command MUST follow this exact format: VERB filename <<< CONTENT >>>\n"
                "- The content MUST be wrapped in triple angle brackets <<< and >>>.\n"
                "- Example: CREATE main.py <<< print('hello') >>>\n"
                "- Verbs: CREATE, PATCH, DELETE, RUN, FETCH_FIGMA.\n"
                "- For PATCH, use: PATCH filename SEARCH <<< old >>> REPLACE <<< new >>>\n\n"
                "ENTRY POINT RULE:\n"
                "- When using the RUN command, ALWAYS target the main entry point of the application (e.g., main.py, app.py, or the primary script).\n"
                "- If you create a new system, ensure you RUN the file that launches the entire thing.\n"
                "- DEPENDENCIES: If you need to install libraries, use RUN pip install <library>. The executor is now smart enough to handle this.\n\n"
                "NEVER omit the <<< >>> markers. NEVER use markdown code blocks inside COMMANDS.\n"
                "If you are creating a file, provide the FULL file content."
            )
            self.model = genai.GenerativeModel(
                'gemini-2.5-pro',
                system_instruction=self.system_instruction
            )

    def fetch_figma_data(self, url):
        """Helper to call Figma API using FIGMA_ACCESS_TOKEN. 
        Fetches the entire file first, then extracts the specific node locally."""
        if not self.figma_token:
            return {"error": "FIGMA_ACCESS_TOKEN not found in .env"}
        
        try:
            # Handle both /file/ and /design/ URLs
            if "/file/" in url:
                file_key = url.split("/file/")[1].split("/")[0]
            elif "/design/" in url:
                file_key = url.split("/design/")[1].split("/")[0]
            else:
                return {"error": "Invalid Figma URL format. Expected /file/ or /design/."}

            # Check for node-id in query parameters
            import urllib.parse as urlparse
            parsed = urlparse.urlparse(url)
            node_id_from_url = urlparse.parse_qs(parsed.query).get('node-id', [None])[0]
            # Figma URLs often use '-' instead of ':' for node IDs
            node_id = node_id_from_url.replace("-", ":") if node_id_from_url else None

            headers = {"X-Figma-Token": self.figma_token}
            endpoint = f"https://api.figma.com/v1/files/{file_key}"
            response = requests.get(endpoint, headers=headers)
            
            if response.status_code != 200:
                return {"error": f"Figma API returned status {response.status_code}: {response.text}"}
                
            full_data = response.json()

            if node_id:
                # Mission: Local Node Extraction
                node_data = self.extract_node_from_json(full_data.get("document", {}), node_id)
                if node_data:
                    return {"node": node_data, "file_name": full_data.get("name"), "node_id": node_id}
                else:
                    return {"error": f"Node ID {node_id} not found in the Figma file.", "file_name": full_data.get("name")}
            
            return full_data
        except Exception as e:
            return {"error": f"Failed to fetch Figma data: {str(e)}"}

    def extract_node_from_json(self, current_node, target_id):
        """Recursively searches for a node with target_id in the Figma document tree."""
        if current_node.get("id") == target_id:
            return current_node
        
        children = current_node.get("children", [])
        for child in children:
            result = self.extract_node_from_json(child, target_id)
            if result:
                return result
        return None

    def build_full_context(self, project_root):
        """Mission 2: Reads all files to provide 'Full Project Vision' within the project folder."""
        context = "FULL CODEBASE CONTEXT:\n"
        # Strictly exclude system, library, and non-readable binary directories
        skip_dirs = {'.git', '__pycache__', 'venv', '.env', 'node_modules', '.ipynb_checkpoints', '.vscode', 'dist', 'build', '.marvelcode'}
        # Strictly exclude binary or non-text extensions
        skip_exts = {'.pyc', '.exe', '.db', '.png', '.jpg', '.jpeg', '.gif', '.zip', '.pdf', '.bin', '.dll', '.so', '.pyo'}

        total_tokens_estimate = 0
        max_context_tokens = 30000 # Safety cap to keep latency reasonable

        for root, dirs, files in os.walk(project_root):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for file in files:
                if any(file.endswith(ext) for ext in skip_exts):
                    continue
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, project_root)
                try:
                    # Skip files larger than 50KB to prevent massive latency
                    if os.path.getsize(file_path) > 51200:
                        context += f"FILE: {rel_path} (Skipped: File too large for real-time context)\n" + "="*30 + "\n"
                        continue
                        
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        # Very rough estimate: 1 word ~= 1.3 tokens
                        total_tokens_estimate += len(content.split()) * 1.3
                        
                        if total_tokens_estimate > max_context_tokens:
                            context += f"FILE: {rel_path} (Context Limit Reached, skipping content)\n" + "="*30 + "\n"
                            continue
                            
                        context += f"FILE: {rel_path}\nCONTENT:\n{content}\n" + "="*30 + "\n"
                except Exception as e:
                    pass
        return context

    def clean_response(self, text):
        """Mission 4: Refined response cleaning. 
        Extracts CEIL commands and ensures syntax compliance even if the AI used markdown."""
        if "COMMANDS" in text:
            text = text.split("COMMANDS")[-1]

        # Pre-process: Convert common markdown failures to CEIL blocks
        # If a line starts with a verb and the next line is a markdown block, wrap it.
        lines = text.split('\n')
        processed_lines = []
        valid_verbs = ["CREATE", "PATCH", "DELETE", "RUN", "FETCH_FIGMA", "OVERWRITE"]
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
                
            # If line starts with a verb but has no block
            if any(line.startswith(v) for v in valid_verbs) and "<<<" not in line:
                processed_lines.append(line)
                # Look ahead for markdown block or content
                if i + 1 < len(lines) and (lines[i+1].strip().startswith("```") or lines[i+1].strip()):
                    processed_lines.append("<<<")
                    i += 1
                    # Skip the opening backticks if present
                    if lines[i].strip().startswith("```"): i += 1
                    
                    # Capture until closing backticks or next verb/end
                    while i < len(lines):
                        if lines[i].strip().startswith("```") or any(lines[i].strip().startswith(v) for v in valid_verbs):
                            break
                        processed_lines.append(lines[i])
                        i += 1
                    processed_lines.append(">>>")
                    # Skip closing backticks if we stopped at them
                    if i < len(lines) and lines[i].strip().startswith("```"): i += 1
                    continue
            else:
                processed_lines.append(lines[i])
            i += 1

        final_text = "\n".join(processed_lines)
        
        # Final pass: Standard cleaning logic
        text = final_text.replace("```ceil", "").replace("```", "").strip()
        lines = text.split('\n')
        clean_lines = []
        is_inside_block = False
        
        for line in lines:
            stripped = line.strip()
            if not stripped and not is_inside_block: continue
            
            if "<<<" in stripped: is_inside_block = True
            
            if is_inside_block or any(stripped.startswith(v) for v in valid_verbs) or ">>>" in stripped:
                clean_lines.append(line)
                
            if ">>>" in stripped: is_inside_block = False
            
        return "\n".join(clean_lines)

    def generate_instructions(self, prompt, project_path, history=None, log_callback=None):
        """Mission 4: Core reasoning and instruction generation with robust error handling and retry logic."""
        full_context = self.build_full_context(project_path)
        
        # PROACTIVE FIGMA INJECTION:
        # If the user provides a Figma URL, fetch the data and inject it into the context immediately.
        if "figma.com/" in prompt:
            import re
            figma_urls = re.findall(r'https?://(?:www\.)?figma\.com/(?:file|design)/[a-zA-Z0-9]+[^\s]*', prompt)
            if figma_urls:
                if log_callback: log_callback(f"Detected Figma URL: {figma_urls[0]}", "AI_OP")
                figma_data = self.fetch_figma_data(figma_urls[0])
                if "error" not in figma_data:
                    if log_callback: log_callback("Figma Data Fetched and Parsed Locally!", "SUCCESS")
                    # Inject the JSON data into the context. 
                    # If it's a node-specific extraction, we'll label it as such.
                    if "node" in figma_data:
                        full_context += f"\nEXTRACTED FIGMA NODE DATA (ID: {figma_data['node_id']}):\n{json.dumps(figma_data['node'], indent=2)}\n"
                        full_context += f"Note: This is a specific part of the '{figma_data['file_name']}' design. Use these details to implement the UI.\n"
                    else:
                        full_context += f"\nFULL FIGMA DESIGN DATA:\n{json.dumps(figma_data, indent=2)}\n"
                        full_context += "Note: Use the full design file to implement the UI perfectly.\n"
                else:
                    error_msg = figma_data['error']
                    if log_callback: log_callback(f"Figma Fetch Failed: {error_msg}", "ERROR")
                    full_context += f"\nFIGMA FETCH ERROR: {error_msg}\n"
        
        # Convert history for Gemini format if provided
        gemini_history = []
        if history:
            for msg in history:
                # FIX: Correctly map keys from ChatManager ('sender', 'message') to Gemini ('role', 'parts')
                sender = msg.get('sender', 'USER')
                content = msg.get('message', '')
                role = "user" if sender == "USER" else "model"
                gemini_history.append({"role": role, "parts": [content]})

        max_retries = 3
        retry_delay = 2 # seconds

        for attempt in range(max_retries):
            try:
                model = genai.GenerativeModel(
                    model_name="gemini-2.5-pro", 
                    system_instruction=self.system_instruction,
                    generation_config={
                        "temperature": 0.2,
                        "top_p": 0.95,
                        "top_k": 40,
                        "max_output_tokens": 8192,
                    },
                    safety_settings=[
                        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                    ]
                )
                
                chat = model.start_chat(history=gemini_history)
                full_query = f"{full_context}\n\nUSER PROMPT: {prompt}"
                response = chat.send_message(full_query)
                
                if not response or not response.text:
                    raise Exception("Empty response from AI")
                    
                return response.text

            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1)) # Exponential backoff
                    continue
                return f"⚠️ ERROR: AI Call Failed - {str(e)}"
        
        return "⚠️ ERROR: AI Call Failed after maximum retries."

    def figma_to_ceil(self, figma_data):
        # 3. Multi-Modal Translation
        prompt = (
            "Act as a UI Transpiler. Convert this Figma JSON data into Python Tkinter code.\n"
            "Wrap the result in a single CEIL 'CREATE' command for 'figma_ui.py'.\n"
            f"DATA: {figma_data}"
        )
        try:
            res = self.model.generate_content(prompt)
            return self.clean_response(res.text)
        except Exception as e:
            return f"ERROR: Figma AI Failed - {str(e)}"
