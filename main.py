import datetime
import calendar
from flask import Flask, request, flash, url_for, redirect, render_template
from flask_sqlalchemy import SQLAlchemy, sqlalchemy
from sqlalchemy.sql import exists
from flask_login import LoginManager, UserMixin, login_required, current_user, logout_user, login_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, SelectField
from wtforms.fields.html5 import DateField
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional
from datetime import date

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

# Player db
class Player(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String, nullable = False, unique = False)
    height = db.Column(db.Integer, nullable = False, unique = False)
    position = db.Column(db.String(30), nullable = False, unique = False)
    age = db.Column(db.Integer, nullable = False, unique = False)
    number = db.Column(db.Integer, nullable = False, unique = False)
    birth_date = db.Column(db.String, nullable = False, unique = False)
    birth_place = db.Column(db.String, nullable = False, unique = False)
    image = db.Column(db.String, nullable = True, unique = True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))

# Team db
class Team(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String, nullable = False, unique = True)
    founded_date = db.Column(db.Integer, nullable = True, unique = False)
    stadium = db.Column(db.String, nullable = True, unique = False)
    chairman = db.Column(db.String, nullable = True, unique = True)
    image = db.Column(db.String, nullable = True, unique = True)
    division = db.Column(db.String, nullable = False, unique = False)
    players = db.relationship('Player', backref='team')

    def __repr__(self):
        return '[Team {}]'.format(self.name)

# Scheduled games db
class TeamGames(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    first_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable = False)
    second_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable = False)
    date = db.Column(db.Date, nullable = False)

# User db
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

# Sign up flask form
class SignupForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[Length(min=6), DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm = PasswordField('Confirm Your Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match.')])
    submit = SubmitField('Register')

# Login flask form
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(message='Enter a valid email.')])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

# Add team flask form
class AddTeamForm(FlaskForm):
    name = StringField('Team Name', validators=[DataRequired()])
    founded_date = IntegerField('Founded Date', validators=[DataRequired()])
    stadium = StringField('Stadium', validators=[DataRequired()])
    chairman = StringField('Chairman', validators=[DataRequired()])
    division = SelectField(choices=[('M', 'Male'),('W','Women')])
    submit = SubmitField('Add')

# Function to query for all the teams to be used for select field 
def choice_query():
    return Team.query.all()

# Add scheduled game flask form
class AddGameForm(FlaskForm):
    first_team = QuerySelectField(query_factory=choice_query,allow_blank=True, get_label='name')
    second_team = QuerySelectField(query_factory=choice_query,allow_blank=True, get_label='name')
    scheduled_date = DateField('date', format='%Y-%m-%d')

# Add player flask form
class AddPlayerForm(FlaskForm):
    name = StringField('Player Name', validators=[DataRequired()])
    height = IntegerField('Height', validators=[DataRequired()])
    position = SelectField(choices=[('Setter', 'Setter'), ('Opposite', 'Opposite'), ('Middle-blocker', 'Middle-blocker'), ('Outside Hitter', 'Outside Hitter'), ('Libero', 'Libero')])
    age = IntegerField('Age', validators=[DataRequired()])
    number = IntegerField('Number', validators=[DataRequired()])
    birth_date = DateField('Birth Date', format='%Y-%m-%d')
    birth_place = StringField('Birth Place', validators=[DataRequired()])
    team = QuerySelectField(query_factory=choice_query, allow_blank=True, get_label='name')

@app.route('/')
def home():
    # Lists to store teams that are competing today 
    first_team_list = []
    second_team_list = []

    # Lists to store teams that are competing tomorrow 
    tmr_first_teams_list = []
    tmr_second_teams_list = []

    # List to store all the users that liked a player
    upvoters = []

    # List to store the most liked players 
    top_players_list = []

    # Query for today and tomorrow's games using the dates  
    today_date = TeamGames.query.filter_by(date=date.today()).all()
    tmr_date = TeamGames.query.filter_by(date=datetime.date.today() + datetime.timedelta(days=1)).all()
    #Query for all players in database
    all_players = Player.query.all()
    # Loop to add all the players upvoters count into a list
    for i in range(len(all_players)):
        upvoters.append(all_players[i].upvoters.count())
    # Loop to add all of tomorrow's first team's id and second team's id into a list
    for i in range(len(tmr_date)):
        tmr_first_teams_list.append(tmr_date[i].first_team_id)
        tmr_second_teams_list.append(tmr_date[i].second_team_id)
    # Loop to add all of today's first team's id and second team's id into a list
    for i in range(len(today_date)):
        first_team_list.append(today_date[i].first_team_id)
        second_team_list.append(today_date[i].second_team_id)
    # Sort the upvoters count list by descending order
    upvoters.sort(reverse=True)
    # Add the top upvoted players according to their upvoters count into a list
    for i in range(len(all_players)):
        if(all_players[i].upvoters.count() == upvoters[0] and upvoters[0] != 0):
            top_players_list.append(all_players[i].id)
        if(all_players[i].upvoters.count() == upvoters[1] and upvoters[1] != 0):
            top_players_list.append(all_players[i].id)
        if(all_players[i].upvoters.count() == upvoters[2] and upvoters[2] != 0):
            top_players_list.append(all_players[i].id)
    # Query for the top upvoted players no duplicates
    top_players = Player.query.filter(Player.id.in_(top_players_list)).all()
    # Query for today and tomorrow's first and second teams with duplicates
    tmr_first_teams = [Team.query.filter_by(id=id).one() for id in tmr_first_teams_list]
    tmr_second_teams = [Team.query.filter_by(id=id).one() for id in tmr_second_teams_list]
    today_first_teams = [Team.query.filter_by(id=id).one() for id in first_team_list]
    today_second_teams = [Team.query.filter_by(id=id).one() for id in second_team_list]
    return render_template('home.html', today_first_teams=today_first_teams, today_second_teams=today_second_teams, tmr_first_teams=tmr_first_teams, tmr_second_teams=tmr_second_teams, top_players=top_players)

@app.route('/account', methods=['GET','POST'])
def account():
    # List to store all the players a user has liked 
    user_upvotes = []

    this_user = User.query.filter_by(id=current_user.id).first()
    # Stores the players the user has liked 
    for i in range(len(current_user.upvotes)):
        user_upvotes.append(current_user.upvotes[i].id)
    # Query for all the players the user has liked
    upvotes = Player.query.filter(Player.id.in_(user_upvotes)).all()
    if request.method == 'POST':
        # Deletes the user
        db.session.delete(this_user)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('account.html', this_user=this_user, upvotes=upvotes)

@app.route('/schedule', methods=['GET','POST'])
def schedule():
    # Lists to store all teams that are competing
    all_first_teams_list = []
    all_second_teams_list = []

    form = AddGameForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            # Data collected from the add game form
            id_one = request.form.get('first_team')
            id_two = request.form.get('second_team')
            sch_date = request.form.get('scheduled_date')
            # Query for the competing teams
            team_one = Team.query.filter_by(id=id_one).first()
            team_two = Team.query.filter_by(id=id_two).first()
            if(id_one != '__None' and id_two != '__None' and sch_date != '' and id_one != id_two):
                # Converts the string to python datetime 
                date = datetime.datetime.strptime(sch_date, '%Y-%m-%d')
                game = TeamGames(first_team_id=int(id_one), second_team_id=int(id_two), date=date)
                # Adds the scheduled game
                db.session.add(game)
                db.session.commit()
                return redirect (url_for('schedule'))
    # Sorts the scheduled games by ascending order based on the dates  
    all_date = TeamGames.query.order_by(TeamGames.date).all()
    dates_to_store = []
    # Stores all the competing teams 
    for i in range(len(all_date)):
        date_to = datetime.date.today()
        if(all_date[i].date > date_to):
            dates_to_store.append(all_date[i].date)
            all_first_teams_list.append(all_date[i].first_team_id)
            all_second_teams_list.append(all_date[i].second_team_id)
    # Query for all the competing teams
    all_first_teams = [Team.query.filter_by(id=id).one() for id in all_first_teams_list]
    all_second_teams = [Team.query.filter_by(id=id).one() for id in all_second_teams_list]
    return render_template('schedule.html', all_second_teams=all_second_teams,dates_to_store=dates_to_store, all_first_teams=all_first_teams, all_date=all_date, form=form)

@app.route('/all-players', methods=['GET', 'POST'])
def allplayers():
    form = AddPlayerForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            # Data collected from the add player form
            name = request.form.get('name')
            height = request.form.get('height')
            position = request.form.get('position')
            age = request.form.get('age')
            number = request.form.get('number')
            birth_date = request.form.get('birth_date')
            birth_place = request.form.get('birth_place')
            team= request.form.get('team')
            print(birth_date)
            # Converts the collected birth date to a string - with format Day Month Year in words, e.g. 10 May 2012
            day = birth_date.split('-')[2]
            month = calendar.month_name[int(birth_date.split('-')[1])]
            year = birth_date.split('-')[0]
            complete_date = day + " " + month + " " + year
            # Checks if the player's name already exist in the player db
            existing_name = Player.query.filter_by(name=name).first()
            if(existing_name): 
                if(birth_place != existing_name.birth_place and birth_date != existing_name.birth_date and number != existing_name.number and team != existing_name.team_id):
                    to_add = Player(name=name, height=height, position=position, age=age, number=number, birth_date=complete_date, birth_place=birth_place, team_id=int(team))
                    db.session.add(to_add)
                    db.session.commit()
                    return redirect (url_for('allplayers'))  
            else:
                to_add = Player(name=name, height=height, position=position, age=age, number=number, birth_date=complete_date, birth_place=birth_place, team_id=int(team))
                db.session.add(to_add)
                db.session.commit()
                return redirect (url_for('allplayers'))  
    # List to store players based on the first letter of their name 
    result = []
    for i in range(26):
        # Variable to store the letters 
        var = chr(65+i)
        result.append(Player.query.filter(Player.name.startswith(var)).all())
    return render_template('allplayers.html', q=result, form=form)

@app.route('/player/<player_name>-<player_id>', methods=['GET','POST'])
def playerprofile(player_name, player_id):
    # Check if the player exists in the player db
    check_id = Player.query.filter_by(id=player_id).first()
    check_player = Player.query.filter_by(name=player_name).all()
    checked=False
    # If player does not exists redirect to 404 page 
    for i in check_player:
        if i == check_id:
            checked=True
            if current_user.is_authenticated:
                user = User.query.filter_by(id=current_user.id).first()
                player = Player.query.filter_by(id=player_id).first()
                # Checks if the user has liked the player 
                liked = player.upvoters.filter_by(id=current_user.id).first()
                if request.method == 'POST':
                    if request.form.get("delete"):
                        # Deletes the player - only for admins
                        to_delete = Player.query.filter_by(id=player_id).first()
                        db.session.delete(to_delete)
                        db.session.commit()
                        return redirect (url_for('allplayers'))
                    else:
                        # Likes the player if the user hasn't already 
                        if liked is None:
                            player.upvoters.append(user)
                            db.session.commit()
                            return redirect(url_for('playerprofile', player_name=player_name, player_id=player_id))
                        # Unlike the player if the user has liked them before 
                        if liked:
                            player.upvoters.remove(user)
                            db.session.commit()
                            return redirect(url_for('playerprofile', player_name=player_name, player_id=player_id))
            else:
                return render_template('player_profile.html', player_info=Player.query.filter_by(id=player_id).all())
            break
    if not checked:
        return redirect('/404')
    return render_template('player_profile.html', liked=liked, player_info=Player.query.filter_by(id=player_id).all())

@app.route('/team/<team_name>', methods=['GET','POST'])
def teampage(team_name):
    # Check if the team exists in the team db
    check_team = Team.query.filter_by(name=team_name).first()
    # If the team does not exist redirect the user to 404 page 
    if check_team is None:
        return redirect('/404')
    team=Team.query.filter_by(name=team_name).all()
    # Query for all the players in the team 
    team_players=Player.query.filter_by(team_id=Team.query.filter_by(name=team_name).first().id).all()
    if request.method == 'POST':
        # Deletes the team - only for admins
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
            # Data collected from the add team form 
            name = request.form.get('name')
            founded_date = request.form.get('founded_date')
            stadium = request.form.get('stadium')
            chairman = request.form.get('chairman')
            division = request.form.get('division').upper()
            length_test = len(str(founded_date))
            # Checks if the team already exist in the team db
            existing_team = Team.query.filter_by(name=name).first()
            if existing_team is None:
                if length_test == 4 and int(founded_date) > 0:
                    team = Team(name=name, founded_date=founded_date, stadium=stadium, chairman=chairman, division=division)
                    db.session.add(team)
                    db.session.commit()
                    return redirect(url_for('allteams'))
    # Query for all the women and men teams 
    women_teams = Team.query.filter(Team.division=='W').all()
    men_teams = Team.query.filter(Team.division=='M').all()
    return render_template('allteams.html', women_teams=women_teams, men_teams=men_teams, form=addteam_form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    signup_form = SignupForm(request.form)
    if request.method == 'POST':
        if signup_form.validate_on_submit():
            # Data collected from the sign up form
            name = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            # Checks if user already has an account under the same email
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
        if login_form.validate():
            # Data collected from the login form 
            email = request.form.get('email')
            password = request.form.get('password')
            user = User.query.filter_by(email=email).first()
            # Checks if user has entered the right email and password
            if user and user.check_password(password=password):
                login_user(user)
                next_page = request.args.get('next')
                return redirect(next_page or url_for('home'))
    return render_template('login.html', form=login_form)

@app.route('/logout')
@login_required
def logout():
   logout_user()
   return redirect(url_for('home'))

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html")

@login_manager.user_loader
def load_user(user_id):
    if user_id is not None:
        return User.query.get(user_id)
    return None

if __name__ == "__main__":
   db.create_all()
   app.run(debug=True)