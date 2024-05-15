from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify
import json
import bcrypt
import jwt
import base64
import time
import io
import os
import cv2
import numpy as np
import urllib.request
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip
from psycopg2.extras import DictCursor
from urllib.parse import urlparse
import psycopg2
import shutil
app = Flask(__name__)
app.secret_key = '$$$$##)($'
url = urlparse("postgresql://gojosatoru:FofLJPodx2IISjlBvRMffw@gojo-satoru-8985.8nk.gcp-asia-southeast1.cockroachlabs.cloud:26257/Gojosatoru?sslmode=verify-full")
db_params = {
    'dbname': url.path[1:],
    'user': url.username,
    'password': url.password,
    'host': url.hostname,
    'port': url.port
}
db = psycopg2.connect(**db_params)
cursor = db.cursor()
# Function to establish connection
def connect_db():
    return psycopg2.connect(**db_params)


# MySQL connection for 'images' database
mysq_params = {
    'dbname': url.path[1:],
# Connection parameters for PostgreSQL
    'user': url.username,
    'password': url.password,
    'host': url.hostname,
    'port': url.port# Updated to your database name
}
mysq =  psycopg2.connect(**mysq_params)

def verify_jwt_token(token):
    secret_key = '@#23$%^'
    try:
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None  # Token has expired
    except jwt.InvalidTokenError:
        return None  # Invalid token


def find_user_details(username):
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user_data = cursor.fetchone()
    if user_data:
        return {'username': user_data[1], 'email': user_data[3], 'password': user_data[2]}
    return None


def generate_jwt_token(username):
    payload = {'username': username}
    secret_key = '@#23$%^'
    expiration_time = 36000  # Set your desired expiration time in seconds
    token = jwt.encode({'exp': time.time() + expiration_time, **payload}, secret_key, algorithm='HS256')

    # Store token and user details in the session
    session['jwt_token'] = token
    session['user_details'] = {'username': username}

    return {'username': username, 'token': token}


@app.route('/playaudio/<int:song_id>')
def playaudio(song_id):
    connection = connect_db()
    connection=connection.cursor()
    connection.execute("SELECT blobData FROM audioFiles WHERE id = %s", (song_id,))
    blob_data = connection.fetchone()[0]
    connection.close()


    return send_file(io.BytesIO(blob_data), mimetype='audio/mpeg')


@app.route('/dis')
def dis():
    user_details = session.get('user_details')
    token = session.get('jwt_token')

    if user_details:
        username = user_details['username']
        payload = verify_jwt_token(token)

        if payload and payload['username'] == username:
            user_data = find_user_details(username)
            print(user_data)
    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("SELECT image FROM images WHERE user_name = %s", (username,))
    image_data = cursor.fetchall()
    
    cursor.execute("SELECT id, file_name, file_path FROM audiofiles")
    songs = cursor.fetchall()

    # Convert the list of tuples into a list of dictionaries
    songs_dict_list = []
    for song in songs:
        song_dict = {
            'id': song[0],
            'file_name': song[1],
            'file_path': song[2]
        }
        songs_dict_list.append(song_dict)
    songs=songs_dict_list
    cursor.close()
    connection.close()

    uploaded_images = []

    for data in image_data:
        try:
            encoded_image = base64.b64encode(data[0]).decode('utf-8')
            uploaded_image = f"data:image/jpeg;base64,{encoded_image}"
            uploaded_images.append(uploaded_image)
        except Exception as e:
            print(f"Error decoding image data: {e}")

    return render_template('create.html', uploaded_images=uploaded_images, songs=songs, data=user_data)

@app.route('/upload', methods=['POST'])
def upload():
    user_details = session.get('user_details')
    token = session.get('jwt_token')

    if user_details:
        username = user_details['username']
        payload = verify_jwt_token(token)

        if payload and payload['username'] == username:
            user_data = find_user_details(username)
            print(user_data)

    if request.method == 'POST':
        print("yes")
        images = request.files.getlist('images')

        try:
            con=connect_db()
            cur = con.cursor()
            print(images)
            for image in images:
                image_bytes = image.read()
                print(username)
                cur.execute("""
                    INSERT INTO images (user_id, image_metadata, image, user_name)
                    VALUES (%s, %s, %s, %s)""", (1, 'Metadata', (image_bytes), username))
                con.commit()

            cur.close()
            con.close()

            return redirect(url_for('uploadedimages'))
        except Exception as e:
            return f'An error occurred: {str(e)}'

    return 'No images were uploaded'


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        try:
            query = 'SELECT * FROM users WHERE username = %s'
            cursor.execute(query, (username,))
            data = cursor.fetchone()

            if data:
                stored_password =data[2]
                # stored_password = stored_password.replace('\\x24', '$')
                stored_password=bytes.fromhex(stored_password[2:]).decode('utf-8')
                print(stored_password)
                # print(password.encode())
                # Verify the entered password with the stored hashed password
                if bcrypt.checkpw(password.encode(), stored_password.encode()):
                    # Passwords match, log in the user
                    user_info = generate_jwt_token(username)
                    session['user_details'] = {'username': username}
                    session['jwt_token'] = user_info['token']
                    return redirect(url_for('success'))
                else:
                    flash("Invalid credentials", "error")
                    session['_reloaded'] = True
                    return render_template('mainpage.html')
            else:
                flash("User not found", "error")
                session['_reloaded'] = True
                return render_template('mainpage.html')

        except Exception as e:
            flash("An error occurred while processing your request.", "error")
            session['_reloaded'] = True
            print(f"Error: {e}")
            db.rollback()  # Assuming db is the connection object
            return render_template('mainpage.html')

    if session.get('_reloaded', False):
        session.pop('_reloaded')
        session.pop('_flashes', None)

    return render_template('mainpage.html')
@app.route('/success')
def success():
    token = session.get('jwt_token')
    if token:
        payload = verify_jwt_token(token)
        if payload:
            username = payload['username']
            user_data = find_user_details(username)
            return render_template('homepage.html', data=user_data, token=token)
        else:
            flash("Invalid or expired token", "error")
    else:
        flash("Token not provided", "error")
    return render_template('mainpage.html')


@app.route('/', methods=['GET', 'POST'])
def start():
    if session.get('_reloaded', False):
        session.pop('_reloaded')
        session.pop('_flashes', None)

    return render_template('mainpage.html')

@app.route('/admin',methods=['GET','POST'])
def admin():
    cur=db.cursor()
    cur.execute("SELECT username, email FROM users")
    users = cur.fetchall()
    cur.close()

    return render_template('index.html', users=users)
@app.route('/display')
def display():
    user_details = session.get('user_details')
    token = session.get('jwt_token')

    if user_details:
        username = user_details['username']
        payload = verify_jwt_token(token)

        if payload and payload['username'] == username:
            user_data = find_user_details(username)
            print(user_data)

    try:
        db = psycopg2.connect(**db_params)
        cursor = db.cursor()

        cursor.execute("SELECT image FROM images WHERE user_name = %s", (username,))
        image_data = cursor.fetchall()

        uploaded_images = []

        for data in image_data:
            try:
                encoded_image = base64.b64encode(data[0]).decode('utf-8')
                uploaded_image = f"data:image/jpeg;base64,{encoded_image}"
                uploaded_images.append(uploaded_image)
            except Exception as e:
                print(f"Error decoding image data: {e}")

        cursor.close()
        db.close()

        return render_template('display.html', uploaded_images=uploaded_images)
    except Exception as e:
        return f'An error occurred: {str(e)}'


@app.route('/signi', methods=['GET', 'POST'])
def signi():
    user_data = request.args.get('user_data')
    data = json.loads(user_data)
    return render_template('homepage.html', data=data)


@app.route('/display.html')
def display_page():
    token = request.args.get('token')
    if token:
        payload = verify_jwt_token(token)
        if payload:
            username = payload['username']
            user_data = find_user_details(username)
            print(user_data)

    return render_template('uploadimages.html', data=None, token=token)


@app.route('/uploadedimages', methods=['GET', 'POST'])
def uploadedimages():
    user_details = session.get('user_details')
    token = session.get('jwt_token')

    if user_details:
        username = user_details['username']
        payload = verify_jwt_token(token)

        if payload and payload['username'] == username:
            user_data = find_user_details(username)
            print(user_data)

    try:
        db = psycopg2.connect(**db_params)
        cursor = db.cursor()

        cursor.execute("SELECT image FROM images WHERE user_name = %s", (username,))
        image_data = cursor.fetchall()

        uploaded_images = []

        for data in image_data:
            try:
                encoded_image = base64.b64encode(data[0]).decode('utf-8')
                uploaded_image = f"data:image/jpeg;base64,{encoded_image}"
                uploaded_images.append(uploaded_image)
            except Exception as e:
                print(f"Error decoding image data: {e}")

        cursor.close()
        db.close()

        return render_template('uploaded.html', uploaded_images=uploaded_images)
    except Exception as e:
        return f'An error occurred: {str(e)}'



@app.route('/signup', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['name']
        email = request.form['email']
        password = request.form['password']

        db = connect_db()
        cursor = db.cursor(cursor_factory=DictCursor)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_email = cursor.fetchone()

        if existing_email:
            flash("Email already exists. Please choose a different email.", "error")
            session['_reloaded'] = True
            return render_template('mainpage.html')

        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("Username already exists. Please choose a different username.", "error")
            session['_reloaded'] = True
            return render_template('mainpage.html')

        salt_hash = bcrypt.gensalt()
        
# Hash the password using the generated salt
        hash_password = bcrypt.hashpw(password.encode(), salt_hash)
        print(hash_password)
        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                       (username, email, hash_password))
        db.commit()

        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        data1 = cursor.fetchone()
        user_data = {'username': data1['username'], 'email': data1['email'], 'password': data1['password']}

        token = generate_jwt_token(username)

        return redirect(url_for("signi", user_data=json.dumps(user_data), token=token))

    session.pop('_flashes', None)
    return render_template('mainpage.html')

# Create the 'users' table if it does not exist
def create_users_table():
    with connect_db() as db:
        with db.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                  id SERIAL PRIMARY KEY,
                  username VARCHAR(50) NOT NULL,
                  password VARCHAR(255) NOT NULL,
                  email VARCHAR(256) UNIQUE,
                  image_id INT8 NULL DEFAULT 1
                )
            """)
        db.commit()

# # Check if 'users' table exists
# def check_users_table():
#     with connect_db() as db:
#         with db.cursor() as cursor:
#             cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')")
#             return cursor.fetchone()[0]

# # Initialize the 'users' table if it doesn't exist
# if not check_users_table():
#     create_users_table()


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if session.get('_reloaded', False):
        session.pop('_reloaded')
        session.pop('_flashes', None)

    return render_template('mainpage.html')

def fetch_song_from_database(song_id, output_folder):
    # MySQL database connection configuration
    # Connect to the database
    conn = connect_db()
    cursor = conn.cursor()

    try:
        # Execute SELECT query to fetch BlobData
        query = "SELECT BlobData, file_name FROM AudioFiles WHERE id = %s"
        cursor.execute(query, (song_id,))
        result = cursor.fetchone()

        if result:
            blob_data, file_name = result

            # Write BlobData to a local file
            output_path = os.path.join(output_folder, f"{file_name}.mp3")
            with open(output_path, 'wb') as f:
                f.write(blob_data)
            
            return output_path
        else:
            print(f"No song found with ID {song_id}")

    except Exception as e:
        print(f"Error fetching song: {e}")

    finally:
        # Close cursor and connection
        cursor.close()
        conn.close()




def fade_in_out(image, fade_duration, fps):
    fade_frames = int(fade_duration * fps)
    height, width, _ = image.shape

    for i in range(fade_frames):
        alpha = i / fade_frames
        fade_in = cv2.addWeighted(image, alpha, np.zeros((height, width, 3), np.uint8), 1 - alpha, 0)
        fade_out = cv2.addWeighted(image, 1 - alpha, np.zeros((height, width, 3), np.uint8), alpha, 0)
        yield fade_in, fade_out

def slide(image, slide_duration, direction, fps):
    slide_frames = int(slide_duration * fps)
    height, width, _ = image.shape

    if direction == 'left':
        for i in range(slide_frames):
            offset_x = int((width / slide_frames) * i)
            slide_image = np.zeros((height, width, 3), np.uint8)
            slide_image[:, :width - offset_x] = image[:, offset_x:]
            yield slide_image
    elif direction == 'right':
        for i in range(slide_frames):
            offset_x = int((width / slide_frames) * i)
            slide_image = np.zeros((height, width, 3), np.uint8)
            slide_image[:, offset_x:] = image[:, :width - offset_x]
            yield slide_image
    elif direction == 'up':
        for i in range(slide_frames):
            offset_y = int((height / slide_frames) * i)
            slide_image = np.zeros((height, width, 3), np.uint8)
            slide_image[:height - offset_y, :] = image[offset_y:, :]
            yield slide_image
    elif direction == 'down':
        for i in range(slide_frames):
            offset_y = int((height / slide_frames) * i)
            slide_image = np.zeros((height, width, 3), np.uint8)
            slide_image[offset_y:, :] = image[:height - offset_y, :]
            yield slide_image



@app.route('/create-video', methods=['POST'])
def createvideo():
    data = request.get_json()
    images = data.get('images', [])
    song_id = data.get('songId')
    videoresolution = data.get('videoResolution')
    song=data.get('song')
    videoquality = data.get('videoQuality')
    print(videoresolution)
    print(videoquality)
    print(song)
    print(song_id)
    # Create video from images
    pwd = os.getcwd()

    # Define the name of the output folder
    output_folder_name = 'output'

    # Construct the full path for the output folder
    output_folder = os.path.join(pwd, output_folder_name)

    # Check if the output folder exists, if not, create it
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    print("Output folder path:", output_folder)

    audio_file_path = fetch_song_from_database(song_id, output_folder)

    video_filename = 'generated_video.mp4'

    video_resolution = data.get('videoResolution')
    video_quality = data.get('videoQuality')
    resolution_map = {
        '480p': (640, 480),
        '720p': (1280, 720),
        '1080p': (1920, 1080),
    }
    frame_size = resolution_map.get(video_resolution, (640, 480)) # Set your desired frame size
    fps = 24  # Adjust FPS as needed

    # if videoresolution:
    # frame_size = resolution_map[videoresolution]
    if videoquality == 'high':
        video_codec = 'mp4v'
    elif videoquality == 'medium':
        video_codec = 'xvid'
    else:
        video_codec = 'mjpg'  # Default codec

    out = cv2.VideoWriter(video_filename, cv2.VideoWriter_fourcc(*video_codec), fps, frame_size)

    # Extend the video until the audio ends
    audio_clip = AudioFileClip(audio_file_path)
    audio_duration = audio_clip.duration
    total_frames = int(audio_duration * fps)

    # Load all images and calculate the total duration for each image
    image_duration = data.get('imageDuration')  # Duration of each image in seconds
    print(image_duration)
    num_images = len(images)
    total_image_duration = num_images * image_duration

    # Calculate the number of times to repeat images to match the audio duration
    num_repeats = int(np.ceil(audio_duration / total_image_duration))

    for _ in range(num_repeats):
        for i, image_url in enumerate(images):
            # Decode image and convert to OpenCV format
            response = urllib.request.urlopen(image_url)
            image = np.asarray(bytearray(response.read()), dtype="uint8")
            image = cv2.imdecode(image, cv2.IMREAD_COLOR)
            image = cv2.resize(image, frame_size)
            transition_effect = data.get('transitionEffect')
            if transition_effect == 'fade':
                
                fade_duration = image_duration  # Fade duration in seconds
                fade_in_out_frames = fade_in_out(image, fade_duration, fps)

                for fade_in_frame, fade_out_frame in fade_in_out_frames:
                    out.write(fade_in_frame)
                out.write(fade_out_frame)
            elif transition_effect == 'slide':
                slide_duration = image_duration  # Slide duration in seconds
                slide_frames = slide(image, slide_duration, 'left', fps)  # Change direction as needed
                for slide_frame in slide_frames:
                    out.write(slide_frame)

    out.release()

    # Create a list of video clips to concatenate
    video_clips = []
    
    for _ in range(num_repeats):
        for _ in range(num_images):
            video_clips.append(VideoFileClip(video_filename))

    # Concatenate video clips
    final_clip = concatenate_videoclips(video_clips)

    # Set the duration of the video to match the audio duration
    final_clip = final_clip.set_duration(audio_duration)
    # Combine video with audio
    final_clip = final_clip.set_audio(audio_clip)

    # Output file path for the final video with audio
    shutil.rmtree(output_folder)
    output_file_path = os.path.join(os.getcwd(), 'f.mp4')
    print("Output file path:", output_file_path)

    # Write the final video with audio
    final_clip.write_videofile(output_file_path, codec='libx264', fps=fps)
    


    return send_file(output_file_path, mimetype='video/mp4', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5691)
