import os
import subprocess
import time
import logging
from datetime import datetime
from app import app, db
from models import Checker, CheckerExecution, ServerState

CHECKER_TIMEOUT = 30

def run_checker(checker):
    """Execute a single checker script and return the result"""
    start_time = time.time()
    
    try:
        dependencies = checker.get_dependencies()
        if dependencies:
            subprocess.run(['pip', 'install', *dependencies], check=True)

        env = os.environ.copy()
        env.update(checker.get_env_variables())
        
        result = subprocess.run(
            ['python3', checker.script_path],
            capture_output=True,
            text=True,
            env=env,
            timeout=CHECKER_TIMEOUT
        )
        
        execution_time = time.time() - start_time
        
        output = result.stdout
        error_output = result.stderr
        
        flag_found = None
        status = 'failure'
        
        if result.returncode == 0:
            if checker.expected_flag in output:
                flag_found = checker.expected_flag
                status = 'success'
            else:
                import re
                flag_pattern = os.getenv('FLAG_FORMAT', 'pascalCTF') + r'\{[^}]+\}'
                flags = re.findall(flag_pattern, output, re.IGNORECASE)
                if flags:
                    flag_found = flags[0]
                    if flag_found.lower() == checker.expected_flag.lower():
                        status = 'success'
        
        execution = CheckerExecution(
            checker_id=checker.id,
            status=status,
            output=output[:1000],
            error_message=error_output[:1000] if error_output else None,
            execution_time=execution_time,
            flag_found=flag_found
        )
            
        return execution
            
    except subprocess.TimeoutExpired as e:
        execution_time = time.time() - start_time
        execution = CheckerExecution(
            checker_id=checker.id,
            status='error',
            output=None,
            error_message=f"Checker timed out after {CHECKER_TIMEOUT} seconds",
            execution_time=execution_time,
            flag_found=None
        )
        return execution
        
    except Exception as e:
        execution_time = time.time() - start_time
        execution = CheckerExecution(
            checker_id=checker.id,
            status='error',
            output=None,
            error_message=str(e),
            execution_time=execution_time,
            flag_found=None
        )
        return execution

def run_all_active_checkers():
    """Run all active checkers and store results"""
    with app.app_context():
        try:
            last_run_time_state = ServerState.query.filter_by(key='last_run_time').first()
            if last_run_time_state:
                last_run_time_state.value = datetime.now().isoformat()
                db.session.commit()

            active_checkers = Checker.query.filter_by(is_active=True).all()
            
            logging.info(f"Running {len(active_checkers)} active checkers")
            
            for checker in active_checkers:
                try:
                    if not os.path.exists(checker.script_path):
                        logging.error(f"Script file not found for checker {checker.name}: {checker.script_path}")
                        continue
                    
                    execution = run_checker(checker)
                    
                    checker.last_run = datetime.now()
                    checker.last_status = execution.status
                    
                    db.session.add(execution)
                    db.session.commit()
                    
                    logging.info(f"Checker '{checker.name}' executed with status: {execution.status}")
                    
                except Exception as e:
                    logging.error(f"Error running checker '{checker.name}': {e}")
                    
                    error_execution = CheckerExecution(
                        checker_id=checker.id,
                        status='error',
                        output=None,
                        error_message=str(e),
                        execution_time=0,
                        flag_found=None
                    )
                    
                    checker.last_run = datetime.now()
                    checker.last_status = 'error'
                    
                    db.session.add(error_execution)
                    db.session.commit()
            
            cleanup_old_executions()
            
        except Exception as e:
            logging.error(f"Error in run_all_active_checkers: {e}")
            db.session.rollback()

def get_last_run_time():
    """Return the last time the checkers were run"""
    with app.app_context():
        last_run_time_state = ServerState.query.filter_by(key='last_run_time').first()
        if last_run_time_state and last_run_time_state.value:
            return datetime.fromisoformat(last_run_time_state.value)
        return None


def cleanup_old_executions():
    """Remove old execution records to prevent database bloat"""
    try:
        checkers = Checker.query.all()
        
        for checker in checkers:
            old_executions = CheckerExecution.query.filter_by(
                checker_id=checker.id
            ).order_by(CheckerExecution.executed_at.desc()).offset(100).all()
            
            for execution in old_executions:
                db.session.delete(execution)
        
        db.session.commit()
        
    except Exception as e:
        logging.error(f"Error cleaning up old executions: {e}")
        db.session.rollback()
