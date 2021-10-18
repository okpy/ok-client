# import http.server
# import socketserver
import os
import logging
import webbrowser

from flask.helpers import send_from_directory
from flask import request, Flask
from threading import Timer
import os

from client.api.assignment import load_assignment

app = Flask(__name__)
mcq_file_name = "mcq.py"
ok_file_name = "config.ok"

q1_code = """
# MCQ identity
def identity(x):
    return None
"""

q2_code = """
# MCQ negate
def negate(x):
    return None
"""
questions = {'q1': q1_code, 'q2': q2_code}

def initialize_files():
    # typically will be done on 61a/88 end (not here)
    with open(mcq_file_name, "w+") as f:
        for question in questions:
            f.write(questions[question] + "\n")

def write_mcq_prob_locally(prob_name, mcq_answer):
    cur_line = -1
    with open(mcq_file_name, "r") as f:
        for i, line in enumerate(f):
            values = line.split()
            if prob_name in values:
                cur_line = i + 2 # add 2 to get to return

    assert cur_line >= 0, "Problem not found in file"

    with open(mcq_file_name, "r") as f:
        contents = f.readlines()
    contents[cur_line] = f"  return '{mcq_answer}'"

    with open(mcq_file_name, "w") as f:
        f.writelines(contents)

@app.route("/save", methods=['POST'])
def save_code():
    if request.method == 'POST':
        data = request.json
        for question in data:
            write_mcq_prob_locally(question, data[question]['code'])
        
    return {}

@app.route("/<path:path>")
def main(path):
    print(os.getcwd())
    return send_from_directory(os.getcwd(), f'static/{path}')

def open_browser():
    webbrowser.open_new('http://127.0.0.1:3000/index.html')

def open_in_browser(args):
    initialize_files()
    port = 3000
    Timer(1, open_browser).start();
    app.run(port=port)

# disable flask logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
os.environ['WERKZEUG_RUN_MAIN'] = 'true'
