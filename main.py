import datetime
from flask import Flask, request, flash, url_for, redirect, render_template
from flask_sqlalchemy import SQLAlchemy, sqlalchemy
from sqlalchemy.sql import exists
from flask_login import LoginManager, UserMixin, login_required, current_user, logout_user, login_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vleague.db'
app.config['SECRET_KEY'] = "random string"

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

likes = db.Table('likes', 
        db.Column('user_id', db.Integer, db.ForeignKey('user.id')), 
        db.Column('player_id', db.Integer, db.ForeignKey('player.id'))
)

class Player(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String, nullable = False, unique = True)
    height = db.Column(db.Integer, nullable = False, unique = False)
    position = db.Column(db.String(30), nullable = False, unique = False)
    age = db.Column(db.Integer, nullable = False, unique = False)
    number = db.Column(db.Integer, nullable = False, unique = False)
    birth_date = db.Column(db.String, nullable = False, unique = False)
    birth_place = db.Column(db.String, nullable = False, unique = False)
    image = db.Column(db.String, nullable = True, unique = True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))

class Team(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String, nullable = False, unique = True)
    founded_date = db.Column(db.String, nullable = True, unique = False)
    stadium = db.Column(db.String, nullable = True, unique = False)
    chairman = db.Column(db.String, nullable = True, unique = True)
    image = db.Column(db.String, nullable = True, unique = True)
    players = db.relationship('Player', backref='team')

class User(UserMixin, db.Model):
   id = db.Column(db.Integer, primary_key = True)
   name = db.Column(db.String, nullable = False, unique = False)
   email = db.Column(db.String, unique = True, nullable = False)
   password = db.Column(db.String(100), nullable = False, unique = False)
   created_on = db.Column(db.DateTime, index = False, unique = False, nullable = True, default=datetime.date.today())
   upvotes = db.relationship('Player', secondary=likes, backref=db.backref('upvoters', lazy='dynamic'))

   def set_password(self, password):
      self.password = generate_password_hash(password, method="sha256")

   def check_password(self, password):
      return check_password_hash(self.password, password)

   def __repr__(self):
      return '<User {}>'.format(self.username)

class SignupForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[Length(min=6), DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm = PasswordField('Confirm Your Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match.')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(message='Enter a valid email.')])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

@app.route('/')
def home():
    if current_user.is_authenticated:
        print('user authenticated')
    if not current_user.is_authenticated:
        print('user not authenticated')
    return render_template('home.html')

@app.route('/all-players')
def allplayers():
    return render_template('allplayers.html', p_startWithL=Player.query.filter(Player.name.startswith('L')).all(), 
                                              p_startWithK=Player.query.filter(Player.name.startswith('K')).all(),
                                              p_startWithH=Player.query.filter(Player.name.startswith('H')).all(),
                                              p_startWithJ=Player.query.filter(Player.name.startswith('J')).all(),
                                              p_startWithG=Player.query.filter(Player.name.startswith('G')).all(),
                                              p_startWithM=Player.query.filter(Player.name.startswith('M')).all(),
                                              p_startWithY=Player.query.filter(Player.name.startswith('Y')).all(),
                                              p_startWithS=Player.query.filter(Player.name.startswith('S')).all()
                                              )

@app.route('/player/<player_name>', methods=['GET','POST'])
def playerprofile(player_name):
    user = User.query.filter_by(id=current_user.id).first()
    player = Player.query.filter_by(name=player_name).first()
    liked = player.upvoters.filter_by(id=current_user.id).first()
    like_count = User.query.filter(User.upvotes.any(id=player.id)).count()
    if request.method == 'POST':
        if liked is None:
            player.upvoters.append(user)
            db.session.commit()
            return redirect(url_for('playerprofile', player_name=player_name))
    return render_template('player_profile.html', liked=liked, player_info=Player.query.filter_by(name=player_name).all())

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    signup_form = SignupForm(request.form)
    if request.method == 'POST':
        print("sign up posted")
        if signup_form.validate_on_submit():
            print("sign up validated")
            name = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            existing_user = User.query.filter_by(email=email).first()
            if existing_user is None:
                user = User(name=name, email=email)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                login_user(user)
                return redirect(url_for('home'))
    return render_template('register.html', form=signup_form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    login_form = LoginForm(request.form)

    if request.method == "POST":
        print('login posted')
        if login_form.validate():
            print('login validated')
            email = request.form.get('email')
            password = request.form.get('password')
            user = User.query.filter_by(email=email).first()
            if user and user.check_password(password=password):
                login_user(user)
                print('logged in')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('home'))
        if not login_form.validate():
            print('login not validated')
    return render_template('login.html', form=login_form)

@app.route('/logout')
@login_required
def logout():
   logout_user()
   return redirect(url_for('home'))

@login_manager.user_loader
def load_user(user_id):
    if user_id is not None:
        return User.query.get(user_id)
    return None

@login_manager.unauthorized_handler
def unauthorized():
    flash('You must be logged in to view that page.')
    return redirect(url_for('login'))

if __name__ == "__main__":
   db.create_all()
   app.run(debug=True)