from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify, g
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

# def fetch_song_from_database(song_id, output_folder):
#     # MySQL database connection configuration
#     # Connect to the database
#     conn = connect_db()
#     cursor = conn.cursor()

#     try:
#         # Execute SELECT query to fetch BlobData
#         query = "SELECT BlobData, file_name FROM AudioFiles WHERE id = %s"
#         cursor.execute(query, (song_id,))
#         result = cursor.fetchone()

#         if result:
#             blob_data, file_name = result

#             # Write BlobData to a local file
#             output_path = os.path.join(output_folder, f"{file_name}.mp3")
#             with open(output_path, 'wb') as f:
#                 f.write(blob_data)
            
#             return output_path
#         else:
#             print(f"No song found with ID {song_id}")

#     except Exception as e:
#         print(f"Error fetching song: {e}")

#     finally:
#         # Close cursor and connection
#         cursor.close()
#         conn.close()




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
    video_resolution = data.get('videoResolution', '720p')
    video_quality = data.get('videoQuality', 'medium')
    image_duration = float(data.get('imageDuration', 3.0))  # Duration of each image in seconds
    transition_effect = data.get('transitionEffect', 'fade')
    
    # Create a temporary directory for processing
    import tempfile
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Set video parameters based on user selection
        resolution_map = {
            '480p': (640, 480),
            '720p': (1280, 720),
            '1080p': (1920, 1080),
        }
        frame_size = resolution_map.get(video_resolution, (1280, 720))
        fps = 24  # Frames per second
        
        # Set codec and bitrate based on quality
        if video_quality == 'high':
            codec = 'libx264'
            bitrate = '2000k'
        elif video_quality == 'medium':
            codec = 'libx264'
            bitrate = '1000k'
        else:  # low
            codec = 'libx264'
            bitrate = '500k'
        
        # Fetch audio file
        audio_file_path = os.path.join(temp_dir, f"audio_{song_id}.mp3")
        fetch_song_from_database(song_id, temp_dir)
        
        # If no audio file was found, return an error
        if not os.path.exists(audio_file_path):
            return jsonify({'error': 'Audio file not found'}), 404
        
        # Get audio duration using moviepy (more efficient than creating a full AudioFileClip)
        audio_clip = AudioFileClip(audio_file_path)
        audio_duration = audio_clip.duration
        
        # Calculate how many times to cycle through images
        num_images = len(images)
        if num_images == 0:
            return jsonify({'error': 'No images provided'}), 400
            
        total_image_duration = num_images * image_duration
        
        # Create output video file path
        output_video_path = os.path.join(temp_dir, 'output.mp4')
        final_output_path = os.path.join(temp_dir, 'final_video.mp4')
        
        # Preload and cache images to avoid repeated downloads
        cached_images = []
        for image_url in images:
            try:
                response = urllib.request.urlopen(image_url)
                image_data = np.asarray(bytearray(response.read()), dtype="uint8")
                image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
                image = cv2.resize(image, frame_size)
                cached_images.append(image)
            except Exception as e:
                print(f"Error loading image: {e}")
                # Use a black frame as fallback
                cached_images.append(np.zeros((frame_size[1], frame_size[0], 3), dtype=np.uint8))
        
        # Create video writer with optimized settings
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # mp4v is more universally compatible than x264
        out = cv2.VideoWriter(output_video_path, fourcc, fps, frame_size)
        
        # Calculate transition frames
        transition_frames = int(0.5 * fps)  # 0.5 seconds for transition
        
        # Generate video frames
        current_time = 0
        while current_time < audio_duration:
            for img_index, image in enumerate(cached_images):
                # Skip if we've exceeded audio duration
                if current_time >= audio_duration:
                    break
                    
                # Calculate frames for this image
                image_frames = int(image_duration * fps)
                
                # Apply effects based on transition_effect
                if transition_effect == 'fade':
                    # Fade in
                    for i in range(min(transition_frames, image_frames // 3)):
                        alpha = i / transition_frames
                        frame = cv2.addWeighted(
                            np.zeros_like(image), 1 - alpha, 
                            image, alpha, 0
                        )
                        out.write(frame)
                    
                    # Full visibility
                    for _ in range(image_frames - 2 * min(transition_frames, image_frames // 3)):
                        out.write(image)
                    
                    # Fade out
                    for i in range(min(transition_frames, image_frames // 3)):
                        alpha = 1 - (i / transition_frames)
                        frame = cv2.addWeighted(
                            np.zeros_like(image), 1 - alpha, 
                            image, alpha, 0
                        )
                        out.write(frame)
                        
                elif transition_effect == 'slide':
                    # Calculate next image for smooth transition
                    next_index = (img_index + 1) % len(cached_images)
                    next_image = cached_images[next_index]
                    
                    # Regular display
                    for _ in range(image_frames - transition_frames):
                        out.write(image)
                    
                    # Slide transition
                    for i in range(transition_frames):
                        offset = int((frame_size[0] * i) / transition_frames)
                        frame = image.copy()
                        frame[:, :frame_size[0]-offset] = image[:, offset:]
                        frame[:, frame_size[0]-offset:] = next_image[:, :offset]
                        out.write(frame)
                        
                else:  # No transition effect
                    for _ in range(image_frames):
                        out.write(image)
                
                current_time += image_duration
                if current_time >= audio_duration:
                    break
        
        # Release resources
        out.release()
        
        # Add audio to video using ffmpeg directly (more efficient than moviepy's write_videofile)
        import subprocess
        cmd = [
            'ffmpeg', '-y',
            '-i', output_video_path,
            '-i', audio_file_path,
            '-c:v', codec,
            '-b:v', bitrate,
            '-c:a', 'aac',
            '-strict', 'experimental',
            '-shortest',  # Important: end when the shortest input ends
            final_output_path
        ]
        
        subprocess.run(cmd, check=True)
        
        # Send the file as response and clean up after sending
        @after_this_request
        def cleanup(response):
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"Error removing temp directory: {e}")
            return response
            
        return send_file(final_output_path, mimetype='video/mp4', as_attachment=True)
        
    except Exception as e:
        # Clean up on error
        shutil.rmtree(temp_dir)
        print(f"Error in video creation: {str(e)}")
        return jsonify({'error': str(e)}), 500


# Helper function to ensure we clean up after response is sent
def after_this_request(f):
    if not hasattr(g, 'after_request_callbacks'):
        g.after_request_callbacks = []
    g.after_request_callbacks.append(f)
    return f


@app.after_request
def call_after_request_callbacks(response):
    for callback in getattr(g, 'after_request_callbacks', ()):
        callback(response)
    return response


def fetch_song_from_database(song_id, output_folder):
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
            output_path = os.path.join(output_folder, f"audio_{song_id}.mp3")
            with open(output_path, 'wb') as f:
                f.write(blob_data)
            
            return output_path
        else:
            print(f"No song found with ID {song_id}")
            return None

    except Exception as e:
        print(f"Error fetching song: {e}")
        return None

    finally:
        # Close cursor and connection
        cursor.close()
        conn.close()
if __name__ == '__main__':
    app.run(debug=True, port=5691)
