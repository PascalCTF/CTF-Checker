import os
import uuid
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from app import app, db
from models import Checker, CheckerExecution
import logging

# Main routes
@app.route('/')
def index():
    return redirect(url_for('dashboard'))

# Dashboard routes
@app.route('/dashboard')
def dashboard():
    checkers = Checker.query.order_by(Checker.created_at.desc()).all()
    
    # Get recent executions for each checker
    for checker in checkers:
        checker.recent_executions = CheckerExecution.query.filter_by(
            checker_id=checker.id
        ).order_by(CheckerExecution.executed_at.desc()).limit(10).all()
    
    return render_template('dashboard.html', checkers=checkers)

@app.route('/add_checker', methods=['GET', 'POST'])
def add_checker():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        expected_flag = request.form['expected_flag']
        
        # Handle file upload
        if 'script_file' not in request.files:
            flash('No script file uploaded.', 'error')
            return render_template('add_checker.html')
        
        file = request.files['script_file']
        if file.filename == '':
            flash('No script file selected.', 'error')
            return render_template('add_checker.html')
        
        if file and file.filename.endswith('.py'):
            # Generate unique filename
            filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Create checker record
            checker = Checker(
                name=name,
                description=description,
                script_path=file_path,
                expected_flag=expected_flag
            )
            db.session.add(checker)
            db.session.commit()
            
            flash(f'Checker "{name}" added successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Only Python (.py) files are allowed.', 'error')
    
    return render_template('add_checker.html')

@app.route('/toggle_checker/<int:checker_id>')
def toggle_checker(checker_id):
    checker = Checker.query.get_or_404(checker_id)
    checker.is_active = not checker.is_active
    db.session.commit()
    
    status = 'activated' if checker.is_active else 'deactivated'
    flash(f'Checker "{checker.name}" {status}.', 'info')
    return redirect(url_for('dashboard'))

@app.route('/delete_checker/<int:checker_id>')
def delete_checker(checker_id):
    checker = Checker.query.get_or_404(checker_id)
    
    # Delete the script file
    try:
        if os.path.exists(checker.script_path):
            os.remove(checker.script_path)
    except Exception as e:
        logging.error(f"Error deleting script file: {e}")
    
    # Delete the checker (executions will be deleted due to cascade)
    db.session.delete(checker)
    db.session.commit()
    
    flash(f'Checker "{checker.name}" deleted successfully.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/api/checker_status')
def checker_status():
    """API endpoint to get real-time checker status"""
    checkers = Checker.query.all()
    
    status_data = []
    for checker in checkers:
        recent_execution = CheckerExecution.query.filter_by(
            checker_id=checker.id
        ).order_by(CheckerExecution.executed_at.desc()).first()
        
        status_data.append({
            'id': checker.id,
            'name': checker.name,
            'status': checker.last_status,
            'last_run': checker.last_run.isoformat() if checker.last_run else None,
            'is_active': checker.is_active,
            'recent_output': recent_execution.output if recent_execution else None,
            'error_message': recent_execution.error_message if recent_execution else None
        })
    
    return jsonify(status_data)

@app.route('/checker_details/<int:checker_id>')
def checker_details(checker_id):
    checker = Checker.query.get_or_404(checker_id)
    executions = CheckerExecution.query.filter_by(
        checker_id=checker_id
    ).order_by(CheckerExecution.executed_at.desc()).limit(50).all()
    
    return render_template('checker_details.html', checker=checker, executions=executions)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
