import socket

@route("/") # this line is called a decorator
def get_index():
    return "index.html" # this is a FUNCTION STUB -- it's a placeholder, it doesn't work

def handle_request(request):
    # AI prompt idea:
    # use decorators/registration to create route functions
    # need to know what route the user is requesting, whether it's "/" or "/about", etc.
    # we want a function for each route

    # a decorator tells the server which function to call for which routes
    return


def start_server():
    server_socket = socket.socket() # creates a socket (the listening program)
    server_socket.bind(('localhost', 8000)) # set host and port (what's that?)
    server_socket.listen(1) # begin listening

    print("Listening on http://localhost:8000")


    while True: # infinite loop
        client_connection, client_address = server_socket.accept() # program waits on this line for a connection
        # we only proceed when we have someone trying to connect to localhost:8000
        request = client_connection.recv(1024).decode()
        handle_request(request) # requests come in a special format, this decodes it
        print(f"Received request:\n{request}") # print a message to terminal about this new request
        json_body = '{"message": "kigmi"}' # random message 
        response = ( # BEGIN response
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: application/json\r\n"
        "Access-Control-Allow-Origin: *\r\n" 
        f"Content-Length: {len(json_body)}\r\n"
        "\r\n"
        f"{json_body}"  
        ) # END response
        """try doing something like this instead of the above response...
        response = handle_request(request)
        """
        client_connection.sendall(response.encode()) # re-encode into special format, send back response
        client_connection.close() # close the connection
        # infinite loop restarts connection right away 

if __name__ == "__main__":
    start_server()

    # Try to ask AI to do one step at a time

    # 1. Encapsulate this code into a function

    # 2. Create a handle_request() function that uses decorator functions, instead of always returning the same thing

    # 3. Using decorators, add one route function for "/", i.e. @route("/")

    # 4. Make one route for "/" that returns index.html

    # Language:phython3 File:server.py To Run: python3 server.py
    # To see the server search localhost:8000
    # "curl" is used to search something, just like how google dooes


    #