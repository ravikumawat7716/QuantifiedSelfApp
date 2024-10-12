#import libraries
import os
from enum import unique
from flask import Flask, render_template, request, url_for, redirect, session, g
from flask_sqlalchemy import SQLAlchemy
from matplotlib import pyplot as plt
from flask import flash, get_flashed_messages


#create a Flask Instance
app=Flask(__name__)
app.secret_key = 'any random string '
# Add Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#Initialize the database
db=SQLAlchemy(app)

#create model
class User(db.Model):
    email_address = db.Column(db.String(100), primary_key=True, nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def __init__(self, email_address, name, password):
        self.email_address = email_address
        self.name = name
        self.password = password

class Tracker(db.Model):
    Tracker_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.String(100), nullable=False)
    Desc = db.Column(db.String(100), nullable=False)
    Tracker_Type = db.Column(db.String(100), nullable=False)
    Settings = db.Column(db.String(100))
    username = db.Column(db.String(100), db.ForeignKey('user.email_address'), nullable=False)

    def __init__(self, Name, Desc, Tracker_Type, Settings, username):
        self.Name = Name
        self.Desc = Desc
        self.Tracker_Type = Tracker_Type
        self.Settings = Settings
        self.username = username

class Log(db.Model):
    Timestamp = db.Column(db.String(100), nullable=False)
    log_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    l_student = db.Column(db.String(100), db.ForeignKey('user.email_address'), nullable=False)
    l_Tracker_ID = db.Column(db.Integer, db.ForeignKey('tracker.Tracker_ID'), nullable=False)
    value = db.Column(db.String(100), nullable=False)
    notes = db.Column(db.String(100), nullable=False)

    def __init__(self, Timestamp, l_student, l_Tracker_ID, value, notes):
        self.Timestamp = Timestamp
        self.l_student = l_student
        self.l_Tracker_ID = l_Tracker_ID
        self.value = value
        self.notes = notes






@app.before_request
def before_request():
    users = User.query.all()
    if 'user_id' in session:
        user = [x for x in users if x.email_address == session['user_id']]
        if user:
            g.user = user[0]
        else:
            g.user = None
    else:
        g.user = None


@app.route('/')
def home():
    if g.user == None:
        return redirect(url_for('login'))
    else:
        return redirect(url_for('profile'))

@app.route("/register",methods=['GET','POST'])
def register():
    if request.form:
        e = request.form['email']
        n = request.form['name']
        p = request.form['pass']

        
        missing=User.query.filter_by(email_address=e).first()
        if missing is None:
            s=User(email_address=e, name=n, password=p)
            db.session.add(s)
            db.session.commit()
            return render_template('registration_successful.html')
        else:
            return render_template('user_already_exists.html')

        


    return render_template('user_registration.html')



@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session.pop('user_id', None)
        un = request.form['username']
        pw = request.form['password']
        userdata = User.query.all()

        for i in userdata:
            if i.email_address == un:
                if i.password == pw:
                    session['user_id'] = un 
                    flash('Login successful!', 'success')
                    return redirect(url_for('profile'))
                else:
                    flash('Incorrect password. Please try again.', 'error')
                    break
        else:
            flash('User not found. Please register.', 'error')
    
    return render_template('login.html', messages=get_flashed_messages())


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return render_template('logout.html')

@app.route('/profile')
def profile():
    if g.user == None:
        return redirect(url_for('login'))
    else:
        trackers = Tracker.query.filter_by(username = g.user.email_address)
        
        if trackers:
            return render_template('profile.html', trackers=trackers)
        else:
            return render_template('fresh_profile.html')


@app.route('/tracker/create',methods=['GET', 'POST'])
def tracker_create():
    if g.user == None:
        return redirect(url_for('login'))
    else:
        if request.method =='POST':
            name=request.form['name']
            desc=request.form['desc']
            tracker_type=request.form['tracker_type']
            settings = request.form['setting']

            missing=Tracker.query.filter_by(Name = name , username = g.user.email_address).first()
            if missing is None:
                # If tracker not exists
                s=Tracker(Name = name,Desc=desc,Tracker_Type=tracker_type,Settings=settings,username = g.user.email_address)
                db.session.add(s)
                db.session.commit()
                return redirect(url_for('profile'))
            return render_template('tracker_exists.html')
        
        return render_template('add_tracker.html')



@app.route('/tracker/<int:Tracker_ID>')
def tracker_page(Tracker_ID):
    if g.user == None:
        return redirect(url_for('login'))
    else:
        logs = Log.query.with_entities(Log.Timestamp,Log.value).filter_by(l_student = g.user.email_address, l_Tracker_ID = Tracker_ID)
        x=[]
        y=[]
        for i in logs:
            print(i)
            x.append(i[0])
            y.append(i[1])
        plt.plot(x,y)
        plt.xlabel("Timestamp")
        plt.ylabel("Value") 
        plt.savefig('static/img.png',dpi=300)
        tracker = Tracker.query.filter_by(Tracker_ID=Tracker_ID).first()
        logss = Log.query.filter_by(l_student = g.user.email_address, l_Tracker_ID = Tracker_ID)

        return render_template('tracker_page.html',logss = logss, tracker = tracker)

@app.route('/tracker/<int:Tracker_ID>/update',methods=['GET','POST'])
def update_tracker(Tracker_ID):
    if g.user == None:
        return redirect(url_for('login'))
    else:
        if request.method == 'POST':
            name=request.form['name']
            desc=request.form['desc']
            tracker_type=request.form['tracker_type']
            settings = request.form['setting']
            s=Tracker.query.filter_by(Tracker_ID=Tracker_ID).update(dict(Name=name,Desc=desc,Tracker_Type=tracker_type,Settings=settings))
            db.session.commit()
            return redirect(url_for('profile'))
        elif request.method == 'GET':
            this_tracker = Tracker.query.filter_by(Tracker_ID=Tracker_ID).first()
            options = Tracker.query.with_entities(Tracker.Tracker_Type).filter_by(Tracker_ID=Tracker_ID).all()
            l=[]
            for i in options:
                if i == ('numerical',):
                    l.append(1)
                else:
                    l.append(2)
            print(l)
            return render_template('update_tracker.html',this_tracker = this_tracker,l = l)


@app.route('/tracker/<int:Tracker_ID>/delete')
def delete_tracker(Tracker_ID):
    if g.user == None:
        return redirect(url_for('login'))
    else:
        Tracker.query.filter_by(Tracker_ID=Tracker_ID).delete()
        Log.query.filter_by(l_Tracker_ID=Tracker_ID).delete()
        db.session.commit()
        return redirect(url_for('profile'))



@app.route('/add_log/<int:Tracker_ID>',methods=['GET', 'POST'])
def add_log(Tracker_ID):
    tracker = Tracker.query.filter_by(Tracker_ID = Tracker_ID)
    if request.method == 'POST':
        date = request.form['date']
        value = request.form['value']
        notes = request.form['notes']

        s=Log(Timestamp = date,l_student = g.user.email_address,l_Tracker_ID = Tracker_ID,value = value , notes = notes)
        db.session.add(s)
        db.session.commit()
        return redirect(url_for('profile'))

    elif tracker[0].Tracker_Type=='numerical':
        return render_template('add_log1.html',tracker = tracker)
    else:
        values = tracker[0].Settings
        values_list = values.split(",")
        return render_template('add_log2.html',tracker=tracker,values_list = values_list)


if __name__ == "__main__":
    database_path = os.path.join('database.sqlite3')
    if not os.path.isfile(database_path):
        with app.app_context():
            db.create_all()
    app.run()