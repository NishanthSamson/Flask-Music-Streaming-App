from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/song')
def song():
    return render_template('song.html')


@app.route('/artist')
def artist():
    return render_template('artist.html')


@app.route('/profile')
def profile():
    return render_template('profile.html')


if (__name__ == '__main__'):
    app.run(debug=True)
