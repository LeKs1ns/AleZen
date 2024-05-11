from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import random
from app.upload import upload_file, UPLOAD_FOLDER, ALLOWED_EXTENSIONS


db = sqlite3.connect("site.db", check_same_thread=False)
cursor = db.cursor()
    
query = """ 
    CREATE TABLE IF NOT EXISTS users (
    name VARCHAR(30),  
    login VARCHAR(30),
    id INTEGER PRIMARY KEY,
    balance INTEGER NOT NULL DEFAULT 0,
    password VARCHAR(20),
    filename VARCHAR DEFAULT NULL
    );
    CREATE TABLE IF NOT EXISTS casino (
    name VARCHAR(50),
    description TEXT(300),
    balance BIGINT NOT NULL DEFAULT 1000000)
    """
cursor.executescript(query)


app = Flask(__name__)
app.secret_key = "shuki" # FOR SESSION
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER # UPLOAD CONFIG

@app.route("/")
def home ():
    return render_template ("home.html")

@app.route("/registr")
def registr ():
    return render_template("reg.html")


@app.route("/registrindb", methods=['POST'])
def regindb():
    name = request.form.get('name')
    login = request.form.get('login')
    password = request.form.get('password')

    # Проверяем, был ли загружен файл (фото профиля)
    filename = None
    if 'file' in request.files:
        filename = upload_file()

    cursor.execute(f"SELECT * FROM users WHERE login=?", [login])
    if cursor.fetchone() is None:
        # Вставляем данные пользователя, включая filename, который может быть None
        cursor.execute("INSERT INTO users (name, login, password, filename) VALUES (?, ?, ?, ?)",
                       (name, login, password, filename))
        db.commit()

        # После успешной регистрации, устанавливаем сессионные данные
        user = cursor.execute("SELECT * FROM users WHERE login = ?", [login]).fetchone()
        session['user'] = user

        return redirect(f"/?message={name} Registered Successfully")
    else:
        return redirect("/registr?message=Login already exists, choose another one")


@app.route("/players")
def players_list():
    if 'user' in session:
        user_id = session['user'][2]
        if user_id == 1:
            p_list = cursor.execute("SELECT * FROM users")
            return render_template("players.html", players=p_list)
        else:
            return redirect(url_for("home"))
    else:
        return redirect(url_for("home"))

    
    
@app.route("/deleteplayer")
def deletebook():
    delid = request.args.get('delid')
    cursor.execute(f"DELETE FROM users WHERE id={delid}")
    db.commit()
    return redirect("/players?message=Player Deleted")


@app.route("/play")
def play_game():  
    if 'user' in session :
        user = session['user']
        return render_template("play.html", user=user)
    else:
        return redirect(url_for("log_in"))  
    

@app.route("/login")
def log_in():
    if 'user' in session:
        return render_template("home.html")
    else:
        return render_template("login.html")
    

@app.route("/logcheck", methods=['POST'])
def log_check ():
    login=request.form.get('login')
    password=request.form.get('password')
    cursor.execute(f"SELECT * FROM users  WHERE login=? AND password=?",[login, password])
    if cursor.fetchone() is None :
        return redirect("/login?message=Incorrect Login/User")
    else:
        user=cursor.execute(f"SELECT * FROM users  WHERE login=? AND password=?",[login, password]).fetchone()
        session["user"] = user  # insert user to session
        return render_template("home.html")


@app.route("/bet50", methods=['POST', 'GET'])
def bet_50():
    # Получение значений из формы
    bet = request.form.get('bet')
    stavka = request.form.get('stavka')
    user = session['user']
    number = random.randint(1, 12)

    # Проверка на наличие и корректность значения bet
    if not bet or not bet.isdigit() or int(bet) < 1:
        return redirect("/play?message=Please enter a valid bet amount to start the game")

    bet = int(bet)

    cursor.execute("SELECT balance FROM users WHERE login = ?", [user[1]])
    user_balance = cursor.fetchone()[0]

    if bet > user_balance:
        return redirect("/play?message=Your bet exceeds your current balance. Please place a valid bet.")

    # Проверка на наличие и корректность значения stavka
    if not stavka or not stavka.isdigit() or int(stavka) < 1 or int(stavka) > 12:
        return redirect("/play?message=Choose a number between 1 and 12 to start the game")

    stavka = int(stavka)

    if stavka != number:  # Игрок проигрывает
        cursor.execute("UPDATE users SET balance = balance - ? WHERE login = ?", [bet, user[1]])
        cursor.execute("UPDATE casino SET balance = balance + ?", [bet])
        db.commit()
        user = cursor.execute("SELECT * FROM users WHERE login = ?", [user[1]]).fetchone()
        session["user"] = user
        return redirect(f"/play?message=You lost {bet} $")
    else:
        cursor.execute("UPDATE users SET balance = balance + ? WHERE login = ?", [bet, user[1]])
        cursor.execute("UPDATE casino SET balance = balance - ?", [bet])
        db.commit()
        user = cursor.execute("SELECT * FROM users WHERE login = ?", [user[1]]).fetchone()
        session["user"] = user
        return redirect(f"/play?message=You won {bet} $")



@app.route("/profile")
def profile():
    user = session['user']
    return render_template("profile.html", user=user)


@app.route("/logout")
def log_out():
    if 'user' in session:
        session.pop("user", None)
        return redirect(url_for("log_in"))
    else:
        return redirect(url_for("home"))



#app.run(debug=True)