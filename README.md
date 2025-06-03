# Intelligent Engineering Partner - Flask Edition 🤖

This Flask application helps guide engineers through the nine classical phases of development, leveraging AI to streamline workflows and generate documentation.

## Overview

The application provides:
- A web interface to input and manage data for each of the 9 development phases.
- AI-powered generation of:
    - Solution summaries for each phase.
    - Detailed phase documents based on predefined outlines.
    - Seed data for subsequent phases.
- A modular structure based on Flask, with UI styled using custom CSS.
- Configuration of phases and fields via an external `phases.yaml` file.

## Prerequisites

- **Python 3.8+** and **pip**
- A **Google Gemini API Key**. You can obtain one from [Google AI Studio](https://aistudio.google.com/app/apikey).
- Git (optional, for version control if you host this project)

## Project Structure

```
engineering-partner-flask/
│
├── app.py                    # Main Flask application
├── config.py                 # Loads phases.yaml
├── gemini_client.py          # Gemini API integration
├── doc_generator.py          # Document generation logic
├── phases.yaml               # Phase definitions and document outlines
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── setup_env.ps1             # PowerShell script for setting environment variables (Windows)
├── run_app.ps1               # PowerShell script for running the application (Windows)
│
├── static/
│   └── css/
│       └── style.css         # CSS for UI styling
│
├── templates/                # HTML templates (layout, index, phase_*.html)
│   ├── layout.html
│   ├── index.html
│   ├── phase_1.html
│   └── ... (phase_2.html to phase_9.html)
│
└── generated_docs/           # Stores generated Markdown documents (created automatically)
    └── .gitkeep              # Ensures directory is included if empty
```

## Setup Instructions

1.  **Get the Code:**
    Download the ZIP file containing the application and extract it to your desired location.

2.  **Create a Python Virtual Environment:**
    Open your terminal or command prompt, navigate into the `engineering-partner-flask` directory, and run:
    ```bash
    python -m venv .venv
    ```

3.  **Activate the Virtual Environment:**
    -   **Windows (Command Prompt/PowerShell):**
        ```cmd
        .\.venv\Scripts\activate
        ```
    -   **macOS/Linux (bash/zsh):**
        ```bash
        source .venv/bin/activate
        ```
    You should see `(.venv)` at the beginning of your prompt.

4.  **Install Dependencies:**
    With the virtual environment activated, install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

5.  **Set Environment Variables:**
    The application requires your Gemini API Key and a Flask Secret Key.

    *   **`GEMINI_API_KEY`**: Your actual API key from Google AI Studio.
    *   **`FLASK_SECRET_KEY`**: A long, random string for securing Flask sessions. For development, `app.py` has a default, but it's better to set your own.

    **Option A: Using `setup_env.ps1` (Windows PowerShell users):**
    If you are on Windows and using PowerShell, you can run the provided script:
    ```powershell
    .\setup_env.ps1
    ```
    This script will prompt you for your Gemini API Key and an optional Flask Secret Key, then set them for your *current PowerShell session only*.

    **Option B: Manual Setup (All Platforms - Recommended for persistence):**

    *   **macOS/Linux (bash/zsh):**
        Open your shell configuration file (e.g., `~/.bashrc`, `~/.zshrc`, `~/.profile`):
        ```bash
        nano ~/.bashrc  # Or your preferred editor and file
        ```
        Add the following lines at the end, replacing placeholders with your actual values:
        ```bash
        export GEMINI_API_KEY="YOUR_ACTUAL_GEMINI_API_KEY"
        export FLASK_SECRET_KEY="your_very_strong_and_unique_secret_key_here"
        ```
        Save the file and reload your shell configuration:
        ```bash
        source ~/.bashrc # Or the file you edited
        ```

    *   **Windows (Command Prompt - for current session):**
        ```cmd
        set GEMINI_API_KEY="YOUR_ACTUAL_GEMINI_API_KEY"
        set FLASK_SECRET_KEY="your_very_strong_and_unique_secret_key_here"
        ```
        (To set them permanently on Windows, search for "environment variables" in the Start Menu to edit system environment variables.)

## Running the Application

1.  **Ensure your virtual environment is activated** (you should see `(.venv)` in your prompt).
2.  **Ensure `GEMINI_API_KEY` is set** (see step 5 above).

    **Option A: Using `run_app.ps1` (Windows PowerShell users):**
    If you are on Windows and using PowerShell:
    ```powershell
    .\run_app.ps1
    ```
    This script attempts to activate the venv (if not already) and then starts the Flask app.

    **Option B: Manual Run (All Platforms):**
    Navigate to the `engineering-partner-flask` directory in your terminal and run:
    ```bash
    python app.py
    ```

3.  Open your web browser and navigate to: `http://127.0.0.1:5001`

## Using the Application

-   Navigate through the phases using the sidebar.
-   Enter data into the fields for each phase.
-   Use the buttons to:
    -   **Save Progress**: Saves the current phase's data to your session.
    -   **Generate Solution**: Uses AI to create a summary based on your input for the current phase.
    -   **Generate Document**: Uses AI to create a full Markdown document for the current phase, based on its outline and all data entered up to this point.
    -   **Seed Phase X**: Pre-fills data for the next phase using AI, based on the current phase's content.
-   Generated documents can be downloaded using the link that appears after generation.

## Extending for Other Phases

The application is designed to be dynamic. The HTML templates for phases (`templates/phase_X.html`) are generic and render content based on the `phases.yaml` configuration.

-   **To modify fields or document outlines for any phase:** Edit the corresponding entry in `phases.yaml`.
-   **No HTML changes are usually needed** for `phase_X.html` files if you only change field definitions or document outlines in `phases.yaml`, as the templates adapt dynamically.

## Key Considerations for Further Development

*   **Error Handling**: While basic error handling is in place, it can be further enhanced for a production application.
*   **CSRF Protection**: For production, integrate Flask-WTF or a similar library for CSRF protection on forms.
*   **Database Persistence**: The current version uses Flask sessions for data storage (data is lost when the browser session ends). For persistent storage (like PostgreSQL as mentioned in the original spec), you would need to integrate a database (e.g., using SQLAlchemy) and modify the data helper functions in `app.py`.
*   **User Authentication**: If multiple users or projects are needed, implement a user authentication and authorization system.
*   **Asynchronous Operations**: For long-running AI calls, consider using background tasks (e.g., with Celery and Redis/RabbitMQ) to improve UI responsiveness.
*   **Testing**: Implement comprehensive unit and integration tests.

Happy Engineering! 🚀
