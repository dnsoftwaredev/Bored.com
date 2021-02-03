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

# Configure application
app = Flask(__name__)

# track change in real time
app.config["TEMPLATES_AUTO_RELOAD"] = True

# No Cache
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# change flask session to serverside for max safety
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///bored.db")

@app.route("/")
@login_required
def welcome():
    return render_template("welcome.html")


@app.route("/index")
@login_required
def index():

    activity_rows = db.execute("SELECT * FROM activity WHERE user_id = :id", id = session['user_id'])


    return render_template("index.html", activity_rows=activity_rows)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Clear current id
    session.clear()


    if request.method == "POST":

        # Empty user name?
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Empty pw?
        elif not request.form.get("password"):
            return apology("must provide password", 403)


        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))


        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)


        session["user_id"] = rows[0]["id"]


        return redirect("/")


    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # clear session
    session.clear()


    return redirect("/")


# get activity
@app.route("/activity", methods=["GET", "POST"])
@login_required
def activity():

    # get activity from bored.com API
    if request.method == "POST":

        # no # of participant?
        if not request.form.get("number_of_participants"):
            return apology("must provide the number of participants", 400)

        number_of_participants = request.form.get("number_of_participants")

        int_number_of_participants = int(number_of_participants)

        # api only support 1 to 8 # of partcipants
        if int_number_of_participants > 8 or int_number_of_participants < 1:
            return apology("Between 1 and 8 please", 400)

        # check helpers
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

    else:
        return render_template("activity.html")

@app.route("/activity_provided", methods=["GET", "POST"])
@login_required
def activity_provided():
    """After the user click on the add to my list button"""

    if request.method == "POST":

        row = db.execute("SELECT * FROM record WHERE user_id = :id ORDER BY activity_id DESC LIMIT 1", id = session['user_id'])

        # Now add that data into activity table in bored.db
        db.execute("INSERT INTO activity (user_id, activity, type, participants, price, accessibility) VALUES (:user_id, :activity, :type, :participants, :price, :accessibility)",
            user_id = session["user_id"],
            activity = row[0]['activity'],
            type = row[0]['type'],
            participants = int(row[0]['participants']),
            price = float(row[0]['price']),
            accessibility = float(row[0]['accessibility']))

        # select row[0]
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

    else:
        return render_template("register.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)