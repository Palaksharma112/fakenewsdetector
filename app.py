from flask import Flask, render_template, request, redirect, session
import sqlite3
import requests
from datetime import datetime

app = Flask(__name__)
app.secret_key = "fake_news_secret_key"


# ---------------- DATABASE ---------------- #

def create_database():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    # User Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)


    # History Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        news TEXT,
        result TEXT,
        date TEXT
    )
    """)


    conn.commit()
    conn.close()


create_database()


# ---------------- HOME ---------------- #

@app.route("/")
def home():
    return render_template("index.html")


# ---------------- REGISTER ---------------- #

@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        try:
            conn = sqlite3.connect("database.db")
            cur = conn.cursor()

            cur.execute(
                "INSERT INTO users(username,password) VALUES (?,?)",
                (username,password)
            )

            conn.commit()
            conn.close()

            return redirect("/login")


        except:
            return "User already exists"


    return render_template("register.html")



# ---------------- LOGIN ---------------- #

@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]


        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username,password)
        )

        user = cur.fetchone()

        conn.close()


        if user:
            session["user"] = username
            return redirect("/dashboard")

        else:
            return "Invalid username or password"


    return render_template("login.html")


# ---------------- CHECK NEWS ---------------- #

def check_news(news):

    api_key = "82ac496da08bf9bdc4cddb78136c871876d53c593ae460be3896abffd3cecebf"

    url = "https://api.freenewsapi.io/v1/news"

    headers = {
        "x-api-key": api_key
    }

    params = {
        "q": news,
        "language": "en",
        "order_by": "recent"
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        

        print("STATUS CODE:", response.status_code)
        print("CONTENT TYPE:", response.headers.get("Content-Type"))
        print("RESPONSE TEXT:")
        print(response.text)

        data = response.json()

        if data.get("data"):
            return "✅ Real News"
        else:
            return "⚠️ Suspicious / Fake News"

    except Exception as e:
        return f"ERROR: {e}"

# ---------------- DASHBOARD ---------------- #

@app.route("/dashboard", methods=["GET","POST"])
def dashboard():

    if "user" not in session:
        return redirect("/login")


    result = None


    if request.method == "POST":

        news = request.form["news"]


        result = check_news(news)


        conn = sqlite3.connect("database.db")
        cur = conn.cursor()


        cur.execute(
            """
            INSERT INTO history(username,news,result,date)
            VALUES (?,?,?,?)
            """,

            (
                session["user"],
                news,
                result,
                datetime.now().strftime("%d-%m-%Y %H:%M")
            )
        )

        conn.commit()
        conn.close()


    return render_template(
        "dashboard.html",
        result=result
    )


# ---------------- HISTORY ---------------- #

@app.route("/history")
def history():

    if "user" not in session:
        return redirect("/login")


    conn = sqlite3.connect("database.db")
    cur = conn.cursor()


    cur.execute(
        "SELECT news,result,date FROM history WHERE username=?",
        (session["user"],)
    )


    records = cur.fetchall()

    conn.close()


    return render_template(
        "history.html",
        records=records
    )


# ---------------- LOGOUT ---------------- #

@app.route("/logout")
def logout():

    session.pop("user",None)

    return redirect("/")


# ---------------- RUN APP ---------------- #

if __name__ == "__main__":
    app.run(debug=True)