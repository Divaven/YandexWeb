from flask import Flask, url_for, request, render_template, make_response, redirect
from data import db_session
from data.users import User
from data.user_sessions import UserSession
from data.friendships import Friendship
from data.games import Game

db_session.global_init("db/development.db")
db_sess = db_session.create_session()

app = Flask(__name__)

visits_count = 0


def check_if_user_signed_in(cookies, db_sess):
    return User.check_cookies(cookies, db_sess)


@app.route("/sign_in_user", methods=['POST'])
def sign_in_user():
    global visits_count
    current_user = check_if_user_signed_in(request.cookies, db_sess)
    if current_user:
        return redirect("/users/game")
    else:
        res = User.authenticate_user(request.form["login"], request.form["password"], db_sess)
        user = res[0]
        user_session = res[1]
        if None == user:
            return redirect("/sign_in/user_not_found")
        else:
            res = make_response(redirect("/"))
            res.set_cookie("user_secret", str(user_session.value),
                           max_age=60 * 60 * 24 * 365 * 2)
            return res


@app.route('/')
def landing():
    return redirect("/sign_in/введите пароль")


@app.route("/sign_in/<status>")
def sign_in(status):
    param = {
        "status": status
    }
    current_user = check_if_user_signed_in(request.cookies, db_sess)
    if current_user:
        return redirect("/users/game")
    else:
        param['yousername'] = "Ученик Яндекс.Лицея"
        param['title'] = 'Домашняя страница'
        param["array"] = [1, 2, 3, 4, 5]
        param["array_length"] = len(param["array"])
    return render_template('index.html', **param)


@app.route('/sign_up')
def sign_up():
    current_user = check_if_user_signed_in(request.cookies, db_sess)
    if current_user:
        return redirect("/users/game")

    param = {}
    return render_template('sign_up.html', **param)


@app.route("/sign_up_user", methods=["post"])
def sign_up_user():
    current_user = check_if_user_signed_in(request.cookies, db_sess)
    if current_user:
        return redirect("/users/game")

    res = User.create(request.form["login"], request.form["password"], db_sess)
    user = res[0]
    user_session = res[1]

    http_res = make_response(redirect("/"))
    http_res.set_cookie("user_secret", str(user_session.value),
                        max_age=60 * 60 * 24 * 365 * 2)
    return http_res


@app.route("/users/game")
def game():
    current_user = check_if_user_signed_in(request.cookies, db_sess)
    if not current_user:
        return redirect("/")

    g = Game.get_last_game(current_user, db_sess)
    your_mode = "X"
    if g.user_1_id != current_user.id:
        your_mode = "0"
    params = {
        "current_user": current_user,
        "game_in_html": g.to_html(current_user),
        "user_1": User.find_by_id(g.user_1_id, db_sess),
        "user_2": User.find_by_id(g.user_2_id, db_sess),
        "your_mode": your_mode
    }

    return render_template("game.html", **params)


@app.route("/users/scoreboard")
def scoreboard():
    current_user = check_if_user_signed_in(request.cookies, db_sess)
    params = {
        "users": User.all(db_sess),
        "current_user": current_user
    }
    return render_template("scoreboard.html", **params)


@app.route("/friends")
def friends():
    current_user = check_if_user_signed_in(request.cookies, db_sess)
    if not current_user:
        return redirect("/sign_in/для добавления в друзья нужно войти")
    params = {
        "users": map(lambda x: User.friendship_asked(x, db_sess), current_user.friends(db_sess)),
        "current_user": current_user
    }
    return render_template("friends.html", **params)


@app.route("/users/add_user/<user_id>")
def friend_user(user_id):
    current_user = check_if_user_signed_in(request.cookies, db_sess)
    if not current_user:
        return redirect("/sign_in/для добавления в друзья нужно войти")

    user = User.find_by_id(user_id, db_sess)

    Friendship.create_friendship(current_user, user, db_sess)

    params = {
        "users": map(lambda x: User.friendship_asked(x, db_sess), current_user.friends(db_sess)),
        "current_user": current_user
    }
    return render_template("friends.html", **params)


@app.route("/users/sign_out")
def sign_out():
    current_user = UserSession.sign_out(request.cookies, db_sess)
    return redirect("/")


@app.route("/games/make_move/<row>/<col>/<mode>")
def game_make_move(row, col, mode):
    current_user = check_if_user_signed_in(request.cookies, db_sess)
    g = Game.get_last_game(current_user, db_sess)
    g.make_move(int(col), int(row), mode, db_sess)
    # params = {
    #     "users": User.all(db_sess),
    #     "current_user": current_user
    # }
    return redirect("/users/game")


if __name__ == '__main__':
    app.run(port=8081, host='127.0.0.1')
