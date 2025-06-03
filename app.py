import os
import json
import datetime
from flask import (
    Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, jsonify
)
from werkzeug.utils import secure_filename

# Assuming your other .py files are in the same directory or accessible via PYTHONPATH
from config import get_phase_config, get_all_phases, PHASES_CONFIG # PHASES_CONFIG for checking if loaded
from gemini_client import generate_solution_summary, seed_next_phase_data
from doc_generator import build_document_for_phase

app = Flask(__name__)

# --- Application Configuration ---
# IMPORTANT: Change this in a real application or load from environment!
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_default_super_secret_key_123!@#")

# Configuration for file uploads (generated documents)
UPLOAD_FOLDER = 'generated_docs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True) # Ensure the upload folder exists
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- Helper Functions for Session Data Management ---
def get_project_data_from_session() -> Dict[str, Dict[str, Any]]:
    """Retrieves all project phase data stored in the session. Phase IDs are string keys."""
    return session.get('project_data', {})

def save_project_data_to_session(project_data: Dict[str, Dict[str, Any]]) -> None:
    """Saves all project phase data to the session."""
    session['project_data'] = project_data
    session.modified = True # Important for mutable structures like dicts in session

def get_current_phase_data(phase_id: int) -> Dict[str, Any]:
    """Gets data for a specific phase from the project data in session. Uses string phase_id for session keys."""
    project_data = get_project_data_from_session()
    return project_data.get(str(phase_id), {})

def update_current_phase_data(phase_id: int, data_to_update: Dict[str, Any]) -> None:
    """Updates/adds data for a specific phase in session. Uses string phase_id for session keys."""
    project_data = get_project_data_from_session()
    phase_id_str = str(phase_id)
    if phase_id_str not in project_data:
        project_data[phase_id_str] = {}
    project_data[phase_id_str].update(data_to_update)
    save_project_data_to_session(project_data)

# --- Context Processors (Variables available in all templates) ---
@app.context_processor
def inject_global_template_vars():
    all_phases_list = get_all_phases() # From config.py
    current_phase_id_from_session = session.get('current_phase_id', 1)

    active_phase_id = 1 # Default
    if isinstance(current_phase_id_from_session, (int, str)) and str(current_phase_id_from_session).isdigit():
        active_phase_id = int(current_phase_id_from_session)

    max_p_id = 0
    if all_phases_list:
        max_p_id = max(p.id for p in all_phases_list) if all_phases_list else 0
        # Ensure active_phase_id is valid, otherwise default to first phase id or 1
        if not any(p.id == active_phase_id for p in all_phases_list):
            active_phase_id = all_phases_list[0].id if all_phases_list else 1

    return dict(
        get_all_phases_for_nav=get_all_phases, # Function to get phases for navigation
        active_phase_id=active_phase_id,
        max_phase_id=max_p_id
    )

# --- Routes ---
@app.route('/')
def index():
    # Set a default starting phase if none is in session
    all_phases = get_all_phases()
    default_start_phase = all_phases[0].id if all_phases else 1
    session.setdefault('current_phase_id', default_start_phase)
    return render_template('index.html')

@app.route('/phase/<int:phase_id>', methods=['GET'])
def show_phase(phase_id: int):
    phase_config = get_phase_config(phase_id)
    if not phase_config:
        flash(f"Error: Phase {phase_id} configuration not found.", "error")
        return redirect(url_for('index'))

    session['current_phase_id'] = phase_id # Update current phase in session
    current_phase_session_data = get_current_phase_data(phase_id)
    all_project_session_data = get_project_data_from_session()

    # Construct the path for the phase-specific template
    template_name = f'phase_{phase_id}.html'
    # Basic check if template might exist (more robust checks might involve os.path.exists on template dir)
    # For now, we assume if config exists, template should too, or Flask will error.

    return render_template(
        template_name,
        phase_config=phase_config,
        phase_data=current_phase_session_data,
        phase_data_json_str=json.dumps(current_phase_session_data, indent=2), # For debug view
        all_project_data_json_str=json.dumps(all_project_session_data, indent=2) # For debug view
    )

@app.route('/phase/<int:phase_id>/action', methods=['POST'])
def handle_phase_action(phase_id: int):
    phase_config = get_phase_config(phase_id)
    if not phase_config:
        flash(f"Action Error: Phase {phase_id} configuration not found.", "error")
        return redirect(request.referrer or url_for('index'))

    action = request.form.get('action')
    current_phase_form_data = get_current_phase_data(phase_id) # Get existing data

    # Update core field data from the form for the current phase
    new_field_data = {}
    for field_key in phase_config.fields.keys():
        new_field_data[field_key] = request.form.get(field_key, current_phase_form_data.get(field_key, ''))
    update_current_phase_data(phase_id, new_field_data) # Save form field data first

    # Fetch the fully updated data (including just-saved form fields) for AI actions
    updated_current_phase_data_for_ai = get_current_phase_data(phase_id)

    if action == 'save':
        flash(f"Phase {phase_id} data saved successfully!", "success")

    elif action == 'generate_solution':
        if not updated_current_phase_data_for_ai:
            flash("Cannot generate solution: No data entered for this phase yet.", "warning")
        else:
            solution_summary = generate_solution_summary(json.dumps(updated_current_phase_data_for_ai))
            update_current_phase_data(phase_id, {'_solution_summary': solution_summary}) # Save summary to session
            flash("AI Solution Summary generated and updated.", "info")

    elif action == 'generate_doc':
        if not updated_current_phase_data_for_ai:
            flash("Cannot generate document: No data entered for this phase yet.", "warning")
        elif not phase_config.document or not phase_config.document.outline:
             flash(f"Document generation skipped: No document outline configured for Phase {phase_id}.", "warning")
        else:
            all_project_data_from_sess = get_project_data_from_session()
            full_doc_content = build_document_for_phase(phase_id, updated_current_phase_data_for_ai, all_project_data_from_sess)

            doc_filename_base = phase_config.document.name if phase_config.document else f"phase_{phase_id}_doc.md"
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            # Ensure filename is secure and filesystem-friendly
            doc_filename = secure_filename(f"{doc_filename_base.split('.')[0]}_{timestamp}.md")
            doc_filepath = os.path.join(app.config['UPLOAD_FOLDER'], doc_filename)

            try:
                with open(doc_filepath, 'w', encoding='utf-8') as f:
                    f.write(full_doc_content)
                update_current_phase_data(phase_id, {'_generated_doc_filename': doc_filename}) # Store filename for download link
                flash(f"Document '{doc_filename}' generated! Click download button below.", "success")
            except IOError as e:
                flash(f"Error saving document to server: {e}", "error")

    elif action == 'seed_next':
        next_phase_id = phase_id + 1
        next_phase_config = get_phase_config(next_phase_id)
        if not next_phase_config:
            flash(f"Cannot seed: Next phase ({next_phase_id}) is not configured.", "error")
        elif not updated_current_phase_data_for_ai:
            flash("Cannot seed: No data in current phase to use as source.", "warning")
        else:
            next_phase_field_keys = list(next_phase_config.fields.keys())
            if not next_phase_field_keys:
                flash(f"Cannot seed: Next phase ({next_phase_id}) has no fields configured.", "warning")
            else:
                seeded_data_for_next = seed_next_phase_data(json.dumps(updated_current_phase_data_for_ai), next_phase_field_keys)
                update_current_phase_data(next_phase_id, seeded_data_for_next) # Save seeded data to next phase
                flash(f"Phase {next_phase_id} has been seeded with data from Phase {phase_id}!", "info")
                session['current_phase_id'] = next_phase_id # Navigate user to the next phase
                return redirect(url_for('show_phase', phase_id=next_phase_id))
    else:
        flash(f"Unknown action: '{action}'.", "warning")

    return redirect(url_for('show_phase', phase_id=phase_id))

@app.route('/download/<filename>')
def download_file(filename):
    # Sanitize filename again just in case, though it should be secure from generation
    safe_filename = secure_filename(filename)
    if not safe_filename == filename: # Basic check if secure_filename changed it, might indicate issues
        flash("Download error: Invalid filename provided.", "error")
        return redirect(url_for('index'))
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], safe_filename, as_attachment=True)
    except FileNotFoundError:
        flash("Error: Requested file not found on server.", "error")
        # Redirect to where the user was, or a sensible default
        return redirect(request.referrer or url_for('index'))

# --- Main Execution ---
if __name__ == '__main__':
    print("--- Starting Engineering Partner Flask Application ---")
    if not PHASES_CONFIG: # Check if phases.yaml was loaded successfully by config.py
        print("CRITICAL ERROR: Phase configurations from 'phases.yaml' were not loaded.")
        print("Please ensure 'phases.yaml' exists, is correctly formatted, and 'config.py' can access it.")
    if not os.environ.get("GEMINI_API_KEY"):
        print("WARNING: GEMINI_API_KEY environment variable is not set.")
        print("AI-powered features (solution summary, document generation, seeding) will not work.")
    if app.secret_key == "dev_default_super_secret_key_123!@#":
        print("WARNING: Using default Flask secret key. Set FLASK_SECRET_KEY environment variable for production.")

    app.run(debug=True, port=5001) # Using port 5001 for development
