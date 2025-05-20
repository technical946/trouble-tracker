from flask import Flask, render_template, request, redirect, url_for, session
from config import USER_CREDENTIALS

app = Flask(__name__)
app.secret_key = 'ini_kunci_rahasia_ubah_dulu'

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if (request.form['username'] == USER_CREDENTIALS['username'] and 
            request.form['password'] == USER_CREDENTIALS['password']):
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            error = 'Username atau password salah.'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)