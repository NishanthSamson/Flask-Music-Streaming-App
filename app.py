from flask import Flask, redirect, render_template, request, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore, login_required, current_user, UserMixin, RoleMixin, logout_user
from flask_security.utils import hash_password
from werkzeug.utils import secure_filename
from flask_bcrypt import *
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SECRET_KEY'] = 'MAD1PROJECT'
app.config['UPLOAD_FOLDER'] = 'static\\uploads'
app.config['SECURITY_PASSWORD_SALT'] = 'SALT'
db = SQLAlchemy(app)


class RolesUsers(db.Model):
    __tablename__ = "roles_users"
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column("user_id", db.Integer(), db.ForeignKey("user.id"))
    role_id = db.Column("role_id", db.Integer(), db.ForeignKey("role.id"))


class Role(db.Model, RoleMixin):
    __tablename__ = "role"
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))


class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = db.Column(db.Integer(), primary_key=True)
    email = db.Column(db.String(255), unique=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    img = db.Column(db.String(300), default='user.png')
    phone = db.Column(db.Integer())
    gender = db.Column(db.String(10))
    address = db.Column(db.String(300))
    active = db.Column(db.Boolean())
    fs_uniquifier = db.Column(db.String(255), unique=True, nullable=False)
    confirmed_at = db.Column(db.DateTime())
    songs = db.relationship('Songs', backref='user',
                            cascade="all, delete-orphan")
    roles = db.relationship(
        "Role", secondary="roles_users", backref=db.backref("users", lazy="dynamic")
    )


class Songs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    img = db.Column(db.String(300))
    duration = db.Column(db.Integer)
    genre = db.Column(db.String(50))
    rating = db.Column(db.Float)
    popularity = db.Column(db.Integer, default=0)
    lyrics = db.Column(db.String(3000))
    artist_id = db.Column(db.Integer, db.ForeignKey(
        'user.id'), nullable=False)
    album_id = db.Column(db.Integer, db.ForeignKey(
        'albums.id'))


class Albums(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    img = db.Column(db.String(300))
    desc = db.Column(db.String(1000))
    songs = db.relationship('Songs', backref='album',
                            cascade="all, delete-orphan")


class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    img = db.Column(db.String(300))
    desc = db.Column(db.String(1000))
    creator_id = db.Column(db.Integer, db.ForeignKey(
        'user.id'), nullable=False)
    songs = db.relationship(
        'Songs', secondary='playlist_songs', backref='playlists')

    playlist_songs = db.Table('playlist_songs',
                              db.Column('playlist_id', db.Integer, db.ForeignKey(
                                  'playlist.id'), primary_key=True),
                              db.Column('song_id', db.Integer, db.ForeignKey(
                                  'songs.id'), primary_key=True)
                              )


user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


with app.app_context():
    db.create_all()
    ADMIN_ROLE_NAME = 'admin'
    admin_role = Role.query.filter_by(name=ADMIN_ROLE_NAME).first()
    if not admin_role:
        admin_role = Role(name=ADMIN_ROLE_NAME,
                          description='Administrator role')
        db.session.add(admin_role)
        db.session.commit()

    ARTIST_ROLE_NAME = 'artist'
    artist_role = Role.query.filter_by(name=ARTIST_ROLE_NAME).first()
    if not artist_role:
        artist_role = Role(name=ARTIST_ROLE_NAME,
                           description='Artist role')
        db.session.add(artist_role)
        db.session.commit()

    USER_ROLE_NAME = 'user'
    user_role = Role.query.filter_by(name=USER_ROLE_NAME).first()
    if not user_role:
        user_role = Role(name=USER_ROLE_NAME,
                         description='User role')
        db.session.add(user_role)
        db.session.commit()

    a = user_datastore.find_user(email='admin@gmail.com')
    if a is None:
        user_datastore.create_user(username='admin',
                                   email='admin@gmail.com', password=hash_password('123'), roles=[admin_role])
        db.session.commit()


@app.route('/')
def index():
    user = "login" if not current_user.is_authenticated else current_user.username
    email = "" if not current_user.is_authenticated else current_user.email
    songs = Songs.query.all()
    playlists = Playlist.query.all()
    return render_template('index.html', songs=songs, playlists=playlists, user=user, email=email)


@app.route('/register', methods=['POST', 'GET'])
def register():
    artist_role = Role.query.filter_by(name=ARTIST_ROLE_NAME).first()
    user_role = Role.query.filter_by(name=USER_ROLE_NAME).first()
    if request.method == 'POST':
        uname = request.form.get('username')

        existing_user = User.query.filter_by(username=uname).first()
        if existing_user:
            flash(
                'Username is already taken. Please choose a different username.', 'error')
            return redirect(url_for('register'))

        user_datastore.create_user(
            email=request.form.get('email'), username=uname,
            password=hash_password(request.form.get('password')),
            roles=[artist_role if request.form.get(
                'role') == 'artist' else user_role]
        )
        db.session.commit()

        return redirect(url_for('account'))
    return render_template('register.html')


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


@app.route('/account')
def account():
    return render_template('account.html')


@app.route('/create/song', methods=['POST', 'GET'])
def create_song():
    uid = current_user.id
    if request.method == 'POST':
        file = request.files['song']
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        new_song = Songs(name=request.form.get('name'),
                         genre=request.form.get('genre'), duration=request.form.get('duration'), artist_id=uid, img=filename)
        db.session.add(new_song)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('create_song.html')


@app.route('/create/playlist', methods=['POST', 'GET'])
def create_playlist():
    uid = current_user.id
    if request.method == 'POST':
        file = request.files['img']
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        new_playlist = Playlist(name=request.form.get(
            'name'), desc=request.form.get('desc'), creator_id=uid, img=filename)
        selected_songs = request.form.getlist('selected_songs')
        for song_id in selected_songs:
            song = Songs.query.get(song_id)
            if song:
                new_playlist.songs.append(song)

        db.session.add(new_playlist)
        db.session.commit()

        return redirect(url_for('index'))
    songs = Songs.query.all()
    return render_template('create_playlist.html', songs=songs)


if (__name__ == '__main__'):
    app.run(debug=True)
