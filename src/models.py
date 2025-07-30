from datetime import datetime
from app import db
import json

class Checker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    script_path = db.Column(db.String(255), nullable=False)
    expected_flag = db.Column(db.String(255), nullable=False)
    env_variables = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    last_run = db.Column(db.DateTime)
    last_status = db.Column(db.String(20), default='pending')
    dependencies = db.Column(db.Text)
    
    executions = db.relationship('CheckerExecution', backref='checker', lazy=True, cascade='all, delete-orphan')
    
    def get_dependencies(self):
        """Get dependencies as a list"""
        if self.dependencies:
            try:
                return json.loads(self.dependencies)
            except json.JSONDecodeError:
                return []
        return []

    def set_dependencies(self, dependencies_list):
        """Set dependencies from a list"""
        self.dependencies = json.dumps(dependencies_list) if dependencies_list else None

    def get_env_variables(self):
        """Get environment variables as a dictionary"""
        if self.env_variables:
            try:
                return json.loads(self.env_variables)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_env_variables(self, env_dict):
        """Set environment variables from a dictionary"""
        self.env_variables = json.dumps(env_dict) if env_dict else None
    
    def __repr__(self):
        return f'<Checker {self.name}>'

class CheckerExecution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    executed_at = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(20), nullable=False)
    output = db.Column(db.Text)
    error_message = db.Column(db.Text)
    execution_time = db.Column(db.Float)
    flag_found = db.Column(db.String(255))
    
    checker_id = db.Column(db.Integer, db.ForeignKey('checker.id'), nullable=False)
    
    def __repr__(self):
        return f'<CheckerExecution {self.id} - {self.status}>'

class ServerState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(255))

    def __repr__(self):
        return f'<ServerState {self.key}>'
