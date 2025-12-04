
import sys
import os
import unittest
import re

class CIServer:
    def __init__(self, file_path):
        self.file_path = file_path
        self.status = "PENDING"

    def log(self, message):
        print(f"[CI-SERVER] {message}")

    def gate_1_static_analysis(self):
        self.log("[SEARCH] Running Gate 1: Static Analysis (Linting)...")
        try:
            with open(self.file_path, 'r') as f:
                content = f.read()
                
            # Check 1: Class names should be CamelCase
            if not re.search(r'class [A-Z][a-zA-Z0-9]*:', content):
                self.log("[FAIL] Class names must be CamelCase")
                return False
            
            # Check 2: Functions should be snake_case
            if re.search(r'def [A-Z]', content):
                self.log("[FAIL] Function names must be snake_case")
                return False
                
            self.log("[PASS] Code style looks good.")
            return True
        except Exception as e:
            self.log(f"[ERROR] {e}")
            return False

    def gate_2_security_scan(self):
        self.log("[SECURE] Running Gate 2: Security Scan...")
        try:
            with open(self.file_path, 'r') as f:
                content = f.read()
                
            # Check for hardcoded secrets
            if "SECRET" in content or "PASSWORD" in content or "API_KEY" in content.upper():
                self.log("[FAIL] Security Vulnerability Found! (Hardcoded Secret detected)")
                return False
                
            self.log("[PASS] No obvious secrets found.")
            return True
        except Exception as e:
            self.log(f"[ERROR] {e}")
            return False

    def gate_3_unit_tests(self):
        self.log("[TEST] Running Gate 3: Unit Tests...")
        # Load tests dynamically
        loader = unittest.TestLoader()
        start_dir = os.path.dirname(self.file_path)
        suite = loader.discover(start_dir, pattern='test_*.py')
        
        runner = unittest.TextTestRunner(verbosity=0)
        result = runner.run(suite)
        
        if result.wasSuccessful():
            self.log("[PASS] All Unit Tests Passed.")
            return True
        else:
            self.log(f"[FAIL] {len(result.errors) + len(result.failures)} tests failed.")
            return False

    def run_pipeline(self):
        print(">>> STARTING CI PIPELINE FOR: " + self.file_path)
        print("="*40)
        
        if not self.gate_1_static_analysis():
            print("="*40)
            print("[STOP] PIPELINE FAILED at Gate 1.")
            return
            
        if not self.gate_2_security_scan():
            print("="*40)
            print("[STOP] PIPELINE FAILED at Gate 2.")
            return
            
        if not self.gate_3_unit_tests():
            print("="*40)
            print("[STOP] PIPELINE FAILED at Gate 3.")
            return
            
        print("="*40)
        print("[SUCCESS] BUILD SUCCESSFUL! Ready for Deployment.")

if __name__ == "__main__":
    # Run on the banking app
    pipeline = CIServer("banking_app.py")
    pipeline.run_pipeline()
