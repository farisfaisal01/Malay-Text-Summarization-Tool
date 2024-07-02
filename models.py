from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize SQLAlchemy
db = SQLAlchemy()

class User(db.Model):
    """Model for the user table."""
    __tablename__ = 'tbl_user'
    
    userID = db.Column(db.Integer, primary_key=True)
    userRole = db.Column(db.String(10), nullable=False)
    userName = db.Column(db.String(20), nullable=False, unique=True)
    userPassword = db.Column(db.String(20), nullable=False)
    userEmail = db.Column(db.String(50), nullable=False, unique=True)
    
    summaries = db.relationship('Summary', backref='user', lazy=True)

class Summary(db.Model):
    """Model for the summary table."""
    __tablename__ = 'tbl_summary'
    
    summaryID = db.Column(db.Integer, primary_key=True)
    userID = db.Column(db.Integer, db.ForeignKey('tbl_user.userID'), nullable=False)
    summaryContent = db.Column(db.Text, nullable=False)
    summaryDate = db.Column(db.Date, default=datetime.utcnow)
    kg_data = db.Column(db.Text, nullable=True)
    entities = db.Column(db.Text, nullable=True)

def init_db(app):
    """
    Initialize the database.
    
    Args:
    - app: The Flask application instance.
    """
    db.init_app(app)
    with app.app_context():
        db.create_all()
