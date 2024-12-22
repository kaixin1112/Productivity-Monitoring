import uvicorn
import socket
import webbrowser

def get_local_ip():
    hostname = socket.gethostname()
    return socket.gethostbyname(hostname)

if __name__ == "__main__":
    ip = get_local_ip()
    port = 8000
    url = f"http://{ip}:{port}"

    print(f"Server running at: {url}")
    
    # Open the URL in the default web browser
    webbrowser.open(url)

    # Start the FastAPI server
    uvicorn.run("operator_pg:app", host=ip, port=port, reload=True)
