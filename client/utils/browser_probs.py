# import http.server
# import socketserver
import os
import logging
import webbrowser

from flask.helpers import send_from_directory
from flask import request, Flask
from threading import Timer
import os

app = Flask(__name__)

@app.route("/save", methods=['POST'])
def save_code():
    if request.method == 'POST':
        data = request.json
        for question in data:
            with open(f"{question}.py", "w+") as f:
                f.write(data[question]['code'])
    return {}

@app.route("/<path:path>")
def main(path):
    print(os.getcwd())
    return send_from_directory(os.getcwd(), f'static/{path}')

def open_browser():
    webbrowser.open_new('http://127.0.0.1:3000/index.html')

def open_in_browser(args):
    port = 3000
    Timer(1, open_browser).start();
    app.run(port=port)

# disable flask logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
os.environ['WERKZEUG_RUN_MAIN'] = 'true'


"""
class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = 'test_page.html'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

# Create an object of the above class

def server_url(cmd_args):
    scheme = 'http' if cmd_args.insecure else 'https'
    return '{}://{}'.format(scheme, cmd_args.server)

def open_in_browser(cmd_args):
    # server = server_url(cmd_args)
    handler_object = MyHttpRequestHandler

    PORT = 8000
    my_server = socketserver.TCPServer(("", PORT), handler_object)

    # Start the server
    my_server.serve_forever()

# open_in_browser(None)
"""