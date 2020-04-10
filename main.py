from flask import Flask, request, flash, url_for, redirect, render_template
from flask_sqlalchemy import SQLAlchemy, sqlalchemy
from sqlalchemy.sql import exists
from flask_login import LoginManager, UserMixin, login_required, current_user, logout_user, login_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vleague.sqlite3'
app.config['SECRET_KEY'] = "random string"

db = SQLAlchemy(app)

class User(UserMixin, db.Model):
   id = db.Column(db.Integer, primary_key = True)
   name = db.Column(db.String, nullable = False, unique = False)
   password = db.Column(db.String(100), nullable = False, unique = False)

   def set_password(self, password):
      self.password = generate_password_hash(password, method="sha256")

   def check_password(self, password):
      return check_password_hash(self.password, password)

   def __repr__(self):
      return '<User {}>'.format(self.username)

class SignupForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm = PasswordField('Confirm Your Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match.')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    """User Login Form."""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    signup_form = SignupForm(request.form)
    if request.method == 'POST':
        print("posted")
        if signup_form.validate_on_submit():
            print("validated")
            name = request.form.get('username')
            password = request.form.get('password')
            #existing_user = User.query.filter_by(username=username).first()
            #if existing_user is None:
            user = User(name=name)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('home'))
    return render_template('register.html', form=signup_form)

if __name__ == "__main__":
   db.create_all()
   app.run(debug=True)