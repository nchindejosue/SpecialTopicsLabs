# Marvel Code - AI-Powered Codebase Orchestrator

Marvel Code is an advanced, AI-driven IDE designed for autonomous software engineering. It combines a deep-blue themed user interface with a powerful orchestration engine capable of reading, writing, and executing code across entire projects.

## 🚀 How to Run the Project

To launch the Marvel Code application, follow these steps:

1. **Environment Setup**: Ensure you have Python 3.10+ installed.
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure API Keys**:
   - Rename `.env.example` to `.env`.
   - Add your `GEMINI_API_KEY` and `FIGMA_ACCESS_TOKEN`.
4. **Launch the Application**:
   - Open and run the `Capstone_Orchestrator.ipynb` notebook.
   - **OR** run the main script directly:
     ```bash
     python app/main_window.py
     ```

## 🔐 Credentials for Login

Use the following credentials to access the secure IDE environment:

*   **Username**: `admin`
*   **Password**: `admin123`

## 📁 Project Structure

*   `app/`: Core application source code.
    *   `core/`: The "brain" of Marvel Code.
        *   `ai_engine/`: Integration with Gemini API and Figma fetching logic.
        *   `compiler/`: CEIL (Command Execution Interface Language) Lexer and Parser.
        *   `executor/`: Secure command execution environment.
        *   `security/`: Database and security engine for user authentication.
    *   `ui/`: Custom Tkinter-based components and theme definitions.
*   `User_Codebase/`: A sample directory for the AI to work within.
*   `Capstone_Orchestrator.ipynb`: The primary entry point for demonstration and testing.

## ⚠️ Important Usage Notes (For the Lecturer)

*   **Python Focus**: This orchestrator is currently optimized for **Python-based codebases**.
*   **Scale Limitation**: Please avoid running this against massive codebases. It is designed to maintain "Full Project Vision" within a reasonable token window.
*   **Recommended Start**: For the best demonstration, **select an empty folder** as your project root and prompt the AI to build a new Python application (e.g., *"Build a simple weather dashboard with Tkinter"*) from scratch.
*   **Figma Integration**: Paste a Figma design link (with a `node-id`) into the chat to see Marvel Code extract specific UI components and implement them automatically.
