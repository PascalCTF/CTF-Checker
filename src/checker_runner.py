import os
import subprocess
import time
import logging
import tempfile
from datetime import datetime
from app import app, db
from models import Checker, CheckerExecution

# Timeout for checker execution (in seconds)
CHECKER_TIMEOUT = 30

def run_checker(checker):
    """Execute a single checker script and return the result"""
    start_time = time.time()
    
    try:
        # Prepare the environment for the checker
        env = os.environ.copy()
        
        # Create a temporary directory for checker execution
        with tempfile.TemporaryDirectory() as temp_dir:
            # Run the checker script with timeout
            result = subprocess.run(
                ['python3', checker.script_path],
                capture_output=True,
                text=True,
                cwd=temp_dir,
                env=env,
                timeout=CHECKER_TIMEOUT
            )
            
            execution_time = time.time() - start_time
            
            # Parse the output to find the flag
            output = result.stdout
            error_output = result.stderr
            
            # Look for the expected flag in the output
            flag_found = None
            status = 'failure'
            
            if result.returncode == 0:
                # Check if the expected flag is in the output
                if checker.expected_flag in output:
                    flag_found = checker.expected_flag
                    status = 'success'
                else:
                    # Try to extract any flag-like pattern from output
                    import re
                    flag_pattern = r'flag\{[^}]+\}'
                    flags = re.findall(flag_pattern, output, re.IGNORECASE)
                    if flags:
                        flag_found = flags[0]
                        if flag_found.lower() == checker.expected_flag.lower():
                            status = 'success'
            
            # Create execution record
            execution = CheckerExecution(
                checker_id=checker.id,
                status=status,
                output=output[:1000],  # Limit output length
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
            active_checkers = Checker.query.filter_by(is_active=True).all()
            
            logging.info(f"Running {len(active_checkers)} active checkers")
            
            for checker in active_checkers:
                try:
                    # Skip if script file doesn't exist
                    if not os.path.exists(checker.script_path):
                        logging.error(f"Script file not found for checker {checker.name}: {checker.script_path}")
                        continue
                    
                    # Run the checker
                    execution = run_checker(checker)
                    
                    # Update checker status
                    checker.last_run = datetime.now()
                    checker.last_status = execution.status
                    
                    # Save execution result
                    db.session.add(execution)
                    db.session.commit()
                    
                    logging.info(f"Checker '{checker.name}' executed with status: {execution.status}")
                    
                except Exception as e:
                    logging.error(f"Error running checker '{checker.name}': {e}")
                    
                    # Create error execution record
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
            
            # Clean up old execution records (keep only last 100 per checker)
            cleanup_old_executions()
            
        except Exception as e:
            logging.error(f"Error in run_all_active_checkers: {e}")
            db.session.rollback()

def cleanup_old_executions():
    """Remove old execution records to prevent database bloat"""
    try:
        checkers = Checker.query.all()
        
        for checker in checkers:
            # Keep only the latest 100 executions per checker
            old_executions = CheckerExecution.query.filter_by(
                checker_id=checker.id
            ).order_by(CheckerExecution.executed_at.desc()).offset(100).all()
            
            for execution in old_executions:
                db.session.delete(execution)
        
        db.session.commit()
        
    except Exception as e:
        logging.error(f"Error cleaning up old executions: {e}")
        db.session.rollback()
