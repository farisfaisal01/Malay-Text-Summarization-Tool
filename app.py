from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify
from flask_mysqldb import MySQL
import malaya
from malaya_summarizer_abstractive import cleaning
from malaya.text.vectorizer import SkipGramCountVectorizer
from sklearn.decomposition import TruncatedSVD
from malaya_summarizer_extractive import split_into_sentences
# from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from models import User, Summary, init_db
from flask_migrate import Migrate
from models import db
# from fpdf import FPDF
# import io
from werkzeug.utils import secure_filename
import os
import matplotlib
matplotlib.use('Agg')
import base64

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

app = Flask(__name__)
app.secret_key = "your-secret-key"

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

@app.route("/")
def home():
    if 'username' in session:
        return render_template('home.html', username=session['username'])
    return render_template('home.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT userName, userPassword, userRole, userID FROM tbl_user WHERE userName = %s", (username,))
        user = cur.fetchone()
        cur.close()

        if user and password == user[1]:
            session['username'] = user[0]
            session['userrole'] = user[2]
            session['userid'] = user[3]
            return redirect(url_for('home'))
        flash('nama pengguna atau kata laluan tidak sah')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO tbl_user (userName, userEmail, userPassword, userRole) VALUES (%s, %s, %s, 'user')", (username, email, password))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('userrole', None)
    session.pop('userid', None)
    return redirect(url_for('home'))

@app.route('/summarizer', methods=['GET', 'POST'])
def summarizer():
    if request.method == 'POST':
        rawtext = request.form['rawtext']
        summary_type = request.form.get('summary_type', 'abstractive')
        keyword = request.form.get('keyword', None)
        
        cleaned_text = cleaning(rawtext)
        
        word_scores = None
        kg_data = None  # Initialize the knowledge graph data variable
        
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
            word_scores = sorted(r['score'], key=lambda item: item[1], reverse=True)[:20]
        
        # Generate the knowledge graph
        kg_result = kg_model.generate([summary_text], max_length=256)  # Adjusted to generate two graphs for demonstration
        kg_data = generate_knowledge_graph_images(kg_result)

        if 'username' in session:
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO tbl_summary (userID, summaryContent, summaryDate) VALUES (%s, %s, %s)",
                        (session['userid'], summary_text, datetime.utcnow()))
            mysql.connection.commit()
            cur.close()
            return render_template('summarizer.html', username=session['username'], text=rawtext, summary=summary_text, word_scores=word_scores, kg_data=kg_data)
        else:
            return render_template('summarizer.html', text=rawtext, summary=summary_text, word_scores=word_scores, kg_data=kg_data)
    elif 'username' in session:
        return render_template('summarizer.html', username=session['username'])
    else:
        return render_template('summarizer.html')

@app.route('/history')
def history():
    if 'username' in session:
        if session['userrole'] == 'admin':
            users = User.query.all()
            return render_template('history-selectprofile.html', users=users)
        else:
            summaries = Summary.query.filter_by(userID=session['userid']).all()
            return render_template('history-selectsummary.html', summaries=summaries)
    flash('Anda perlu log masuk untuk mengakses halaman ini.')
    return redirect(url_for('login'))

@app.route('/history/user/<int:user_id>')
def history_user(user_id):
    if 'username' in session and session['userrole'] == 'admin':
        summaries = Summary.query.filter_by(userID=user_id).all()
        return render_template('history-selectsummary.html', summaries=summaries)
    flash('Anda tidak mempunyai kebenaran yang diperlukan untuk mengakses halaman ini.')
    return redirect(url_for('login'))

@app.route('/history/summary/<int:summary_id>')
def history_summary(summary_id):
    if 'username' in session:
        summary = Summary.query.get(summary_id)
        if summary and (summary.userID == session['userid'] or session['userrole'] == 'admin'):
            return render_template('history-summary.html', summary=summary)
    flash('Anda tidak mempunyai kebenaran yang diperlukan untuk mengakses halaman ini.')
    return redirect(url_for('login'))

@app.route("/accountsettings", methods=['GET', 'POST'])
def account_settings():
    if 'username' in session:
        if request.method == 'POST':
            email = request.form['email']
            old_password = request.form['old_password']
            new_password = request.form['new_password']
            confirm_new_password = request.form['confirm_new_password']

            # Fetch the user's current email from the database
            cur = mysql.connection.cursor()
            cur.execute("SELECT userEmail, userPassword FROM tbl_user WHERE userName = %s", (session['username'],))
            user = cur.fetchone()
            cur.close()

            # Check if the old password matches the password in the database
            if old_password != user[1]:
                flash('Kata laluan lama yang salah')
                return redirect(url_for('account_settings'))

            # If the user entered a new email, update it in the database
            if email != user[0]:
                cur = mysql.connection.cursor()
                cur.execute("UPDATE tbl_user SET userEmail = %s WHERE userName = %s", (email, session['username']))
                mysql.connection.commit()
                cur.close()
                flash('E-mel berjaya dikemas kini')

            # If the user entered a new password, update it in the database
            if new_password:
                if new_password != confirm_new_password:
                    flash('Kata laluan tidak sepadan')
                    return redirect(url_for('account_settings'))
                cur = mysql.connection.cursor()
                cur.execute("UPDATE tbl_user SET userPassword = %s WHERE userName = %s", (new_password, session['username']))
                mysql.connection.commit()
                cur.close()
                flash('Kata laluan berjaya dikemas kini')

            flash('Tetapan akaun berjaya dikemas kini')
            return redirect(url_for('account_settings'))
        return render_template('accountsettings.html', user=session['username'])
    else:
        return redirect(url_for('login'))

@app.route('/export')
def export():
    format = request.args.get('format')
    text = request.args.get('text')
    date = request.args.get('date')

    export_funcs = {
        'pdf': export_pdf,
        'word': export_word,
        'txt': export_txt
    }

    if format in export_funcs:
        return export_funcs[format](text, date)
    else:
        return "Invalid format", 400

@app.route('/upload_file', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'})

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        text = extract_text_from_file(file_path)
        
        os.remove(file_path)  # Clean up the file after processing

        return jsonify({'success': True, 'text': text})
    return jsonify({'success': False, 'message': 'Invalid file format'})

if __name__ == "__main__":
    app.run(debug=True)