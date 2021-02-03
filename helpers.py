import os
import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps

# just basically a function that return an url with top and bottom code according
# to what the user input in UNDERSTOOD
def apology(message, code=400):
    """Render an error message to the user."""
    def escape(s):
        """
        Escape special characters. This basically mean to just convert special character
        to things that the website memegen.link can understand and make a meme img.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login. This is basically magic. If you are willing to learn more
    head to the website below, else be ready for a pretty bad mind fuck.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def activity_nop(number_of_people):
    """ Look up an activity based on # of participant
    """

    # contact the bored API and get the number of people
    try:
        url = f"https://www.boredapi.com/api/activity?participants={number_of_people}"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        dataf = response.json()
        return {
            "activity": dataf["activity"],
            "type": dataf["type"],
            "participants": dataf["participants"],
            "price": dataf["price"],
            "accessibility": dataf["accessibility"]
        }
    except (KeyError, TypeError, ValueError):
        return None

# just leave this here for now. maynot have any use
def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"
