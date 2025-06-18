import os
import json
import datetime
from typing import Dict, Any # Added for type hinting
from flask import (
    Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, jsonify
)
from werkzeug.utils import secure_filename
from werkzeug.exceptions import HTTPException
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
import datetime # Already imported, but good to ensure it's here for model defaults

# Assuming your other .py files are in the same directory or accessible via PYTHONPATH
from config import (
    get_phase_config, get_all_phases, PHASES_CONFIG, # PHASES_CONFIG for checking if loaded
    SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS # For DB setup
)
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

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS

db = SQLAlchemy(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)

# --- SQLAlchemy Models ---
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, default="Untitled Project")
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    phases = db.relationship('PhaseData', backref='project', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project {self.id}: {self.name}>"

class PhaseData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    phase_id_int = db.Column(db.Integer, nullable=False) # e.g., 1, 2, 3 for Phase 1, Phase 2 etc.
    data = db.Column(db.JSON, nullable=False, default=dict) # Stores the actual phase data dictionary
    last_modified = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('project_id', 'phase_id_int', name='uq_project_phase'),)

    def __repr__(self):
        return f"<PhaseData {self.id} for Project {self.project_id} - PhaseDef {self.phase_id_int}>"

# --- Helper Functions for Database Data Management ---
def get_or_create_default_project() -> Project:
    """Tries to fetch the project with id=1, or creates it if not found."""
    # For simplicity, we're using a fixed ID (1) for the default project.
    # In a multi-project setup, you'd have a way to select or create projects.
    project = Project.query.get(1)
    if project is None:
        project = Project(id=1, name="Default Project") # Specify id if it's not auto-incrementing from a specific value
        db.session.add(project)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash("A database error occurred while trying to load project data. Please try again later.", "error")
            # Depending on app structure, might re-raise or handle differently
            raise
    return project

def get_all_project_phase_data_db(project_id: int) -> Dict[str, Any]:
    """Queries all PhaseData entries for a project and returns them in a dict keyed by phase_id_int."""
    phases = PhaseData.query.filter_by(project_id=project_id).all()
    return {str(phase.phase_id_int): phase.data for phase in phases}

def get_current_phase_data_db(project_id: int, phase_id_int: int) -> Dict[str, Any]:
    """Fetches specific PhaseData for the project and phase_id_int."""
    phase_data_entry = PhaseData.query.filter_by(project_id=project_id, phase_id_int=phase_id_int).first()
    if phase_data_entry and phase_data_entry.data:
        return phase_data_entry.data
    return {}

def update_current_phase_data_db(project_id: int, phase_id_int: int, data_to_update: Dict[str, Any]) -> None:
    """Updates or creates a PhaseData entry for the project and phase_id_int."""
    phase_data_entry = PhaseData.query.filter_by(project_id=project_id, phase_id_int=phase_id_int).first()
    if phase_data_entry:
        current_data = phase_data_entry.data or {}
        current_data.update(data_to_update)
        phase_data_entry.data = current_data
        phase_data_entry.last_modified = datetime.datetime.utcnow()
        # Ensure SQLAlchemy detects the change in the JSON field
        db.session.flag_modified(phase_data_entry, "data")
    else:
        phase_data_entry = PhaseData(
            project_id=project_id,
            phase_id_int=phase_id_int,
            data=data_to_update,
            last_modified=datetime.datetime.utcnow()
        )
        db.session.add(phase_data_entry)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash("A database error occurred while saving your data. Please try again later.", "error")
        # Log error e
        # Depending on app structure, might re-raise or handle differently
        raise

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

    project = get_or_create_default_project()
    session['current_phase_id'] = phase_id # Update current phase in session
    current_phase_db_data = get_current_phase_data_db(project.id, phase_id)
    all_project_db_data = get_all_project_phase_data_db(project.id)

    # Construct the path for the phase-specific template
    template_name = f'phase_{phase_id}.html'
    # Basic check if template might exist (more robust checks might involve os.path.exists on template dir)
    # For now, we assume if config exists, template should too, or Flask will error.

    return render_template(
        template_name,
        phase_config=phase_config,
        phase_data=current_phase_db_data,
        phase_data_json_str=json.dumps(current_phase_db_data, indent=2), # For debug view
        all_project_data_json_str=json.dumps(all_project_db_data, indent=2) # For debug view
    )

@app.route('/phase/<int:phase_id>/action', methods=['POST'])
def handle_phase_action(phase_id: int):
    phase_config = get_phase_config(phase_id)
    if not phase_config:
        flash(f"Action Error: Phase {phase_id} configuration not found.", "error")
        return redirect(request.referrer or url_for('index'))

    project = get_or_create_default_project()
    action = request.form.get('action')
    # Get existing data for the current phase from DB
    current_phase_data_from_db = get_current_phase_data_db(project.id, phase_id)

    # Update core field data from the form for the current phase
    new_field_data = {}
    for field_key in phase_config.fields.keys():
        new_field_data[field_key] = request.form.get(field_key, current_phase_data_from_db.get(field_key, ''))

    # Save the updated form field data to the database
    update_current_phase_data_db(project.id, phase_id, new_field_data)

    # Fetch the fully updated data (including just-saved form fields) for AI actions
    # This re-fetches to ensure we have the absolute latest, though new_field_data could be merged with existing if careful
    updated_current_phase_data_for_ai = get_current_phase_data_db(project.id, phase_id)

    if action == 'save':
        flash(f"Phase {phase_id} data saved successfully to database!", "success")

    elif action == 'generate_solution':
        if not updated_current_phase_data_for_ai:
            flash("Cannot generate solution: No data entered for this phase yet.", "warning")
        else:
            solution_summary = generate_solution_summary(json.dumps(updated_current_phase_data_for_ai))
            # Save summary to the database for the current phase
            update_current_phase_data_db(project.id, phase_id, {'_solution_summary': solution_summary})
            flash("AI Solution Summary generated and updated in database.", "info")

    elif action == 'generate_doc':
        if not updated_current_phase_data_for_ai:
            flash("Cannot generate document: No data entered for this phase yet.", "warning")
        elif not phase_config.document or not phase_config.document.outline:
             flash(f"Document generation skipped: No document outline configured for Phase {phase_id}.", "warning")
        else:
            # For document generation, we need all data for the project
            all_project_data_from_db = get_all_project_phase_data_db(project.id)
            full_doc_content = build_document_for_phase(phase_id, updated_current_phase_data_for_ai, all_project_data_from_db)

            doc_filename_base = phase_config.document.name if phase_config.document else f"phase_{phase_id}_doc.md"
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            doc_filename = secure_filename(f"{doc_filename_base.split('.')[0]}_{timestamp}.md")
            doc_filepath = os.path.join(app.config['UPLOAD_FOLDER'], doc_filename)

            try:
                with open(doc_filepath, 'w', encoding='utf-8') as f:
                    f.write(full_doc_content)
                # Store filename in the database for the current phase for download link
                update_current_phase_data_db(project.id, phase_id, {'_generated_doc_filename': doc_filename})
                flash(f"Document '{doc_filename}' generated! Click download button below.", "success")
            except IOError as e:
                flash(f"Error saving document to server: {e}", "error")

    elif action == 'seed_next':
        next_phase_id = phase_id + 1
        next_phase_config = get_phase_config(next_phase_id)
        if not next_phase_config:
            flash(f"Cannot seed: Next phase ({next_phase_id}) is not configured.", "error")
        elif not updated_current_phase_data_for_ai: # This is data from current phase
            flash("Cannot seed: No data in current phase to use as source.", "warning")
        else:
            next_phase_field_keys = list(next_phase_config.fields.keys())
            if not next_phase_field_keys:
                flash(f"Cannot seed: Next phase ({next_phase_id}) has no fields configured.", "warning")
            else:
                seeded_data_for_next = seed_next_phase_data(json.dumps(updated_current_phase_data_for_ai), next_phase_field_keys)
                # Save seeded data to the database for the next phase
                update_current_phase_data_db(project.id, next_phase_id, seeded_data_for_next)
                flash(f"Phase {next_phase_id} has been seeded with data from Phase {phase_id} and saved to database!", "info")
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

# --- Error Handlers ---
@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    # note that we set the 500 status explicitly
    return render_template('errors/500.html'), 500

@app.errorhandler(Exception)
def handle_exception(e):
    # Pass through HTTP errors
    if isinstance(e, HTTPException):
        return e
    # Non-HTTP exceptions are handled here
    # You could log the error e here if you have logging configured
    print(f"Unhandled exception: {e}") # Basic logging to console
    return render_template('errors/500.html', e=e), 500

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
