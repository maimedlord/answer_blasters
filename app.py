from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, redirect, render_template, request, session, url_for, flash
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
import processing as prc
import calls
from user import User


# NEXT AFTER LOGIN_USER - SEE FLASK-LOGIN DOCUMENTATION


app = Flask(__name__)

login_manager = LoginManager()
login_manager.init_app(app)

app.config['SECRET_KEY'] = 'secret!'# put in config file?


'''
INCOMPLETE
'''
@login_manager.user_loader
def user_loader(email):
    user_obj = calls.get_user_record_email(email)
    if user_obj:
        return User(email, user_obj['uName'])
    else:
        return None


'''
INCOMPLETE
'''
@app.route('/', methods=['post', 'get'])
def index():
    temp_array = prc.get_orders_top()
    if request.method == 'POST':
        email = request.form.get('user_email')
        password = request.form.get('user_password')
        user_obj = calls.is_auth_user(email, password)
        if user_obj:
            user_obj = User(email, user_obj['uName'])
            login_user(user_obj)
            # next = flask.request.args.get('next')
            # if not is_safe_url(next):
            #     return flask.abort(400)
            return render_template('account.html')
        else:
            print("failed login")
            return render_template('index.html', temp_array=temp_array)
    else:
        return render_template('index.html', temp_array=temp_array)


'''
INCOMPLETE
'''
@app.route('/account')
@login_required
def account():
    return render_template('account.html')


'''
INCOMPLETE
'''
@app.route('/logout')
def logout():
    temp_array = prc.get_orders_top()
    logout_user()
    return render_template('logout.html', temp_array=temp_array)


'''
INCOMPLETE
'''
@app.route('/register', methods=['post', 'get'])
def register():
    temp_array = prc.get_orders_top()
    if current_user.is_authenticated:
        return render_template('index.html', temp_array=temp_array)
    else:
        if request.method == 'POST':
            email = request.form.get('user_email')
            password1 = request.form.get('user_password1')
            password2 = request.form.get('user_password2')
            username = request.form.get('username')
            dict_template = {
                'active': True,
                'email': email,
                'pass': generate_password_hash(password1),
                'uName': username,
                'joinDate': 'some date for sure 2',
                'orders': []
            }
            result = calls.create_user(dict_template)
            if result:
                user_obj = User(email, username)
                login_user(user_obj)
                # next = flask.request.args.get('next')
                # if not is_safe_url(next):
                #     return flask.abort(400)
                return render_template('success.html')
            else:
                return render_template('index.html', temp_array=temp_array)

        return render_template('register.html', temp_array=temp_array)


'''
INCOMPLETE
'''
@app.route('/market')
def market():
    return render_template('market.html')


'''
INCOMPLETE
'''
@app.route('/success')
@login_required
def success():
    return render_template('success.html')


# '''
# INCOMPLETE
# '''
# @login_manager.unauthorized_handler
# def unauthorized():
#     temp_array = prc.get_orders_top()
#     return render_template('index.html', temp_array=temp_array)


if __name__ == '__main__':
    print(register())
    app.run(debug=True)
    #print(user_loader("theman@gmail.com"))

