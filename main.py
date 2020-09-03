import datetime
from flask import Flask, request, flash, url_for, redirect, render_template
from flask_sqlalchemy import SQLAlchemy, sqlalchemy
from sqlalchemy.sql import exists
from flask_login import LoginManager, UserMixin, login_required, current_user, logout_user, login_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional
from datetime import date

first_team_list = []
second_team_list = []

tmr_first_teams_list = []
tmr_second_teams_list = []

all_first_teams_list = []
all_second_teams_list = []

upvoters = []
top_players_list = []

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///static/vleague.db'
app.config['SECRET_KEY'] = "random string"

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

# many to many relationship table for user likes 
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
    division = db.Column(db.String, nullable = False, unique = False)
    players = db.relationship('Player', backref='team')

class TeamGames(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    first_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable = False)
    second_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable = False)
    date = db.Column(db.Date, nullable = False)

class User(UserMixin, db.Model):
   id = db.Column(db.Integer, primary_key = True)
   name = db.Column(db.String, nullable = False, unique = False)
   email = db.Column(db.String, unique = True, nullable = False)
   password = db.Column(db.String(100), nullable = False, unique = False)
   created_on = db.Column(db.Date, index = False, unique = False, nullable = True, default=date.today())
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

class AddTeamForm(FlaskForm):
    name = StringField('Team Name', validators=[DataRequired()])
    founded_date = IntegerField('Founded Date', validators=[DataRequired()])
    stadium = StringField('Stadium', validators=[DataRequired()])
    chairman = StringField('Chairman', validators=[DataRequired()])
    division = StringField('Divison', validators=[DataRequired(), Length(min=1,max=1)])
    submit = SubmitField('Add')


@app.route('/')
def home():
    #Clears the list to prevent duplicates
    first_team_list.clear()
    second_team_list.clear()
    tmr_first_teams_list.clear()
    tmr_second_teams_list.clear()
    upvoters.clear()
    top_players_list.clear()
    #Query for today and tomorrow's games using the dates  
    today_date = TeamGames.query.filter_by(date=date.today()).all()
    tmr_date = TeamGames.query.filter_by(date=datetime.date.today() + datetime.timedelta(days=1)).all()
    #Query for all players in database
    all_players = Player.query.all()
    #Loop to add all the players upvoters count into a list
    for i in range(len(all_players)):
        upvoters.append(all_players[i].upvoters.count())
    #Loop to add all of tomorrow's first team's id and second team's id into a list
    for i in range(len(tmr_date)):
        tmr_first_teams_list.append(tmr_date[i].first_team_id)
        tmr_second_teams_list.append(tmr_date[i].second_team_id)
    #Loop to add all of today's first team's id and second team's id into a list
    for i in range(len(today_date)):
        first_team_list.append(today_date[i].first_team_id)
        second_team_list.append(today_date[i].second_team_id)
    #Sort the upvoters count list by descending order
    upvoters.sort(reverse=True)
    #Add the top upvoted players according to their upvoters count into a list
    for i in range(len(all_players)):
        if(all_players[i].upvoters.count() == upvoters[0] and upvoters[0] != 0):
            top_players_list.append(all_players[i].id)
        if(all_players[i].upvoters.count() == upvoters[1] and upvoters[1] != 0):
            top_players_list.append(all_players[i].id)
        if(all_players[i].upvoters.count() == upvoters[2] and upvoters[2] != 0):
            top_players_list.append(all_players[i].id)
    #Query for the top upvoted players
    top_players = Player.query.filter(Player.id.in_(top_players_list)).all()
    #Query for today and tomorrow's first and second teams 
    tmr_first_teams = [Team.query.filter_by(id=id).one() for id in tmr_first_teams_list]
    tmr_second_teams = [Team.query.filter_by(id=id).one() for id in tmr_second_teams_list]
    today_first_teams = [Team.query.filter_by(id=id).one() for id in first_team_list]
    today_second_teams = [Team.query.filter_by(id=id).one() for id in second_team_list]
    return render_template('home.html', today_first_teams=today_first_teams, today_second_teams=today_second_teams, tmr_first_teams=tmr_first_teams, tmr_second_teams=tmr_second_teams, top_players=top_players)

@app.route('/schedule')
def schedule():
    all_first_teams_list.clear()
    all_second_teams_list.clear()
    all_date = TeamGames.query.all()
    for i in range(len(all_date)):
        all_first_teams_list.append(all_date[i].first_team_id)
        all_second_teams_list.append(all_date[i].second_team_id)
    all_first_teams = [Team.query.filter_by(id=id).one() for id in all_first_teams_list]
    all_second_teams = [Team.query.filter_by(id=id).one() for id in all_second_teams_list]
    return render_template('schedule.html', all_second_teams=all_second_teams, all_first_teams=all_first_teams, all_date=all_date)

@app.route('/all-players')
def allplayers():
    result = []
    for i in range(26):
        var = chr(65+i)
        result.append(Player.query.filter(Player.name.startswith(var)).all())
    return render_template('allplayers.html', q=result)

@app.route('/player/<player_name>', methods=['GET','POST'])
def playerprofile(player_name):
    if current_user.is_authenticated:
        user = User.query.filter_by(id=current_user.id).first()
        player = Player.query.filter_by(name=player_name).first()
        # checks if the user has liked the player 
        liked = player.upvoters.filter_by(id=current_user.id).first()
        if request.method == 'POST':
            if liked is None:
                player.upvoters.append(user)
                db.session.commit()
                return redirect(url_for('playerprofile', player_name=player_name))
            if liked:
                player.upvoters.remove(user)
                db.session.commit()
                return redirect(url_for('playerprofile', player_name=player_name))
    else:
        return render_template('player_profile.html', player_info=Player.query.filter_by(name=player_name).all())
    return render_template('player_profile.html', liked=liked, player_info=Player.query.filter_by(name=player_name).all())

@app.route('/team/<team_name>', methods=['GET','POST'])
def teampage(team_name):
    team=Team.query.filter_by(name=team_name).all()
    team_players=Player.query.filter_by(team_id=Team.query.filter_by(name=team_name).first().id).all()
    if request.method == 'POST':
        delteam = Team.query.filter_by(name=team_name).first()
        db.session.delete(delteam)
        db.session.commit()
        return redirect(url_for('allteams'))
    return render_template('team_page.html', team=team, team_players=team_players)

@app.route('/all-teams', methods=['GET', 'POST'])
def allteams():
    addteam_form = AddTeamForm(request.form)
    if request.method == 'POST':
        if addteam_form.validate_on_submit():
            name = request.form.get('name')
            founded_date = request.form.get('founded_date')
            stadium = request.form.get('stadium')
            chairman = request.form.get('chairman')
            division = request.form.get('division').upper()
            length_test = len(str(founded_date))
            # checks if user already has an account under the same email
            existing_user = Team.query.filter_by(name=name).first()
            if existing_user is None:
                if length_test == 4 and int(founded_date) > 0 and (division == 'M' or division == 'W'):
                    team = Team(name=name, founded_date=founded_date, stadium=stadium, chairman=chairman, division=division)
                    db.session.add(team)
                    db.session.commit()
                    return redirect(url_for('allteams'))
    women_teams = Team.query.filter(Team.division=='W').all()
    men_teams = Team.query.filter(Team.division=='M').all()
    return render_template('allteams.html', women_teams=women_teams, men_teams=men_teams, form=addteam_form)

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
            # checks if user already has an account under the same email
            existing_user = User.query.filter_by(email=email).first()
            if existing_user is None:
                if(('@' in email) & ((".com" in email) | (".nz" in email))):
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

if __name__ == "__main__":
   db.create_all()
   today = date.today()
   if str(today) == '2020-08-26':   
    print(today)
   app.run(debug=True)