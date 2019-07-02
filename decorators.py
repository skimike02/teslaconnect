from functools import wraps

from flask import redirect, url_for, session
import users

def check_confirmed(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        try:
            confirmed=users.ExecSQL(f'''SELECT confirmed FROM users WHERE username='{session['username']}';''')[0][0]
        except:
            confirmed=0
        if confirmed==0:
            return redirect(url_for('unconfirmed'))
        return func(*args, **kwargs)

    return decorated_function

def login_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('index'))
        return func(*args, **kwargs)

    return decorated_function