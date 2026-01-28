import os
import subprocess

class CeilExecutor:
    def __init__(self, base_path):
        self.base_path = base_path

    def execute(self, audited_ast):
        results = []
        for cmd in audited_ast:
            try:
                # Only calculate path if 'file' key exists (FETCH_FIGMA uses 'url')
                path = os.path.join(self.base_path, cmd['file']) if 'file' in cmd else None
                
                if cmd['type'] == 'CREATE':
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    with open(path, 'w') as f: f.write(cmd['content'])
                    results.append(f"CREATED: {cmd['file']}")
                elif cmd['type'] == 'PATCH':
                    with open(path, 'r') as f: content = f.read()
                    new_content = content.replace(cmd['search'], cmd['replace'])
                    with open(path, 'w') as f: f.write(new_content)
                    results.append(f"PATCHED: {cmd['file']}")
                elif cmd['type'] == 'DELETE':
                    if os.path.exists(path):
                        os.remove(path)
                        results.append(f"DELETED: {cmd['file']}")
                elif cmd['type'] == 'RUN':
                    # Clean the command string
                    raw_cmd = cmd['file'].strip()
                    
                    # Mission 3: Robust RUN Handling
                    # 1. Handle "python main.py" or "main.py"
                    if raw_cmd.startswith("python "):
                        target_file = raw_cmd.replace("python ", "").strip()
                    elif raw_cmd == "python":
                        # AI hallucination: wrote 'RUN python' without a file
                        target_file = "main.py" # Intelligent fallback
                    else:
                        target_file = raw_cmd
                    
                    # 2. System Command Detection
                    system_verbs = ['pip', 'npm', 'git', 'node', 'npx']
                    is_system = any(target_file.startswith(v) for v in system_verbs)
                    
                    if is_system:
                        res = subprocess.run(target_file, shell=True, capture_output=True, text=True)
                        results.append(f"SHELL {target_file}: {res.stdout or res.stderr}")
                    else:
                        # 3. Resolve Path
                        full_path = os.path.join(self.base_path, target_file)
                        if not os.path.exists(full_path):
                            # Try basename fallback
                            full_path = os.path.join(self.base_path, os.path.basename(target_file))
                        
                        if os.path.exists(full_path):
                            res = subprocess.run(['python', full_path], capture_output=True, text=True)
                            results.append(f"RUN {target_file}: {res.stdout or res.stderr}")
                        else:
                            results.append(f"ERROR: File {target_file} not found for RUN.")
                elif cmd['type'] == 'FETCH_FIGMA':
                    results.append(f"FETCH_FIGMA {cmd['url']}: Data retrieved from Figma.")
            except Exception as e:
                results.append(f"ERROR on {cmd['file']}: {str(e)}")
        return results
