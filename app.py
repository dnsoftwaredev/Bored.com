import os
import sqlite3

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, activity_nop, usd
from flask.json import jsonify

# Configure application, UNDERSTOOD
app = Flask(__name__)

# Track the changes and show changes in real time for templates, UNDERSTOOD
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached => this means that you will actually see the newest
# version of your app. If cache is enabled => you make change to whatever file like css
# you won't see the actual change because what you see will be the cached website. UNDERSTOOD
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies) # UNDERSTOOD
# basically this configuration => will change the flask session to server-side sessions
# these sessions work exactly the same way as client side session. However, client
# now only send the refference id to server => server interpret it and then store data server side
# WHY? Because of a little bit of increased security + no sensitive information is transmitted in compared
# to client side cookies.
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# just use whatever from CS50, it just make sense
db = SQL("sqlite:///bored.db")

@app.route("/")
@login_required
def welcome():
    return render_template("welcome.html")


@app.route("/index")
@login_required
def index():
    # so this page will display the task that the user select
    activity_rows = db.execute("SELECT * FROM activity WHERE user_id = :id", id = session['user_id'])

    # now just render index no matter GET or POST as the method.
    return render_template("index.html", activity_rows=activity_rows)


@app.route("/login", methods=["GET", "POST"]) # Completed
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # if user's method is POST, or if the user actually submit info
    if request.method == "POST":

        # Is the user name empty?
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Is the password empty?
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember the user by putting his/her id into session["user_id"]
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout") # really nothing to see here
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


# this part of the code will probably be implement to
# get some activity information then display it on screen
# if the user want to he can click a button to add it to his activity list
# which is a database
@app.route("/activity", methods=["GET", "POST"])
@login_required
def activity():
    """Get the activity from the API then spit it out on the user screen"""
    # user reached route via post (as by submitting a form via POST)
    if request.method == "POST":

        # check if there is any # of participant
        if not request.form.get("number_of_participants"):
            return apology("must provide the number of participants", 400)

        # access the data from the form to get the number of participants that the user want
        number_of_participants = request.form.get("number_of_participants")

        # change the number_of_participants into int
        int_number_of_participants = int(number_of_participants)

        # handle the case that the user want an activity more than 8 or less than 1
        if int_number_of_participants > 8 or int_number_of_participants < 1:
            return apology("Between 1 and 8 please", 400)

        # activity_nop will generate data from boredapi.com and give back
        # a package that will be named "data"
        dataf = activity_nop(number_of_participants)
        if not dataf:
            return apology("Cannot access API, please retry", 400)

        # write to record the activity that the user received from the API
        db.execute("INSERT INTO record (user_id, activity, type, participants, price, accessibility) VALUES (:user_id, :activity, :type, :participants, :price, :accessibility)",
            user_id = session["user_id"],
            activity = dataf['activity'],
            type = dataf['type'],
            participants = int(dataf['participants']),
            price = float(dataf['price']),
            accessibility = float(dataf['accessibility']))

        # render the activity_provided.html with all the data displayed + the button to add the
        # activity into the user's portfolio
        return render_template("activity_provided.html", data=dataf)

    # user reached this route via get
    else:
        return render_template("activity.html")

@app.route("/activity_provided", methods=["GET", "POST"])
@login_required
def activity_provided():
    """After the user click on the add to my list button"""
    # user reached route via post (as by submitting a form via POST)
    if request.method == "POST":

        # Query the rows of data from record
        row = db.execute("SELECT * FROM record WHERE user_id = :id ORDER BY activity_id DESC LIMIT 1", id = session['user_id'])

        # Now add that data into activity table in bored.db
        db.execute("INSERT INTO activity (user_id, activity, type, participants, price, accessibility) VALUES (:user_id, :activity, :type, :participants, :price, :accessibility)",
            user_id = session["user_id"],
            activity = row[0]['activity'],
            type = row[0]['type'],
            participants = int(row[0]['participants']),
            price = float(row[0]['price']),
            accessibility = float(row[0]['accessibility']))

        # select the row[0] because that will be the latest data that is added
        return render_template("activity.html")

    # user reached this route via get
    else:
        return render_template("activity.html")


@app.route("/check", methods=["GET"])
def check():
    # return true if username available, else false, in JSON format
    if request.method == "GET":
        # take username as argument
        username = request.args.get("username")

        # if no such username, then username is free
        users = db.execute("SELECT username FROM users WHERE username=:username", username=username)
        if not users:
            return jsonify(True)
        else:
            return jsonify(False)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
      # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Check if the username is empty?
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Check if the password is empty?
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Check if the username is already exist
        if len(rows) == 1:
            return apology("username is already exist", 400)

        # Access form data:
        username = request.form.get("username")
        password = request.form.get("password")
        passwordhash = generate_password_hash(password)
        confirmation = request.form.get("confirmation")

        if password != confirmation:
            return apology("passwords do not match", 400)

        # Write into bored.db the username + password, inital point will be 0:
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, passwordhash)

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


# done dont touch these, UNDERSTOOD
def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors, should be good UNDERSTOOD
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

