import os

class SecurityEngine:
    def __init__(self, base_path):
        self.base_path = os.path.abspath(base_path)

    def audit_ast(self, ast, role="USER"):
        audited = []
        for cmd in ast:
            file_path = os.path.abspath(os.path.join(self.base_path, cmd['file']))
            if not file_path.startswith(self.base_path):
                raise Exception(f"SECURITY ALERT: Path traversal detected: {cmd['file']}")
            
            if cmd['type'] == 'RUN' and role != 'admin':
                raise Exception(f"SECURITY ALERT: Unauthorized RUN command for role {role}")
            
            audited.append(cmd)
        return audited
