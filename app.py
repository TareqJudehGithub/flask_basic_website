from smtplib import SMTP
from datetime import datetime
import os

# Flask app:
from flask import Flask, render_template, request, flash, redirect

# Flask wtf-forms:
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email
from wtforms.fields.html5 import EmailField

# SQL Alchemy:
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Query

# CONSTANTS:
year = datetime.now().year
current_date = datetime.now().strftime("%x")
subscribers = set()
# Gmail credentials:
my_email_add = os.environ.get("EMAIL_ADD")
my_email_pass = os.environ.get("EMAIL_PASS")

# Instantiate Flask app:
app = Flask(__name__)

# wtf-forms secret key:
SECRET_KEY = os.environ.get("SECRET_KEY")
app.config["SECRET_KEY"] = SECRET_KEY

# SQL Alchemy:
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///friends.db"
app .config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize DB:
db = SQLAlchemy(app=app)


# Create DB model:
class Friends(db.Model):
    # Create db columns:
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.now)

    # Create a function to return a string, when we add something:
    def __repr__(self):
        # return "<Name %r>" % self.id
        return f"Name: {self.id}, {self.name}, {self.date_created}"


db.create_all()


# Form class
class NewsLetter(FlaskForm):
    first_name = StringField("First Name", validators=[DataRequired("Enter your first name.")])
    last_name = StringField("Last Name", validators=[DataRequired()])
    email = EmailField("Email Address", validators=[DataRequired(), Email()])
    submit = SubmitField("Submit")


# Friends class
class FriendsList(FlaskForm):
    first_name = StringField("First Name", validators=[DataRequired("Enter your first name.")])
    submit = SubmitField("Submit Me")


@app.route("/")
def index():
    title = "My Flask website"
    return render_template("index.html", title=title, year=year)


# About
@app.route("/about")
def about():
    about_list = ["fun", "friendly", "handsome"]
    return render_template("about.html", year=year, about_list=about_list)


# Subscribe
@app.route("/subscribe")
def subscribe():
    title = "Subscribe to my Newsletter"
    return render_template("subscribe.html", title=title, year=year)


# Form
@app.route("/form", methods=["GET", "POST"])
def form():
    # WTF Forms:
    first_name = None
    last_name = None
    email = None
    news_letter = NewsLetter()

    # Submit form:
    try:
        if news_letter.validate_on_submit():
            first_name = news_letter.first_name.data
            news_letter.first_name.data = ""
            last_name = news_letter.last_name.data
            news_letter.last_name.data = ""
            email = news_letter.email.data
            news_letter.email.data = ""
            subscribers.add(f"{first_name} {last_name} | {email.lower()}")

            message = "Thank you for subscribing in my newsletter."
            server = SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(user=my_email_add, password=my_email_pass)
            server.sendmail(
                from_addr=my_email_add,
                to_addrs=email,
                msg=f"Subject: Thank you, {first_name.title()}!\n\n{message}"
            )

    except:
        return "Form Submit Error."
    else:

        return render_template(
            "wtf_form.html",
            first_name=first_name,
            last_name=last_name,
            email=email,
            year=year,
            news_letter=news_letter
        )


# Friends route:
@app.route("/friends", methods=["GET", "POST"])
def friends():
    title = "MY friends list"
    friends_form = FriendsList()
    friend_name = None

    try:
        if friends_form.validate_on_submit():

            friend_name = friends_form.first_name.data
            friends_form.first_name.data = ""

            # Add friend_name the the database:
            new_friend = Friends(name=friend_name)

            # Push/save to DB:
            db.session.add(new_friend)
            db.session.commit()
            return redirect("/friends")

    except:
        return "Entry Error!"

    else:
        message = flash("Friend successfully added to the database!")
        # Show friends list from db in friends.html
        friends_list = Friends.query.order_by(Friends.name)

        return render_template(
            "friends.html",
            title=title,
            year=year,
            name=friend_name,
            friends_form=friends_form,
            message=message,
            friends_list=friends_list
        )


@app.route("/old-form", methods=["GET", "POST"])
def old_school_form():
    # Old School Forms:
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        message = "Thank you for subscribing in my newsletter."

        # Send contact an email:
        server = SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(user=my_email_add, password=my_email_pass)
        server.sendmail(
            from_addr=my_email_add,
            to_addrs=email,
            msg=f"Subject: Thank you, {first_name.title()}!\n\n{message}"
        )

        if not first_name or not last_name or not email:
            error_statement = "Form fields required."
            return render_template("form_fail.html", error_statement=error_statement)
        subscribers.add(f"{first_name} {last_name} | {email}")

        return render_template(
            "form.html",
            first_name=first_name,
            year=year
        )


@app.route("/friends_html", methods=["GET", "POST"])
def friends_html():
    try:
        if request.method == "POST":
            first_name = request.form.get("first_name")

            # Add a new friend to SQL:
            new_friend = Friends(name=first_name)
            db.session.add(new_friend)
            db.session.commit()

    except:
        return "SQL data entry Error!"

    else:
        friends_list = Friends.query.order_by(Friends.name)

        return render_template(
            "friends_list_old_form.html",
            friends_list=friends_list,
            year=year
        )


# Update records - HTML forms:
@app.route("/update_friends/<int:friend_id>", methods=["GET", "POST"])
def update_friends(friend_id):

    friend_to_update = Friends.query.get_or_404(friend_id)

    if request.method == "POST":
        friend_to_update.name = request.form["first_name"]
        try:
            # Update name field data in the html form: update_friends.html
            db.session.commit()
            return redirect("/friends_html")

        except:
            return "Error updating record"

    else:

        return render_template(
                "update_friends.html",
                friend_to_update=friend_to_update,
                friend_id=friend_id,
                year=year
            )


# Delete records - HTML forms:
@app.route("/delete_friends/<int:friend_id>", methods=["GET", "POST"])
def delete_friends(friend_id):
    friend_to_delete = Friends.query.get_or_404(friend_id)
    try:
        db.session.delete(friend_to_delete)
        db.session.commit()
        return redirect("/friends_html")

    except:
        return "Error deleting record."


# Not found route:
@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html", error=error,  year=year), 404


if __name__ == "__main__":
    app.run()



