from flask import Flask, render_template
app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/track/<int:id>')
def track(id):
    return render_template('track.html', id=id)


@app.route('/artist/<int:id>')
def artist(id):
    return render_template('artist.html', id=id)


@app.route('/user/<int:id>')
def user(id):
    return render_template('user.html', id=id)


@app.route('/album/<int:id>')
def album(id):
    return render_template('album.html', id=id)


if (__name__ == '__main__'):
    app.run(debug=True)
