# Image to Video Converter

This web application allows users to upload images and convert them into a video with selected effects and quality settings. The backend is built using Flask and the application is deployed on Render. The database for storing user data and uploaded images is managed using CockroachDB.

## Features

- User Registration and Authentication
- Image Upload
- Video Creation with Selected Effects
- Quality Settings for Video Output
- Secure and Scalable Database Management

## Technologies Used

- **Backend**: Flask
- **Deployment**: Render
- **Database**: CockroachDB
- **Database URL**: `postgresql://gojosatoru:FofLJPodx2IISjlBvRMffw@gojo-satoru-8985.8nk.gcp-asia-southeast1.cockroachlabs.cloud:26257/Gojosatoru?sslmode=verify-full`

## Getting Started

### Prerequisites

- Python 3.7+
- Flask
- PostgreSQL client

### Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/your-username/image-to-video-converter.git
    cd image-to-video-converter
    ```

2. Create and activate a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

4. Set up environment variables. Create a `.env` file in the project root and add the following:
    ```
    FLASK_APP=app.py
    FLASK_ENV=development
    DATABASE_URL=postgresql://gojosatoru:FofLJPodx2IISjlBvRMffw@gojo-satoru-8985.8nk.gcp-asia-southeast1.cockroachlabs.cloud:26257/Gojosatoru?sslmode=verify-full
    ```

### Running the Application

1. Initialize the database:
    ```bash
    flask db upgrade
    ```

2. Run the Flask application:
    ```bash
    flask run
    ```

3. Open your web browser and navigate to `http://127.0.0.1:5000`.

## Usage

1. **Register an account**: Navigate to the registration page and create a new account.
2. **Login**: Use your credentials to log in.
3. **Upload Images**: Go to the upload page and select images to upload.
4. **Create Video**: Choose the desired effects and quality settings, then create the video.
5. **Download Video**: Once the video is created, you can download it directly from the application.

## Deployment

The application is deployed on Render and can be accessed at: [Image to Video Converter](https://gojosatoru.onrender.com)

## Database

The application uses CockroachDB for database management. The connection URL is as follows:
```postgresql://gojosatoru:FofLJPodx2IISjlBvRMffw@gojo-satoru-8985.8nk.gcp-asia-southeast1.cockroachlabs.cloud:26257/Gojosatoru?sslmode=verify-full```

Ensure that you have the necessary permissions and the database is up and running before starting the application.

## Contributing

We welcome contributions to enhance the features and improve the application. Please follow these steps to contribute:

1. Fork the repository.
2. Create a new branch:
    ```bash
    git checkout -b feature/your-feature-name
    ```
3. Commit your changes:
    ```bash
    git commit -m 'Add some feature'
    ```
4. Push to the branch:
    ```bash
    git push origin feature/your-feature-name
    ```
5. Open a pull request.


## Contact

For any questions or inquiries, please contact us at tiruveeduala.n@students.iiit.ac.in.

---

