import os
import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps

# error reporting
def apology(message, code=400):
    def escape(s):

        """ https://github.com/jacebrowning/memegen#special-characters"""
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    # decorated function for login fucntion
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def activity_nop(number_of_people):
    """ Look up an activity based on # of participant"""

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

def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"
