from flask import Flask, redirect, request, session, render_template, url_for, jsonify
# from flask_socketio import SocketIO, send
import requests
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secure random key for session management

CLIENT_ID = 'dbf2401566c6424794543f62af8f8252'
CLIENT_SECRET = '8b941b153ac34ec891cb5dec838dc275'
REDIRECT_URI = 'http://localhost:3000/callback'



@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login')
def login():
    scope = 'user-read-private playlist-read-private user-top-read'
    auth_url = f"https://accounts.spotify.com/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&scope={scope}"
    return redirect(auth_url)

@app.route('/callback')
def callback():
    error = request.args.get('error')
    if error:
        print("Received error from Spotify:", error)
        return f"Error from Spotify: {error}", 400

    code = request.args.get('code')
    if not code:
        print("No authorization code provided")
        return render_template('callback.html'), 400

    token_url = 'https://accounts.spotify.com/api/token'
    payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    response = requests.post(token_url, data=payload)
    print("Token exchange response:", response.json())  # Log response from Spotify

    if response.status_code != 200:
        print("Failed to retrieve access token:", response.text)
        return f"Failed to retrieve access token: {response.text}", response.status_code

    response_data = response.json()
    session['access_token'] = response_data.get('access_token')
    if not session['access_token']:
        print("Access token not found in response")
        return "Failed to retrieve access token", 500

    return redirect(url_for('home'))


@app.route('/profile')
def profile():
    print("Accessing profile...")
    access_token = session.get('access_token')
    if not access_token:
        print("Access token missing.")
        return 'Access Token Missing', 401

    headers = {'Authorization': f'Bearer {access_token}'}
    user_response = requests.get('https://api.spotify.com/v1/me', headers=headers)
    print(f"User API response: {user_response.status_code}")
    if user_response.status_code != 200:
        return f"Failed to retrieve user data: {user_response.text}", user_response.status_code

    user_data = user_response.json()

    playlists_response = requests.get('https://api.spotify.com/v1/me/playlists?limit=1', headers=headers)
    print(f"Playlists API response: {playlists_response.status_code}")
    if playlists_response.status_code != 200:
        return f"Failed to retrieve playlists: {playlists_response.text}", playlists_response.status_code
    
    playlists_data = playlists_response.json()
    top_playlist = playlists_data['items'][0] if playlists_data['items'] else None

    return render_template('profile.html', user=user_data, top_playlist=top_playlist)


@app.route('/home')
def home():
    if 'access_token' not in session:
        return redirect(url_for('login'))  # Redirect to login if no session token
    return render_template('home.html')  # Render the home page

@app.route('/messages')
def messages():
    # Your logic here, for example, rendering an HTML template
    return render_template('messages.html')

@app.route('/settings')
def settings():
    # Your logic here, for example, rendering an HTML template
    return render_template('settings.html')



@app.route('/logout')
def logout():
    # Clear the session, removing stored access tokens
    session.clear()
    return redirect(url_for('index'))

@app.route('/get_token', methods=['GET'])
def get_token():
    return jsonify({'access_token': session.get('access_token') })

if __name__ == '__main__':
    app.run(debug=True, port=3000)  # Fixed to port 3000 to match the REDIRECT_URI