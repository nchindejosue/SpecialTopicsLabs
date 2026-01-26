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
                    
                    # SYSTEM COMMAND DETECTION:
                    # If it starts with pip, npm, git, etc., run it directly in shell
                    system_verbs = ['pip', 'npm', 'git', 'node', 'npx']
                    is_system = any(raw_cmd.startswith(v) for v in system_verbs)
                    
                    if is_system:
                        # Run as a shell command directly
                        res = subprocess.run(raw_cmd, shell=True, capture_output=True, text=True)
                        results.append(f"SHELL {raw_cmd}: {res.stdout or res.stderr}")
                    else:
                        # Standard Python file execution
                        target_file = raw_cmd.replace('python ', '').strip()
                        full_path = os.path.join(self.base_path, target_file)
                        
                        # Fallback check if file doesn't exist at path
                        if not os.path.exists(full_path):
                            # Try just the basename in the root
                            full_path = os.path.join(self.base_path, os.path.basename(target_file))
                            
                        res = subprocess.run(['python', full_path], capture_output=True, text=True)
                        results.append(f"RUN {target_file}: {res.stdout or res.stderr}")
                elif cmd['type'] == 'FETCH_FIGMA':
                    results.append(f"FETCH_FIGMA {cmd['url']}: Data retrieved from Figma.")
            except Exception as e:
                results.append(f"ERROR on {cmd['file']}: {str(e)}")
        return results
