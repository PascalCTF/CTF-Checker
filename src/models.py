from datetime import datetime
from app import db

class Checker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    script_path = db.Column(db.String(255), nullable=False)
    expected_flag = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    last_run = db.Column(db.DateTime)
    last_status = db.Column(db.String(20), default='pending')  # pending, success, failure, error
    
    # Relationship to execution results
    executions = db.relationship('CheckerExecution', backref='checker', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Checker {self.name}>'

class CheckerExecution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    executed_at = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(20), nullable=False)  # success, failure, error
    output = db.Column(db.Text)
    error_message = db.Column(db.Text)
    execution_time = db.Column(db.Float)  # in seconds
    flag_found = db.Column(db.String(255))
    
    # Foreign key to checker
    checker_id = db.Column(db.Integer, db.ForeignKey('checker.id'), nullable=False)
    
    def __repr__(self):
        return f'<CheckerExecution {self.id} - {self.status}>'
