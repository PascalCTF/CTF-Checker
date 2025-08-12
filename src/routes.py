import os
import re
import uuid
import importlib
import zipfile
import json
from flask import render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from app import app, db
from models import Checker, CheckerExecution
import logging
from checker_runner import get_last_run_time

def find_dependencies(script_content):
    imports = re.findall(r'^(?:from|import)\s+([a-zA-Z0-9_]+)', script_content, re.MULTILINE)
    dependencies = []

    for imp in imports:
        try:
            importlib.import_module(imp)
        except:
            dependencies.append(imp)

    return list(set(dependencies))

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    checkers = Checker.query.order_by(Checker.created_at.desc()).all()
    
    for checker in checkers:
        checker.recent_executions = CheckerExecution.query.filter_by(
            checker_id=checker.id
        ).order_by(CheckerExecution.executed_at.desc()).limit(10).all()
    
    return render_template('dashboard.html', checkers=checkers)


@app.route('/add_bulk_checkers', methods=['GET', 'POST'])
def add_bulk_checkers():
    if request.method == 'POST':
        if 'zip_file' not in request.files:
            flash('No ZIP file uploaded.', 'error')
            return render_template('add_bulk_checkers.html')

        file = request.files['zip_file']
        if file.filename == '':
            flash('No ZIP file selected.', 'error')
            return render_template('add_bulk_checkers.html')

        if file and file.filename.endswith('.zip'):
            zip_filename = secure_filename(file.filename)
            zip_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)
            file.save(zip_path)

            extract_folder = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename.replace('.zip', ''))
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_folder)

            added_count = 0
            for item in os.listdir(extract_folder):
                item_path = os.path.join(extract_folder, item)
                if os.path.isdir(item_path):
                    metadata_path = os.path.join(item_path, 'metadata.json')
                    script_path = None
                    for file_in_dir in os.listdir(item_path):
                        if file_in_dir.endswith('.py'):
                            script_path = os.path.join(item_path, file_in_dir)
                            break
                    
                    if os.path.exists(metadata_path) and script_path:
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                        
                        name = metadata.get('name')
                        expected_flag = metadata.get('expected_flag')
                        env_vars = metadata.get('env_variables', {})

                        if name and expected_flag:
                            new_filename = f"{uuid.uuid4()}.py"
                            new_script_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
                            os.rename(script_path, new_script_path)

                            with open(new_script_path, 'r') as f:
                                script_content = f.read()
                            
                            dependencies = find_dependencies(script_content)

                            checker = Checker(
                                name=name,
                                script_path=new_script_path,
                                expected_flag=expected_flag
                            )
                            checker.set_env_variables(env_vars)
                            checker.set_dependencies(dependencies)
                            db.session.add(checker)
                            added_count += 1

            if added_count > 0:
                db.session.commit()
                flash(f'{added_count} checkers added successfully!', 'success')
            else:
                flash('No valid checkers found in the ZIP file.', 'warning')

            return redirect(url_for('dashboard'))
        else:
            flash('Only ZIP (.zip) files are allowed.', 'error')

    return render_template('add_bulk_checkers.html')


@app.route('/add_checker', methods=['GET', 'POST'])
def add_checker():
    if request.method == 'POST':
        name = request.form['name']
        expected_flag = request.form['expected_flag']
        
        env_vars = {}
        for key, value in request.form.items():
            if key.startswith('env_key_') and value.strip():
                index = key.replace('env_key_', '')
                env_value = request.form.get(f'env_value_{index}', '').strip()
                if env_value:
                    env_vars[value.strip()] = env_value
        
        if 'script_file' not in request.files:
            flash('No script file uploaded.', 'error')
            return render_template('add_checker.html')
        
        file = request.files['script_file']
        if file.filename == '':
            flash('No script file selected.', 'error')
            return render_template('add_checker.html')
        
        if file and file.filename.endswith('.py'):
            filename = secure_filename(f"{uuid.uuid4()}.py")
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            file.seek(0)
            script_content = file.read().decode('utf-8')
            dependencies = find_dependencies(script_content)
            
            checker = Checker(
                name=name,
                script_path=file_path,
                expected_flag=expected_flag
            )
            checker.set_env_variables(env_vars)
            checker.set_dependencies(dependencies)
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
    
    try:
        if os.path.exists(checker.script_path):
            os.remove(checker.script_path)
    except Exception as e:
        logging.error(f"Error deleting script file: {e}")
    
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
            'error_message': recent_execution.error_message if recent_execution else None,
            'env_variables': checker.get_env_variables()
        })
    
    last_run_time = get_last_run_time()
    
    return jsonify({
        'checkers': status_data,
        'server_time': last_run_time.isoformat() if last_run_time else None
    })

@app.route('/checker_details/<int:checker_id>', methods=['GET', 'POST'])
def checker_details(checker_id):
    checker = Checker.query.get_or_404(checker_id)
    
    if request.method == 'POST':
        checker.name = request.form['name']
        checker.expected_flag = request.form['expected_flag']
        checker.is_active = 'is_active' in request.form
        
        env_vars = {}
        for key, value in request.form.items():
            if key.startswith('env_key_'):
                index = key.split('_')[-1]
                env_key = value.strip()
                env_value = request.form.get(f'env_value_{index}', '').strip()
                if env_key and env_value:
                    env_vars[env_key] = env_value
        
        checker.set_env_variables(env_vars)
        
        if 'script_file' in request.files and request.files['script_file'].filename:
            script_file = request.files['script_file']
            if script_file and script_file.filename.endswith('.py'):
                try:
                    if os.path.exists(checker.script_path):
                        os.remove(checker.script_path)
                except OSError:
                    pass
                
                filename = secure_filename(f"{uuid.uuid4().hex}.py")
                script_path = os.path.join('uploads', filename)
                script_file.save(script_path)
                checker.script_path = script_path
                
                script_file.seek(0)
                script_content = script_file.read().decode('utf-8')
                dependencies = find_dependencies(script_content)
                checker.set_dependencies(dependencies)
        
        db.session.commit()
        flash(f'Checker "{checker.name}" updated successfully.', 'success')
        return redirect(url_for('checker_details', checker_id=checker_id))
    
    # Get execution history
    executions = CheckerExecution.query.filter_by(
        checker_id=checker_id
    ).order_by(CheckerExecution.executed_at.desc()).limit(50).all()
    
    return render_template('checker_details.html', checker=checker, executions=executions)

@app.route('/api/execution_details/<int:execution_id>')
def execution_details_api(execution_id):
    """API endpoint for execution details"""
    execution = CheckerExecution.query.get_or_404(execution_id)
    
    return jsonify({
        'id': execution.id,
        'executed_at': execution.executed_at.isoformat(),
        'status': execution.status,
        'output': execution.output,
        'error_message': execution.error_message,
        'execution_time': execution.execution_time,
        'flag_found': execution.flag_found
    })

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
