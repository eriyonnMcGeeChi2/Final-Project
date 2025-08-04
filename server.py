import socket
import os
import urllib.parse
import hashlib
import sqlite3
import secrets
import time

conn = sqlite3.connect('login.db')
login_conn = sqlite3.connect('login.db')
sessions_conn = sqlite3.connect('sessions.db')
login_conn.row_factory = sqlite3.Row


def create_session(username):
    """Create a new session and store it in the database."""
    session_id = secrets.token_hex(16)
    expires_at = int(time.time()) + 3600  # 1 hour expiry
    cursor = sessions_conn.cursor()
    cursor.execute("INSERT INTO sessions (session_id, username, expires_at) VALUES (?, ?, ?)",
                   (session_id, username, expires_at))
    sessions_conn.commit()
    return session_id

def get_session(request):
    """Extract session_id from Cookie header and look up username."""
    headers = request.split('\r\n')
    cookies = [h for h in headers if h.lower().startswith('cookie:')]
    if not cookies:
        return None
    cookie_str = cookies[0].split(":", 1)[1].strip()
    cookie_parts = cookie_str.split(";")
    session_id = None
    for part in cookie_parts:
        if part.strip().startswith("session_id="):
            session_id = part.strip().split("=", 1)[1]
            break
    if not session_id:
        return None
    cursor = sessions_conn.cursor()
    cursor.execute("SELECT username, expires_at FROM sessions WHERE session_id=?", (session_id,))
    result = cursor.fetchone()
    if result and result[1] > int(time.time()):
        return result[0]  # username
    return None

def render_template(filename, context):
    """Replace {{key}} in file with context[key]."""
    content = get_file(filename)
    if isinstance(content, bytes):
        content = content.decode()
    for key, value in context.items():
        content = content.replace(f"{{{{{key}}}}}", str(value))
    return content

ROUTES = {}

def route(path):
    """Register a function as a route handler."""
    def decorator(func):
        ROUTES[path] = func
        return func
    return decorator

def get_file(filename, content_type="text/html"):
    """Retrieve a file from the server's directory and return its content
    as an HTTP response."""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, filename)
        if content_type.startswith("image/") or content_type.startswith("video/"):
            with open(file_path, "rb") as f:
                content = f.read()
            header = f"HTTP/1.1 200 OK\nContent-Type: {content_type}\n\n"
            response = header.encode("utf-8") + content
            return response
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return f"HTTP/1.1 200 OK\nContent-Type: {content_type}\n\n{content}"
    except Exception:
        if content_type.startswith("image/"):
            return b"HTTP/1.1 500 INTERNAL SERVER ERROR\n\nError loading file: " + filename.encode("utf-8") + " " + Exception.__str__(Exception).encode("utf-8")
        else:
            return f"HTTP/1.1 500 INTERNAL SERVER ERROR\n\nError loading file: {filename}"

def static_file_route(request, filename=None):
    if request == '':
        return None
    path = request.split(" ")[1]
    # Remove leading slash if present
    filename = path.lstrip("/")
    if not filename:
        return None  # No file specified, let normal routing handle
    ext = os.path.splitext(filename)[1].lower()
    # Only serve files with known static extensions
    content_type = {
        ".mp4": "video/mp4",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
        ".webp": "image/webp",
        ".avif": "image/avif",
        ".svg": "image/svg+xml",
        ".ico": "image/x-icon",
        ".css": "text/css",
        ".js": "application/javascript",
        ".json": "application/json",
        ".xml": "application/xml",
        ".pdf": "application/pdf",
        ".txt": "text/plain",
    }
    if ext in content_type:
        # Check if the file exists in the current directory
        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, filename)
        if os.path.isfile(file_path):
            return get_file(filename, content_type[ext])
    return None  # No static file found, let normal routing handle
# Patch handle_request to check static files if no route matches

def start_server():
    server_socket = socket.socket()
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('localhost', 8000))
    server_socket.listen(1)
    print("Listening on http://localhost:8000")
    while True:
        client_connection, client_address = server_socket.accept() # this line waits for a client to connect 
        request = client_connection.recv(1024).decode()
        print(f"Received request:\n{request}")
        response = handle_request(request)
        if isinstance(response, bytes):
            client_connection.sendall(response)
        else:
            client_connection.sendall(response.encode())
        client_connection.close() 

@route("/")
def index(request=None):
    """Serve the index page."""
    username = get_session(request) if request else None
    cursor = login_conn.cursor()
    cursor.execute("SELECT first_name, last_name FROM users WHERE username=?", (username,))
    row = cursor.fetchone()
    context = {}
    if row:
        context = dict(row)  # Convert to dict for easier access
    else:
        # If no user is logged in, just return the index without user data
        context = {"first_name": "Guest", "last_name": "User"}
    return render_template("index.html", context)

@route("/about")
def get_about(request=None):
    return get_file("about.html")

@route("/login")
def get_about(request=None):
    return get_file("login.html")
          
@route("/Register")
def get_index(request=None):
    return get_file("Register.html")





#New --- new handle request
def handle_request(request):
    try:
        path = request.split(" ")[1]
    except IndexError:
        path = "/"
    handler = ROUTES.get(path)
    if handler:
    # Pass the request to /api/login, otherwise call with no arguments
        return handler(request)
    # Check for static files (e.g., /images/filename)
    if request is not None:
        static_response = static_file_route(request)
    if static_response is not None:
        return static_response
    return "HTTP/1.1 404 NOT FOUND\n\nPage not found."



#New --- util functions
def hash_password(password):
    """Generate a random salt and hash the password. Returns (salt_hex, hash_hex)."""
    salt = os.urandom(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100_000)
    return salt.hex(), hashed.hex()

def hash_password_with_salt(password,salt):
    """Hash the password with the given salt."""
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 100_000)
    return hashed.hex()

# This function parses the form data from the HTTP request body and returns it as a Python dictionary.
def parse_form_data(request):
    """Extracts form data from the HTTP request body and returns a dict."""
    try:
        body = request.split('\r\n\r\n', 1)[1]
    except (IndexError, AttributeError):
        return {}
    # Decode URL-encoded form data
    return dict(urllib.parse.parse_qsl(body))



#New --- new routers
# This route serves login requests
@route("/api/login")
def login(request):
    # This part extracts (parses) the data from the request
    params = parse_form_data(request)
    username = params.get('username')
    password = params.get('password')
    # Check if username and password are provided
    if not username or not password:
        return "HTTP/1.1 400 BAD REQUEST\n\nMissing username or password."

    # Attempt to login by asking database for user-pass hash combo

    # connect to database
    cursor = conn.cursor()
    # Get this user's salt
    cursor.execute("SELECT salt, password_hash FROM users WHERE username=?", (username,))
    # Fetch the result
    # If the user does not exist, this will return None, a type of Python object that is basically "nothing"
    result = cursor.fetchone()
    if not result:
        # If the result is None, it means the user does not exist. 
        # Don't tell the user if it's the username or password that is wrong, just say "login failed"
        # This is a security measure to prevent attackers from knowing if the username exists.
        # This prevents brute force attacks where an attacker tries to guess the username and password.
        return "HTTP/1.1 401 UNAUTHORIZED\n\nLogin failed: Invalid username or password."
    # If the user exists, we get the salt and password hash from the database
    salt, stored_hash = result
    # Now we hash the password with the salt we got from the database
    password_hash = hash_password_with_salt(password, salt)
    if password_hash != stored_hash:
        return "HTTP/1.1 401 UNAUTHORIZED\n\nLogin failed: Invalid username or password."
    session_id = create_session(username)
    return (
        "HTTP/1.1 200 OK\n"
        f"Set-Cookie: session_id={session_id}; Path=/; HttpOnly; SameSite=Lax\n"
        "Content-Type: text/plain\n\n"
        "Success! Redirecting to home..."
    )

# This route adds a new user to the database
@route("/api/create_account")
def create_account(request):
    # Extract the form data from the request
    params = parse_form_data(request)
    username = params.get('username')
    password = params.get('password')
    first_name = params.get('first_name')
    last_name = params.get('last_name')
    email = params.get('email')
    # Check if all fields are provided
    if not username or not password or not first_name or not last_name or not email:
        return "HTTP/1.1 400 BAD REQUEST\n\nMissing required fields."

    cursor = conn.cursor()
    salt, password_hash = hash_password(password)
    try:
        cursor.execute("INSERT INTO users (username, salt, password_hash, first_name, last_name, email) VALUES (?, ?, ?, ?, ?, ?)",
                       (username, salt, password_hash, first_name, last_name, email))
        conn.commit()
        return "HTTP/1.1 201 CREATED\n\nUser created successfully."
    except sqlite3.IntegrityError:
        return "HTTP/1.1 409 CONFLICT\n\nUsername already exists."
    


start_server()

