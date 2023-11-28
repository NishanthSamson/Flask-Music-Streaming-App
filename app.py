from flask import Flask, redirect, render_template, request, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore, login_required, current_user, UserMixin, RoleMixin, logout_user
from flask_security.utils import hash_password
from werkzeug.utils import secure_filename
from flask_bcrypt import *
import os
import pygame
from mutagen.mp3 import MP3
from datetime import datetime

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
    duration = db.Column(db.String(10))
    genre = db.Column(db.String(50))
    rating = db.Column(db.Float, default=0.0)
    num_ratings = db.Column(db.Integer, default=0)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
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


def show():
    auth = current_user.is_authenticated
    if not auth:
        user = User(username='login', email=' ', img='default.png')
        log, hide = "hidden", ""
    else:
        user = User.query.get(current_user.id)
        log, hide = "", "hidden"
    return user, log, hide


@app.route('/')
def index():
    if current_user.is_authenticated and current_user.username == 'admin':
        return redirect(url_for('admin_manage_content'))
    a = session.get('current_song_id', 1)
    curr_song = Songs.query.filter_by(id=a).first()
    if not curr_song:
        curr_song = Songs(name='', img='default.png')

    status = session.get('playpause', 'play')

    user, log, hide = show()

    songs = Songs.query.order_by(Songs.date_added.desc()).all()
    playlists = Playlist.query.all()
    albums = Albums.query.all()

    return render_template('index.html', songs=songs, playlists=playlists, hide=hide, log=log, albums=albums, curr_song=curr_song, status=status, user=user)


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


@app.route('/admin/manage/content')
def admin_manage_content():
    songs = Songs.query.all()
    playlists = Playlist.query.all()
    albums = Albums.query.all()
    return render_template('admin_manage_content.html', songs=songs, playlists=playlists, albums=albums)


@app.route('/admin/manage/users')
def admin_manage_users():

    users = User.query.filter(User.id != 1).all()
    return render_template('admin_manage_users.html', users=users)


@app.route('/remove/user/<int:id>')
def remove_user(id):
    if id != 1:
        user = User.query.get(id)
        db.session.delete(user)
        db.session.commit()
    return redirect(url_for('index'))


@app.route('/song/<int:id>')
def view_song(id):
    status = session.get('playpause', 'play')
    song = Songs.query.filter_by(id=id).first()
    a = session.get('current_song_id', 1)
    curr_song = Songs.query.filter_by(id=a).first()
    user, log, hide = show()
    if song.rating != 0:
        rating = round((song.rating/song.num_ratings), 2)
    else:
        rating = 0
    if not curr_song:
        curr_song = Songs(name='', img='default.png')
    song.popularity += 1
    db.session.commit()
    return render_template('viewsong.html', song=song, curr_song=curr_song, status=status, user=user, log=log, hide=hide, rating=rating)


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


@app.route('/album/<int:id>')
def view_album(id):
    album = Albums.query.get(id)
    a = session.get('current_song_id', 1)
    curr_song = Songs.query.filter_by(id=a).first()
    if not curr_song:
        curr_song = Songs(name='', img='default.png')
    status = session.get('playpause', 'play')
    user, log, hide = show()
    if album:
        album_songs = album.songs
    return render_template('viewalbum.html', id=id, album_songs=album_songs, album=album, curr_song=curr_song, status=status, user=user, log=log, hide=hide)


@app.route('/edit/album/<int:id>', methods=['POST', 'GET'])
def edit_album(id):
    album = Albums.query.get(id)
    if current_user.id == album.creator_id or current_user.id == 1:
        songs = Songs.query.filter_by(artist_id=current_user.id)
        if request.method == 'POST':
            action = request.form.get('action')
            if action == 'add_song':
                new_song_id = request.form.get('add_song')
                new_song = Songs.query.get(new_song_id)
                album.songs.append(new_song)

            elif action == 'remove_song':
                song_id_to_remove = int(request.form.get('remove_song'))
                song_to_remove = Songs.query.get(song_id_to_remove)
                album.songs.remove(song_to_remove)

            if request.form.get('playlist_name') and request.form.get('playlist_duration'):
                album.name = request.form.get('album_name')
                album.desc = request.form.get('album_desc')

            db.session.commit()

            return redirect(url_for('index'))
        return render_template('edit_album.html', album=album, songs=songs)
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
        curr_song = Songs(name='', img='default.png')
    status = session.get('playpause', 'play')
    user, log, hide = show()
    if playlist:
        playlist_songs = playlist.songs
    return render_template('viewplaylist.html', id=id, playlist_songs=playlist_songs, playlist=playlist, curr_song=curr_song, status=status, user=user, log=log, hide=hide)


@app.route('/edit/playlist/<int:id>', methods=['POST', 'GET'])
def edit_playlist(id):
    playlist = Playlist.query.get(id)
    if current_user.id == playlist.creator_id or current_user.id == 1:
        songs = Songs.query.all()
        if request.method == 'POST':
            action = request.form.get('action')

            if action == 'add_song':
                new_song_id = request.form.get('add_song')
                new_song = Songs.query.get(new_song_id)
                playlist.songs.append(new_song)

            elif action == 'remove_song':
                song_id_to_remove = int(request.form.get('remove_song'))
                song_to_remove = Songs.query.get(song_id_to_remove)
                playlist.songs.remove(song_to_remove)

            if request.form.get('playlist_name') and request.form.get('playlist_duration'):
                playlist.name = request.form.get('playlist_name')
                playlist.desc = request.form.get('playlist_duration')

            db.session.commit()

            return redirect(url_for('index'))
        return render_template('edit_playlist.html', playlist=playlist, songs=songs)
    return redirect(url_for('index'))


@app.route('/remove/playlist/<int:id>', methods=['POST', 'GET'])
def remove_playlist(id):
    playlist = Playlist.query.get(id)
    if current_user.id == playlist.creator_id or current_user.id == 1:
        db.session.delete(playlist)
        db.session.commit()
    return redirect(url_for('index'))


@app.route('/account', methods=['POST', 'GET'])
def account():
    user = User.query.get(current_user.id)
    if request.method == 'POST':
        user.phone = request.form.get('phone')
        user.gender = request.form.get('gender')
        user.address = request.form.get('address')
        db.session.commit()

    return render_template('account.html', user=user)


@app.route('/create/song', methods=['POST', 'GET'])
def create_song():
    uid = current_user.id
    status = session.get('playpause', 'play')
    a = session.get('current_song_id', 1)
    curr_song = Songs.query.filter_by(id=a).first()
    user, log, hide = show()
    if not curr_song:
        curr_song = Songs(name='', img='default.png')
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
                         genre=request.form.get('genre'), duration=request.form.get('duration'), artist_id=uid, lyrics=request.form.get('lyrics'), song=filename, img=covername)
        db.session.add(new_song)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('create_song.html', hide=hide, log=log, curr_song=curr_song, status=status, user=user)


@app.route('/create/playlist', methods=['POST', 'GET'])
def create_playlist():
    uid = current_user.id
    status = session.get('playpause', 'play')
    a = session.get('current_song_id', 1)
    curr_song = Songs.query.filter_by(id=a).first()
    user, log, hide = show()
    if not curr_song:
        curr_song = Songs(name='', img='default.png')
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
    return render_template('create_playlist.html', songs=songs, hide=hide, log=log, curr_song=curr_song, status=status, user=user)


@app.route('/create/album', methods=['POST', 'GET'])
def create_album():
    uid = current_user.id
    uid = current_user.id
    status = session.get('playpause', 'play')
    a = session.get('current_song_id', 1)
    curr_song = Songs.query.filter_by(id=a).first()
    user, log, hide = show()
    if not curr_song:
        curr_song = Songs(name='', img='default.png')
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
    return render_template('create_playlist.html', songs=songs, hide=hide, log=log, curr_song=curr_song, status=status, user=user)


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


@app.route('/accprofilepic', methods=['GET', 'POST'])
def accprofilepic():
    if request.method == 'POST':
        file = request.files['img']
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            user = User.query.get(current_user.id)
            user.img = filename
            db.session.commit()
            return redirect(url_for('index'))
    return render_template('userpic.html')


@app.route('/search/results/', methods=['GET', 'POST'])
def search_results():
    status = session.get('playpause', 'play')
    user, log, hide = show()
    a = session.get('current_song_id', 1)
    curr_song = Songs.query.filter_by(id=a).first()
    if not curr_song:
        curr_song = Songs(name='', img='default.png')
    query_string = request.form.get('queryString')
    songs = Songs.query.filter(
        db.or_(
            Songs.name.ilike(f"%{query_string}%"),
            Songs.genre.ilike(f"%{query_string}%")
        )
    ).all()
    playlists = Playlist.query.filter(
        Playlist.name.ilike(f"%{query_string}%")).all()
    albums = Albums.query.filter(
        Albums.name.ilike(f"%{query_string}%")).all()

    return render_template('results.html', songs=songs, playlists=playlists, albums=albums, status=status, user=user, log=log, hide=hide, curr_song=curr_song)


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


@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.has_role('admin'):
        return redirect(url_for('index'))

    total_users = User.query.count()
    total_artists = User.query.filter(User.roles.any(name='artist')).count()
    total_songs = Songs.query.count()

    genre_stats = db.session.query(User.gender, Songs.genre, db.func.count().label('count')) \
        .join(Songs, User.id == Songs.artist_id) \
        .group_by(User.gender, Songs.genre).all()

    country_stats = db.session.query(User.address, Songs.name, db.func.count().label('count')) \
        .join(Songs, User.id == Songs.artist_id) \
        .group_by(User.address, Songs.name).all()
    return render_template('admin_dashboard.html',
                           total_users=total_users,
                           total_artists=total_artists,
                           total_songs=total_songs,
                           genre_stats=genre_stats,
                           country_stats=country_stats)


@app.route('/submit_rating/<int:song_id>', methods=['POST'])
def submit_rating(song_id):
    song = Songs.query.get(song_id)
    if not song:
        flash("Song not found")
        return redirect(url_for('index'))

    if request.method == 'POST':
        rating = int(request.form.get('rating'))
        new_rating = song.rating + rating
        new_num = song.num_ratings + 1
        song.rating = new_rating
        song.num_ratings = new_num
        db.session.commit()

        rate = "hidden"

        flash("Rating submitted successfully")

    return redirect(url_for('view_song', id=song_id))


@app.route('/user/<int:user_id>')
def view_user_profile(user_id):
    vuser = User.query.get(user_id)
    status = session.get('playpause', 'play')
    a = session.get('current_song_id', 1)
    curr_song = Songs.query.filter_by(id=a).first()
    user, log, hide = show()

    user_songs = Songs.query.filter_by(artist_id=user_id).all()
    user_playlists = Playlist.query.filter_by(creator_id=user_id).all()
    user_albums = Albums.query.filter_by(creator_id=user_id).all()

    if not curr_song:
        curr_song = Songs(name='', img='default.png')
    if not user:
        flash("User not found")
        return redirect(url_for('index'))

    return render_template('user_profile.html', vuser=vuser, hide=hide, log=log, curr_song=curr_song, status=status, user=user,
                           songs=user_songs, playlists=user_playlists, albums=user_albums)


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
