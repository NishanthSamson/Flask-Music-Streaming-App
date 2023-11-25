from flask import Flask, redirect, render_template, request, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore, login_required, current_user, UserMixin, RoleMixin, logout_user
from flask_security.utils import hash_password
from werkzeug.utils import secure_filename
from flask_bcrypt import *
import os
import pygame
from mutagen.mp3 import MP3

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
    albums = db.relationship('Albums', backref='user',
                             cascade="all, delete-orphan")
    playlist = db.relationship('Playlist', backref='user',
                               cascade="all, delete-orphan")
    roles = db.relationship(
        "Role", secondary="roles_users", backref=db.backref("users", lazy="dynamic")
    )


class Songs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    song = db.Column(db.String(300))
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
    creator_id = db.Column(db.Integer, db.ForeignKey(
        'user.id'), nullable=False)
    songs = db.relationship(
        'Songs', secondary='album_songs', backref='albums')

    album_songs = db.Table('album_songs',
                           db.Column('album_id', db.Integer, db.ForeignKey(
                               'albums.id'), primary_key=True),
                           db.Column('song_id', db.Integer, db.ForeignKey(
                               'songs.id'), primary_key=True)
                           )


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


pygame.mixer.init()


@app.route('/')
def index():
    if current_user.is_authenticated and current_user.username == 'admin':
        return redirect(url_for('admin_manage'))
    a = session.get('current_song_id', 1)
    curr_song = Songs.query.filter_by(id=a).first()
    if not curr_song:
        curr_song = Songs(name='None', img='default.png')
    status = session.get('playpause', 'play')
    auth = current_user.is_authenticated
    user = "login" if not auth else current_user.username
    email = "" if not auth else current_user.email
    hide = "" if not auth else "hidden"
    log = "hidden" if not auth else ""
    songs = Songs.query.all()
    playlists = Playlist.query.all()
    albums = Albums.query.all()
    return render_template('index.html', songs=songs, playlists=playlists, user=user, email=email, hide=hide, log=log, albums=albums, curr_song=curr_song, status=status)


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


@app.route('/admin/manage')
def admin_manage():
    songs = Songs.query.all()
    playlists = Playlist.query.all()
    albums = Albums.query.all()
    return render_template('admin_manage.html', songs=songs, playlists=playlists, albums=albums)


@app.route('/song/<int:id>')
def view_song(id):
    status = session.get('playpause', 'play')
    song = Songs.query.filter_by(id=id).first()
    a = session.get('current_song_id', 1)
    curr_song = Songs.query.filter_by(id=a).first()
    if not curr_song:
        curr_song = Songs.query.first()
    return render_template('viewsong.html', song=song, curr_song=curr_song, status=status)


@app.route('/edit/song/<int:id>', methods=['POST', 'GET'])
def edit_song(id):
    song = Songs.query.get(id)
    if current_user.id == song.artist_id or current_user.id == 1:
        if request.method == 'POST':
            song.name = request.form.get('song_name')
            song.duration = request.form.get('song_duration')
            song.genre = request.form.get('song_genre')
            song.lyrics = request.form.get('song_lyrics')
            db.session.commit()

            return redirect(url_for('index'))
        return render_template('edit_song.html', song=song)
    return redirect(url_for('index'))


@app.route('/remove/song/<int:id>', methods=['POST', 'GET'])
def remove_song(id):
    song = Songs.query.get(id)
    if current_user.id == song.artist_id or current_user.id == 1:
        db.session.delete(song)
        db.session.commit()
    return redirect(url_for('index'))


@app.route('/artist/<int:id>')
def artist(id):
    return render_template('artist.html', id=id)


@app.route('/user/<int:id>')
def user(id):
    return render_template('user.html', id=id)


@app.route('/album/<int:id>')
def view_album(id):
    album = Albums.query.get(id)
    a = session.get('current_song_id', 1)
    curr_song = Songs.query.filter_by(id=a).first()
    if not curr_song:
        curr_song = Songs.query.first()
    status = session.get('playpause', 'play')
    if album:
        album_songs = album.songs
    return render_template('viewalbum.html', id=id, album_songs=album_songs, album=album, curr_song=curr_song, status=status)


@app.route('/edit/album/<int:id>', methods=['POST', 'GET'])
def edit_album(id):
    album = Albums.query.get(id)
    if current_user.id == album.creator_id or current_user.id == 1:
        if request.method == 'POST':
            album.name = request.form.get('album_name')
            album.desc = request.form.get('album_desc')
            db.session.commit()

            return redirect(url_for('index'))
        return render_template('edit_album.html', album=album)
    return redirect(url_for('index'))


@app.route('/remove/album/<int:id>', methods=['POST', 'GET'])
def remove_album(id):
    album = Albums.query.get(id)
    if current_user.id == album.creator_id or current_user.id == 1:
        db.session.delete(album)
        db.session.commit()
    return redirect(url_for('index'))


@app.route('/playlist/<int:id>')
def view_playlist(id):
    playlist = Playlist.query.get(id)
    a = session.get('current_song_id', 1)
    curr_song = Songs.query.filter_by(id=a).first()
    if not curr_song:
        curr_song = Songs.query.first()
    status = session.get('playpause', 'play')
    if playlist:
        playlist_songs = playlist.songs
    return render_template('viewplaylist.html', id=id, playlist_songs=playlist_songs, playlist=playlist, curr_song=curr_song, status=status)


@app.route('/edit/playlist/<int:id>', methods=['POST', 'GET'])
def edit_playlist(id):
    playlist = Playlist.query.get(id)
    if current_user.id == playlist.creator_id or current_user.id == 1:
        if request.method == 'POST':
            playlist.name = request.form.get('playlist_name')
            playlist.desc = request.form.get('playlist_duration')
            db.session.commit()

            return redirect(url_for('index'))
        return render_template('edit_playlist.html', playlist=playlist)
    return redirect(url_for('index'))


@app.route('/remove/playlist/<int:id>', methods=['POST', 'GET'])
def remove_playlist(id):
    playlist = Playlist.query.get(id)
    if current_user.id == playlist.creator_id or current_user.id == 1:
        db.session.delete(playlist)
        db.session.commit()
    return redirect(url_for('index'))


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

        cover = request.files['img']
        if cover:
            covername = secure_filename(cover.filename)
            cover.save(os.path.join(app.config['UPLOAD_FOLDER'], covername))

        new_song = Songs(name=request.form.get('name'),
                         genre=request.form.get('genre'), duration=request.form.get('duration'), artist_id=uid, song=filename, img=covername)
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


@app.route('/create/album', methods=['POST', 'GET'])
def create_album():
    uid = current_user.id
    if request.method == 'POST':
        file = request.files['img']
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        new_album = Albums(name=request.form.get(
            'name'), desc=request.form.get('desc'), creator_id=uid, img=filename)
        selected_songs = request.form.getlist('selected_songs')
        for song_id in selected_songs:
            song = Songs.query.get(song_id)
            if song:
                new_album.songs.append(song)

        db.session.add(new_album)
        db.session.commit()

        return redirect(url_for('index'))
    songs = Songs.query.filter_by(artist_id=uid)
    return render_template('create_playlist.html', songs=songs)


@app.route('/manage/songs')
def manage_songs():
    songs = Songs.query.filter_by(artist_id=current_user.id)
    return render_template('manage_songs.html', songs=songs)


@app.route('/manage/playlists')
def manage_playlists():
    playlists = Playlist.query.filter_by(creator_id=current_user.id)
    return render_template('manage_playlists.html', playlists=playlists)


@app.route('/manage/albums')
def manage_albums():
    albums = Albums.query.filter_by(creator_id=current_user.id)
    return render_template('manage_albums.html', albums=albums)


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/logout')
def logout():
    return redirect(url_for('index'))


@app.route('/play_pause')
def play_pause():
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.pause()
        session['playpause'] = 'play'
    else:
        pygame.mixer.music.unpause()
        session['playpause'] = 'pause'
    return "Success"


@app.route('/play/<int:song_id>')
def play(song_id=1):
    song = Songs.query.filter_by(id=song_id).first()
    full_path = os.path.join('static/uploads', song.song)
    pygame.mixer.music.load(full_path)
    pygame.mixer.music.play()
    audio = MP3(full_path)
    song_duration = audio.info.length
    session['current_song_id'] = song_id
    session['playpause'] = 'pause'
    return "Success"


@app.route('/next/<int:song_id>')
def get_next_song(song_id):
    try:
        a = int(song_id) + 1
        next_song = Songs.query.get(a)
    except:
        flash("Last song")
    if next_song:
        play(next_song.id)
    return "Success"


@app.route('/prev/<int:song_id>')
def get_prev_song(song_id):
    try:
        a = int(song_id) - 1
        prev_song = Songs.query.get(a)
    except:
        flash("First song")
    if prev_song:
        play(prev_song.id)
    return "Success"


if (__name__ == '__main__'):
    app.run(debug=True)
