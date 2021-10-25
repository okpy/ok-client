# import http.server
# import socketserver
import os
import logging
import webbrowser
import importlib

from flask.helpers import send_from_directory
from flask import request, Flask, render_template, jsonify
from threading import Timer
from datetime import datetime

from client.api.assignment import load_assignment
from client.cli.common import messages


app = Flask(__name__, template_folder=f'{os.getcwd()}/static')
gargs = [None]

mcq_file_name = "mcq.py"
ok_file_name = "config.ok"

q1_code = """
def identity(x):
    return None
"""

q2_code = """
def negate(x):
    return None
"""
questions = {'identity': q1_code, 'negate': q2_code}
question_tests = {'identity': 'identity(1)', 'negate': 'negate(-2)'}
def initialize_files():
    # typically will be done on 61a/88 end (not here)
    with open(mcq_file_name, "w+") as f:
        for question in questions:
            f.write(f'# {question}')
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
    contents[cur_line] = f"  return '{mcq_answer}'\n"

    with open(mcq_file_name, "w") as f:
        f.writelines(contents)

@app.route("/save", methods=['POST'])
def save_code():
    print("save and run")
    if request.method == 'POST':
        data = request.json
        for question in data:
            print(data[question]['code'])
            write_mcq_prob_locally(question, data[question]['code'])
    # return {}
    # do some grading stuff
    args = gargs[0] # should be class variable later
    assign = load_assignment(args.config, args)
    msgs = messages.Messages()
    proto_name = "grading"
    module = importlib.import_module(assign._PROTOCOL_PACKAGE + '.' + proto_name)

    proto = module.protocol(assign.cmd_args, assign)
    log.info('Loaded protocol "{}"'.format(proto_name))
    log.info('Execute {}.run()'.format(proto_name))
    proto.run(msgs)
    print(msgs)
    msgs['timestamp'] = str(datetime.now())
    feedback = 'Correct!'
    print("finish save code")
    # now instead of printing the grading results, we need to send them back as a response to our JS save()
    # and then create an html element with feedback
    return jsonify({"feedback": feedback})
    # return render_template('index.html', opt1=4, feedback=feedback)

# @app.route("/<path:path>")
# def main(path):
#     print("main")
#     print(os.getcwd())
#     return send_from_directory(os.getcwd(), f'static/{path}')
#     # return render_template(f'{os.getcwd()}/static/index.html', opt1='1')

@app.route("/index.js")
def get_index():
    return send_from_directory(os.getcwd(), f'static/index.js')
    # return render_template(f'{os.getcwd()}/static/index.html', opt1='1')

def open_browser():
    webbrowser.open_new('http://127.0.0.1:3000/index.html')

@app.route('/index.html')
def index():
    print("index")
    print(os.getcwd())
    # return render_template(f'{os.getcwd()}/static/index.html')
    return render_template('index.html', q1=question_tests['identity'], q2=question_tests['negate'], feedback=None)

def open_in_browser(args):
    initialize_files()
    port = 3000
    gargs[0] = args
    Timer(1, open_browser).start()
    app.run(port=port)

# disable flask logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
os.environ['WERKZEUG_RUN_MAIN'] = 'true'
