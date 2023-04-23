from flask import Flask, make_response, request, jsonify, render_template, redirect, url_for, session, send_file
import datetime
from flask_sqlalchemy import SQLAlchemy
import requests
import os, json
from cohere import Client
from werkzeug.security import check_password_hash, generate_password_hash
from genpdf import generate_pdfs
import hashlib
from processInp import get_text_from_wikipedia, get_text_from_youtube
from coheretest import gen_fib, gen_mcqs, gen_tf
app = Flask(__name__)
# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///questions.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.config['SECRET_KEY'] = os.urandom(24)


# ------------------------ DB MODELS -----------------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=True)
    email = db.Column(db.String, nullable=False)
    school_name = db.Column(db.String, nullable=True)
    degree = db.Column(db.String, nullable=True)
    major = db.Column(db.String, nullable=True)
    year = db.Column(db.String, nullable=True)
    points = db.Column(db.Integer, default=0)
    worksheets = db.relationship('Worksheet', back_populates='user')
    friends = db.relationship('Friend', foreign_keys='Friend.user_id', back_populates='user')

class Friend(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', foreign_keys=[user_id], back_populates='friends')
    friend = db.relationship('User', foreign_keys=[friend_id])

class Worksheet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', back_populates='worksheets')
    title = db.Column(db.String(120), nullable=False)
    questions = db.relationship('Question', back_populates='worksheet', cascade="all,delete")
    question_pdf = db.Column(db.String(120), nullable=True)
    answer_pdf = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    worksheet_id = db.Column(db.Integer, db.ForeignKey('worksheet.id'))
    worksheet = db.relationship('Worksheet', back_populates='questions')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User')
    question_type = db.Column(db.Enum('mcq', 'tf', 'fib'), nullable=False)
    question = db.Column(db.String, nullable=False)
    correct_answer = db.Column(db.String)
    incorrect_answers = db.Column(db.String)  # Store incorrect answers as a JSON-encoded string
    is_true = db.Column(db.Boolean)

with app.app_context():
    db.create_all()


# -------------------------   USER MANAGEMENT ------------------------------------------

def get_logged_in_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

@app.route('/')
def home():
    user = get_logged_in_user()
    print(user)
    if not user:
        return redirect(url_for('login'))
    return redirect(url_for('conversion_methods'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    user = get_logged_in_user()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the user exists in the database
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('conversion_methods'))
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html',user=user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form.get('last_name', None)
        email = request.form['email']
        school_name = request.form.get('school_name', None)
        degree = request.form.get('degree', None)
        major = request.form.get('major', None)
        year = request.form.get('year', None)

        # Check if the user already exists
        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            return render_template('register.html', error="Username already exists")

        # Create a new user and add to the database
        user = User(username=username, password=generate_password_hash(password),
                    first_name=first_name, last_name=last_name, email=email,
                    school_name=school_name, degree=degree, major=major, year=year)        
        db.session.add(user)
        db.session.commit()

        session['user_id'] = user.id
        return redirect(url_for('conversion_methods'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/search_users', methods=['GET'])
def search_users():
    search = request.args.get('search')
    user = get_logged_in_user()
    if not user:
        return redirect(url_for('login'))

    if search:
        # Search for users in the database
        results = User.query.filter(User.username.contains(search)).all()
    else:
        results = []

    return render_template('search_users.html', user=user, results=results)

@app.route('/add_friend/<int:friend_id>', methods=['POST'])
def add_friend(friend_id):
    user = get_logged_in_user()
    if not user:
        return redirect(url_for('login'))

    # Check if the friendship already exists
    existing_friendship = Friend.query.filter_by(user_id=user.id, friend_id=friend_id).first()

    if not existing_friendship:
        # Add friendship in both directions
        friend = Friend(user_id=user.id, friend_id=friend_id)
        db.session.add(friend)
        friend2 = Friend(user_id=friend_id, friend_id=user.id)
        db.session.add(friend2)
        db.session.commit()

    return redirect(url_for('profile'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    user = get_logged_in_user()
    print(user)

    if not user:
        return redirect(url_for('login'))

    friends = User.query.join(Friend, User.id == Friend.friend_id).filter(Friend.user_id == user.id).all()

    if request.method == 'POST':
        search_query = request.form['search_query']
        results = User.query.filter(User.username.ilike(f"%{search_query}%")).all()
        return render_template('profile.html', user=user, friends=friends, results=results)
    return render_template('profile.html', user=user, friends=friends)

# ------------------------------------------- Worksheet -----------------------------

@app.route('/conversion_methods')
def conversion_methods():
    user = get_logged_in_user()
    if not user:
        return redirect(url_for('login'))

    return render_template('conversion_methods.html', user = user)

@app.route('/create_worksheet/text', methods=['GET', 'POST'])
def create_worksheet_text():
    user = get_logged_in_user()
    if not user:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        input_text = request.form['input-text']
        w_title = str(request.form['w-title'])
        num_mcqs = int(request.form['num-mcqs'])
        num_tfs = int(request.form['num-tfs'])
        num_fibs = int(request.form['num-fibs'])

        # Generate questions for each type
        mcqs = gen_mcqs(input_text, num_mcqs)
        tfs = gen_tf(input_text, num_tfs)
        fibs = gen_fib(input_text, num_fibs)

        # Save the generated questions and worksheet to the database
        worksheet = Worksheet(user_id=user.id, title=w_title)

        # Save the PDF filenames to the database
        question_filename = f'question_{hashlib.sha1(str(worksheet.id).encode()).hexdigest()}.pdf'
        answer_filename = f'answer_{hashlib.sha1(str(worksheet.id).encode()).hexdigest()}.pdf'
        worksheet.question_pdf = question_filename
        worksheet.answer_pdf = answer_filename
        db.session.add(worksheet)
        db.session.commit()
        for question in mcqs:
            incorrect_answers_json = json.dumps(question["incorrect_answers"])
            db_question = Question(worksheet_id=worksheet.id, user_id=user.id, question_type='mcq', question=question["question"], correct_answer=question["correct_answer"], incorrect_answers=incorrect_answers_json)
            db.session.add(db_question)
        # Save True/False questions
        for question in tfs:
            db_question = Question(worksheet_id=worksheet.id, user_id=user.id, question_type='tf', question=question["question"], correct_answer=question["correct_answer"])
            db.session.add(db_question)

        # Save Fill-in-the-blank questions
        for question in fibs:
            db_question = Question(worksheet_id=worksheet.id, user_id=user.id, question_type='fib', question=question["question"], correct_answer=question["correct_answer"])
            db.session.add(db_question)

        db.session.commit()

        # Call the generate_pdfs function
        generate_pdfs(worksheet, w_title, mcqs, tfs, fibs) # Add tfs and fibs as needed

        return redirect(url_for('manage_worksheets'))

    return render_template('create_worksheet_text.html', user=user)


@app.route('/create_worksheet/pdf', methods=['GET', 'POST'])
def create_worksheet_pdf():
    user = get_logged_in_user()
    if not user:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        input_text = request.form['input-text']
        w_title = str(request.form['w-title'])
        num_mcqs = int(request.form['num-mcqs'])
        num_tfs = int(request.form['num-tfs'])
        num_fibs = int(request.form['num-fibs'])

        # Generate questions for each type
        mcqs = gen_mcqs(input_text, num_mcqs)
        tfs = gen_tf(input_text, num_tfs)
        fibs = gen_fib(input_text, num_fibs)

        # Save the generated questions and worksheet to the database
        worksheet = Worksheet(user_id=user.id, title=w_title)

        # Save the PDF filenames to the database
        question_filename = f'question_{hashlib.sha1(str(worksheet.id).encode()).hexdigest()}.pdf'
        answer_filename = f'answer_{hashlib.sha1(str(worksheet.id).encode()).hexdigest()}.pdf'
        worksheet.question_pdf = question_filename
        worksheet.answer_pdf = answer_filename
        db.session.add(worksheet)
        db.session.commit()
        for question in mcqs:
            incorrect_answers_json = json.dumps(question["incorrect_answers"])
            db_question = Question(worksheet_id=worksheet.id, user_id=user.id, question_type='mcq', question=question["question"], correct_answer=question["correct_answer"], incorrect_answers=incorrect_answers_json)
            db.session.add(db_question)
        # Save True/False questions
        for question in tfs:
            db_question = Question(worksheet_id=worksheet.id, user_id=user.id, question_type='tf', question=question["question"], correct_answer=question["correct_answer"])
            db.session.add(db_question)

        # Save Fill-in-the-blank questions
        for question in fibs:
            db_question = Question(worksheet_id=worksheet.id, user_id=user.id, question_type='fib', question=question["question"], correct_answer=question["correct_answer"])
            db.session.add(db_question)

        db.session.commit()

        # Call the generate_pdfs function
        generate_pdfs(worksheet, w_title, mcqs, tfs, fibs) # Add tfs and fibs as needed

        return redirect(url_for('manage_worksheets'))

    return render_template('create_worksheet_pdf.html', user=user)

@app.route('/create_worksheet/img', methods=['GET', 'POST'])
def create_worksheet_image():
    user = get_logged_in_user()
    if not user:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        input_text = request.form['input-text']
        w_title = str(request.form['w-title'])
        num_mcqs = int(request.form['num-mcqs'])
        num_tfs = int(request.form['num-tfs'])
        num_fibs = int(request.form['num-fibs'])

        # Generate questions for each type
        mcqs = gen_mcqs(input_text, num_mcqs)
        tfs = gen_tf(input_text, num_tfs)
        fibs = gen_fib(input_text, num_fibs)

        # Save the generated questions and worksheet to the database
        worksheet = Worksheet(user_id=user.id, title=w_title)

        # Save the PDF filenames to the database
        question_filename = f'question_{hashlib.sha1(str(worksheet.id).encode()).hexdigest()}.pdf'
        answer_filename = f'answer_{hashlib.sha1(str(worksheet.id).encode()).hexdigest()}.pdf'
        worksheet.question_pdf = question_filename
        worksheet.answer_pdf = answer_filename
        db.session.add(worksheet)
        db.session.commit()
        for question in mcqs:
            incorrect_answers_json = json.dumps(question["incorrect_answers"])
            db_question = Question(worksheet_id=worksheet.id, user_id=user.id, question_type='mcq', question=question["question"], correct_answer=question["correct_answer"], incorrect_answers=incorrect_answers_json)
            db.session.add(db_question)
        # Save True/False questions
        for question in tfs:
            db_question = Question(worksheet_id=worksheet.id, user_id=user.id, question_type='tf', question=question["question"], correct_answer=question["correct_answer"])
            db.session.add(db_question)

        # Save Fill-in-the-blank questions
        for question in fibs:
            db_question = Question(worksheet_id=worksheet.id, user_id=user.id, question_type='fib', question=question["question"], correct_answer=question["correct_answer"])
            db.session.add(db_question)

        db.session.commit()

        # Call the generate_pdfs function
        generate_pdfs(worksheet, w_title, mcqs, tfs, fibs) # Add tfs and fibs as needed

        return redirect(url_for('manage_worksheets'))

    return render_template('create_worksheet_image.html', user=user)

@app.route('/create_worksheet/wiki', methods=['GET', 'POST'])
def create_worksheet_wikipedia():
    user = get_logged_in_user()
    if not user:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        input_text = get_text_from_wikipedia(request.form['wikipedia_url'])
        w_title = str(request.form['w-title'])
        num_mcqs = int(request.form['num-mcqs'])
        num_tfs = int(request.form['num-tfs'])
        num_fibs = int(request.form['num-fibs'])

        # Generate questions for each type
        mcqs = gen_mcqs(input_text, num_mcqs)
        tfs = gen_tf(input_text, num_tfs)
        fibs = gen_fib(input_text, num_fibs)

        # Save the generated questions and worksheet to the database
        worksheet = Worksheet(user_id=user.id, title=w_title)

        # Save the PDF filenames to the database
        question_filename = f'question_{hashlib.sha1(str(worksheet.id).encode()).hexdigest()}.pdf'
        answer_filename = f'answer_{hashlib.sha1(str(worksheet.id).encode()).hexdigest()}.pdf'
        worksheet.question_pdf = question_filename
        worksheet.answer_pdf = answer_filename
        db.session.add(worksheet)
        db.session.commit()
        for question in mcqs:
            incorrect_answers_json = json.dumps(question["incorrect_answers"])
            db_question = Question(worksheet_id=worksheet.id, user_id=user.id, question_type='mcq', question=question["question"], correct_answer=question["correct_answer"], incorrect_answers=incorrect_answers_json)
            db.session.add(db_question)
        # Save True/False questions
        for question in tfs:
            db_question = Question(worksheet_id=worksheet.id, user_id=user.id, question_type='tf', question=question["question"], correct_answer=question["correct_answer"])
            db.session.add(db_question)

        # Save Fill-in-the-blank questions
        for question in fibs:
            db_question = Question(worksheet_id=worksheet.id, user_id=user.id, question_type='fib', question=question["question"], correct_answer=question["correct_answer"])
            db.session.add(db_question)

        db.session.commit()

        # Call the generate_pdfs function
        generate_pdfs(worksheet, w_title, mcqs, tfs, fibs) # Add tfs and fibs as needed

        return redirect(url_for('manage_worksheets'))

    return render_template('create_worksheet_wikipedia.html', user=user)

@app.route('/create_worksheet/yt', methods=['GET', 'POST'])
def create_worksheet_youtube():
    user = get_logged_in_user()
    if not user:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        input_text = get_text_from_youtube(request.form['youtube_url'])
        w_title = str(request.form['w-title'])
        num_mcqs = int(request.form['num-mcqs'])
        num_tfs = int(request.form['num-tfs'])
        num_fibs = int(request.form['num-fibs'])

        # Generate questions for each type
        mcqs = gen_mcqs(input_text, num_mcqs)
        tfs = gen_tf(input_text, num_tfs)
        fibs = gen_fib(input_text, num_fibs)

        # Save the generated questions and worksheet to the database
        worksheet = Worksheet(user_id=user.id, title=w_title)

        # Save the PDF filenames to the database
        question_filename = f'question_{hashlib.sha1(str(worksheet.id).encode()).hexdigest()}.pdf'
        answer_filename = f'answer_{hashlib.sha1(str(worksheet.id).encode()).hexdigest()}.pdf'
        worksheet.question_pdf = question_filename
        worksheet.answer_pdf = answer_filename
        db.session.add(worksheet)
        db.session.commit()
        for question in mcqs:
            incorrect_answers_json = json.dumps(question["incorrect_answers"])
            db_question = Question(worksheet_id=worksheet.id, user_id=user.id, question_type='mcq', question=question["question"], correct_answer=question["correct_answer"], incorrect_answers=incorrect_answers_json)
            db.session.add(db_question)
        # Save True/False questions
        for question in tfs:
            db_question = Question(worksheet_id=worksheet.id, user_id=user.id, question_type='tf', question=question["question"], correct_answer=question["correct_answer"])
            db.session.add(db_question)

        # Save Fill-in-the-blank questions
        for question in fibs:
            db_question = Question(worksheet_id=worksheet.id, user_id=user.id, question_type='fib', question=question["question"], correct_answer=question["correct_answer"])
            db.session.add(db_question)

        db.session.commit()

        # Call the generate_pdfs function
        generate_pdfs(worksheet, w_title, mcqs, tfs, fibs) # Add tfs and fibs as needed

        return redirect(url_for('manage_worksheets'))

    return render_template('create_worksheet_youtube.html', user=user)




@app.route('/create_worksheet/audio', methods=['GET', 'POST'])
def create_worksheet_audio():
    user = get_logged_in_user()
    if not user:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        input_text = request.form['input-text']
        w_title = str(request.form['w-title'])
        num_mcqs = int(request.form['num-mcqs'])
        num_tfs = int(request.form['num-tfs'])
        num_fibs = int(request.form['num-fibs'])

        # Generate questions for each type
        mcqs = gen_mcqs(input_text, num_mcqs)
        tfs = gen_tf(input_text, num_tfs)
        fibs = gen_fib(input_text, num_fibs)

        # Save the generated questions and worksheet to the database
        worksheet = Worksheet(user_id=user.id, title=w_title)

        # Save the PDF filenames to the database
        question_filename = f'question_{hashlib.sha1(str(worksheet.id).encode()).hexdigest()}.pdf'
        answer_filename = f'answer_{hashlib.sha1(str(worksheet.id).encode()).hexdigest()}.pdf'
        worksheet.question_pdf = question_filename
        worksheet.answer_pdf = answer_filename
        db.session.add(worksheet)
        db.session.commit()
        for question in mcqs:
            incorrect_answers_json = json.dumps(question["incorrect_answers"])
            db_question = Question(worksheet_id=worksheet.id, user_id=user.id, question_type='mcq', question=question["question"], correct_answer=question["correct_answer"], incorrect_answers=incorrect_answers_json)
            db.session.add(db_question)
        # Save True/False questions
        for question in tfs:
            db_question = Question(worksheet_id=worksheet.id, user_id=user.id, question_type='tf', question=question["question"], correct_answer=question["correct_answer"])
            db.session.add(db_question)

        # Save Fill-in-the-blank questions
        for question in fibs:
            db_question = Question(worksheet_id=worksheet.id, user_id=user.id, question_type='fib', question=question["question"], correct_answer=question["correct_answer"])
            db.session.add(db_question)

        db.session.commit()

        # Call the generate_pdfs function
        generate_pdfs(worksheet, w_title, mcqs, tfs, fibs) # Add tfs and fibs as needed

        return redirect(url_for('manage_worksheets'))

    return render_template('create_worksheet_audio.html', user=user)

@app.route('/worksheet/<int:worksheet_id>/download_questions')
def download_worksheet_questions(worksheet_id):
    worksheet = Worksheet.query.get_or_404(worksheet_id)
    questions_pdf_path = os.path.join('static', worksheet.question_pdf)
    with open(questions_pdf_path, 'rb') as f:
        pdf_data = f.read()

    response = make_response(pdf_data)
    response.headers.set('Content-Type', 'application/pdf')
    response.headers.set('Content-Disposition', 'attachment', filename=f'{worksheet.title}_questions.pdf')
    return response

@app.route('/worksheet/<int:worksheet_id>/download_answers')
def download_worksheet_answers(worksheet_id):
    worksheet = Worksheet.query.get_or_404(worksheet_id)
    answers_pdf_path = os.path.join('static', worksheet.answer_pdf)
    with open(answers_pdf_path, 'rb') as f:
        pdf_data = f.read()

    response = make_response(pdf_data)
    response.headers.set('Content-Type', 'application/pdf')
    response.headers.set('Content-Disposition', 'attachment', filename=f'{worksheet.title}_answers.pdf')
    return response

@app.route('/worksheet/<int:worksheet_id>/delete')
def delete_worksheet(worksheet_id):
    user = get_logged_in_user()
    if not user:
        return redirect(url_for('login'))

    worksheet = Worksheet.query.get_or_404(worksheet_id)

    if worksheet.user_id != user.id:
        return "Unauthorized", 403

    db.session.delete(worksheet)
    db.session.commit()

    return redirect(url_for('manage_worksheets'))


@app.route('/manage_worksheets')
def manage_worksheets():
    user = get_logged_in_user()
    if not user:
        return redirect(url_for('login'))
    worksheets = Worksheet.query.filter_by(user_id=user.id).order_by(Worksheet.created_at.desc()).all()

    return render_template('manage_worksheets.html', user=user, worksheets=worksheets)


if __name__ == '__main__':
    # trial_text = "The production of renewable energy in Scotland came to the fore in technical, economic and political terms in the 21st century. In 2020, Scotland had 12 gigawatts of renewable electricity capacity which produced about a quarter of UK renewable generation. In decreasing order of capacity, Scotland's renewable generation comes from onshore wind (turbines pictured), water, offshore wind, solar photovoltaics and biomass. Fears regarding fuel poverty and climate change increased its prevalence on the political agenda. Renewables met a quarter of total energy consumption in 2020; the Scottish government target is having renewables meet half of total energy consumption by 2030. Although there is significant support from the public, private and community-led sectors, concerns about the effect of the technologies on the natural environment have been expressed. There is also a political debate about the relationship between the siting, and the ownership and control of these widely distributed resources."
    # print(generate_questions_with_cohere(trial_text))
    app.run(debug=True)