from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file, make_response
from flask_mysqldb import MySQL
import malaya
from malaya_summarizer_abstractive import cleaning
from malaya.text.vectorizer import SkipGramCountVectorizer
from sklearn.decomposition import TruncatedSVD
from malaya_summarizer_extractive import split_into_sentences
from datetime import datetime
from models import User, Summary, init_db
from flask_migrate import Migrate
from models import db
from werkzeug.utils import secure_filename
import os
import matplotlib
import json
import base64
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import utils
from docx import Document
from docx.shared import Inches

matplotlib.use('Agg')

# Import the separated functions
from export_pdf_word_txt import export_pdf, export_word, export_txt
from upload_file import allowed_file, extract_text_from_file
from summarization_text_to_kg import generate_knowledge_graph_images

# Initialize the extractive summarization model
stopwords = malaya.text.function.get_stopwords()
vectorizer = SkipGramCountVectorizer(
    max_df=0.95,
    min_df=1,
    ngram_range=(1, 3),
    stop_words=stopwords,
    skip=2
)
svd = TruncatedSVD(n_components=30)
extractive_model = malaya.summarization.extractive.sklearn(svd, vectorizer)

# Initialize the abstractive summarization model
abstractive_model = malaya.summarization.abstractive.huggingface()
model_base = malaya.summarization.abstractive.huggingface(model='mesolitica/finetune-summarization-t5-base-standard-bahasa-cased')

# Load the knowledge graph model
kg_model = malaya.knowledge_graph.huggingface()

# Import the general entity model from Malaya
entity_model = malaya.entity.general_entity()

# Initialize the Flask application
app = Flask(__name__)
app.secret_key = "your-secret-key"

# SQLAlchemy Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@127.0.0.1/malay_text_summarizer'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
init_db(app)
migrate = Migrate(app, db)

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'malay_text_summarizer'
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

mysql = MySQL(app)

# Define the home route
@app.route("/")
def home():
    if 'username' in session:
        return render_template('home.html', username=session['username'])
    return render_template('home.html')

# Define the login route
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT userName, userPassword, userRole, userID FROM tbl_user WHERE userName = %s OR userEmail = %s", (username_or_email, username_or_email))
        user = cur.fetchone()
        cur.close()

        if user:
            db_username = user[0]
            db_password = user[1]
            if password == db_password:
                session['username'] = db_username
                session['userrole'] = user[2]
                session['userid'] = user[3]
                return redirect(url_for('home'))
            else:
                flash('Kata laluan tidak sah. Sila cuba lagi.', 'error')
        else:
            flash('Nama pengguna atau e-mel tidak sah. Sila cuba lagi.', 'error')

    return render_template('login.html')

# Define the register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check if username already exists
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM tbl_user WHERE userName = %s", (username,))
        user_by_username = cur.fetchone()

        # Check if email already exists
        cur.execute("SELECT * FROM tbl_user WHERE userEmail = %s", (email,))
        user_by_email = cur.fetchone()
        cur.close()

        if user_by_username:
            flash('Nama pengguna sudah wujud. Sila gunakan yang lain.', 'error')
            return redirect(url_for('register'))

        if user_by_email:
            flash('E-mel sudah wujud. Sila gunakan yang lain.', 'error')
            return redirect(url_for('register'))

        # Check if the password meets the requirements
        if len(password) < 8 or not any(char.isdigit() for char in password) or not any(char.isalpha() for char in password):
            flash('Kata laluan mestilah sekurang-kurangnya 8 aksara dan mengandungi huruf dan nombor.', 'error')
            return redirect(url_for('register'))

        # Insert new user into the database
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO tbl_user (userName, userEmail, userPassword, userRole) VALUES (%s, %s, %s, 'user')", 
                    (username, email, password))
        mysql.connection.commit()
        cur.close()

        flash('Pendaftaran berjaya. Sila log masuk.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Define the logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('userrole', None)
    session.pop('userid', None)
    return redirect(url_for('home'))

# Define the summarizer route
@app.route('/summarizer', methods=['GET', 'POST'])
def summarizer():
    if request.method == 'POST':
        rawtext = request.form['rawtext']
        summary_type = request.form.get('summary_type', 'abstractive')
        keyword = request.form.get('keyword', None)
        
        cleaned_text = cleaning(rawtext)
        
        kg_data = None
        entities = None
        
        if summary_type == 'abstractive':
            summary = abstractive_model.generate([cleaned_text], max_length=256, temperature=0.5)
            summary_text = summary[0]
        else:
            sentences = split_into_sentences(cleaned_text)
            if keyword:
                r = extractive_model.sentence_level(sentences, isi_penting=keyword)
            else:
                r = extractive_model.sentence_level(sentences)
            summary_text = r['summary']
        
        kg_result = kg_model.generate([summary_text], max_length=256)
        kg_data = generate_knowledge_graph_images(kg_result)
        
        entities = entity_model.predict(summary_text)
        
        kg_data_str = json.dumps(kg_data)
        entities_str = json.dumps(entities)

        if 'username' in session:
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO tbl_summary (userID, summaryContent, summaryDate, kg_data, entities) VALUES (%s, %s, %s, %s, %s)",
                        (session['userid'], summary_text, datetime.utcnow(), kg_data_str, entities_str))
            mysql.connection.commit()
            cur.close()
            return render_template('summarizer.html', username=session['username'], text=rawtext, summary=summary_text, kg_data=kg_data, entities=entities)
        else:
            return render_template('summarizer.html', text=rawtext, summary=summary_text, kg_data=kg_data, entities=entities)
    elif 'username' in session:
        return render_template('summarizer.html', username=session['username'])
    else:
        return render_template('summarizer.html')

# Define the history route
@app.route('/history')
def history():
    if 'username' in session:
        if session['userrole'] == 'admin':
            users = User.query.all()
            return render_template('history-selectprofile.html', users=users)
        else:
            summaries = Summary.query.filter_by(userID=session['userid']).all()
            return render_template('history-selectsummary.html', summaries=summaries)
    flash('Anda perlu log masuk untuk mengakses halaman ini.', 'error')
    return redirect(url_for('login'))

# Define the history for specific user route
@app.route('/history/user/<int:user_id>')
def history_user(user_id):
    if 'username' in session and session['userrole'] == 'admin':
        summaries = Summary.query.filter_by(userID=user_id).all()
        return render_template('history-selectsummary.html', summaries=summaries)
    flash('Anda tidak mempunyai kebenaran yang diperlukan untuk mengakses halaman ini.', 'error')
    return redirect(url_for('login'))

# Define the history for specific summary route
@app.route('/history/summary/<int:summary_id>')
def history_summary(summary_id):
    if 'username' in session:
        summary = Summary.query.get(summary_id)
        if summary and (summary.userID == session['userid'] or session['userrole'] == 'admin'):
            kg_data = json.loads(summary.kg_data)
            entities = json.loads(summary.entities)
            return render_template('history-summary.html', summary=summary, kg_data=kg_data, entities=entities)
    flash('Anda tidak mempunyai kebenaran yang diperlukan untuk mengakses halaman ini.', 'error')
    return redirect(url_for('login'))

# Define the account settings route
@app.route("/accountsettings", methods=['GET', 'POST'])
def account_settings():
    if 'username' in session:
        if request.method == 'POST':
            new_username = request.form.get('username')
            email = request.form['email']
            old_password = request.form['old_password']
            new_password = request.form['new_password']
            confirm_new_password = request.form['confirm_new_password']

            # Retrieve user details from database
            cur = mysql.connection.cursor()
            cur.execute("SELECT userEmail, userPassword, userName FROM tbl_user WHERE userName = %s", (session['username'],))
            user = cur.fetchone()
            cur.close()

            # Validate old password
            if old_password != user[1]:
                flash('Kata laluan lama yang salah', 'error')
                return redirect(url_for('account_settings'))

            # Check if email is changing and if it's already in use
            if email and email != user[0]:
                cur = mysql.connection.cursor()
                cur.execute("SELECT * FROM tbl_user WHERE userEmail = %s", (email,))
                existing_user = cur.fetchone()
                cur.close()
                if existing_user:
                    flash('E-mel sudah wujud. Sila gunakan yang lain.', 'error')
                    return redirect(url_for('account_settings'))
                cur = mysql.connection.cursor()
                cur.execute("UPDATE tbl_user SET userEmail = %s WHERE userName = %s", (email, session['username']))
                mysql.connection.commit()
                cur.close()
                flash('E-mel berjaya dikemas kini', 'success')

            # Check if username is changing and if it's already in use
            if new_username and new_username != user[2]:
                cur = mysql.connection.cursor()
                cur.execute("SELECT * FROM tbl_user WHERE userName = %s", (new_username,))
                existing_user = cur.fetchone()
                cur.close()
                if existing_user:
                    flash('Nama pengguna sudah wujud. Sila gunakan yang lain.', 'error')
                    return redirect(url_for('account_settings'))
                cur = mysql.connection.cursor()
                cur.execute("UPDATE tbl_user SET userName = %s WHERE userName = %s", (new_username, session['username']))
                mysql.connection.commit()
                cur.close()
                session['username'] = new_username
                flash('Nama pengguna berjaya dikemas kini', 'success')

            # Check if new password is provided and meets the requirements
            if new_password:
                if new_password != confirm_new_password:
                    flash('Kata laluan tidak sepadan. Sila masukkan semula.', 'error')
                    return redirect(url_for('account_settings'))
                elif len(new_password) < 8 or not any(char.isdigit() for char in new_password) or not any(char.isalpha() for char in new_password):
                    flash('Kata laluan mestilah sekurang-kurangnya 8 aksara dan mengandungi huruf dan nombor.', 'error')
                    return redirect(url_for('account_settings'))
                
                # Update password if everything is correct
                cur = mysql.connection.cursor()
                cur.execute("UPDATE tbl_user SET userPassword = %s WHERE userName = %s", (new_password, session['username']))
                mysql.connection.commit()
                cur.close()
                flash('Kata Laluan berjaya dikemas kini', 'success')

            # Redirect to account settings page
            return redirect(url_for('account_settings'))

        # Handle GET request for account settings page
        # Retrieve current user details to pre-fill the form
        cur = mysql.connection.cursor()
        cur.execute("SELECT userEmail, userName FROM tbl_user WHERE userName = %s", (session['username'],))
        user = cur.fetchone()
        cur.close()
        return render_template('accountsettings.html', user=session['username'], email=user[0])

    # Redirect to login if not logged in
    return redirect(url_for('login'))

# Define the export route
@app.route('/export')
def export():
    format = request.args.get('format')
    text = request.args.get('text')
    date = request.args.get('date')
    kg_data = request.args.get('kg_data')
    entities = request.args.get('entities')

    export_funcs = {
        'pdf': export_pdf,
        'word': export_word,
        'txt': export_txt
    }

    if format in export_funcs:
        return export_funcs[format](text, date, kg_data, entities)
    else:
        return "Invalid format", 400

# Define the file upload route
@app.route('/upload_file', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'Tiada bahagian fail'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Tiada fail dipilih'})

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        text = extract_text_from_file(file_path)
        
        os.remove(file_path)  # Clean up the file after processing

        return jsonify({'success': True, 'text': text})
    return jsonify({'success': False, 'message': 'Format fail tidak sah'})

# Run the application
if __name__ == "__main__":
    app.run(debug=True)