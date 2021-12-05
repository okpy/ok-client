# from app import db, lock, read_semaphore
import glob
import sys
from flask import request, Flask, render_template, jsonify, redirect, url_for

# from flask_login import current_user, login_required, login_user, logout_user
from client.utils.fpp_utils import load_config, FPP_FOLDER_PATH
from client.utils.fpp_routes import get_next_problem
from client import exceptions as ex

import time
from multiprocessing import Semaphore
from threading import Timer
import webbrowser
import logging
from client.api.assignment import load_assignment
from client.cli.common import messages
from datetime import datetime
import logging
from collections import OrderedDict
import os

from client.utils.output import DisableLog, DisableStdout

PORT = 3000

FPP_OUTFILE = f"{FPP_FOLDER_PATH}/test_log"
FRONTEND_PATH = "fpp/faded-parsons-frontend/app"
utility_files = ["fpp/ucb.py"]
log = logging.getLogger('client')   # Get top-level logger

# done in Nate's init
read_semaphore = Semaphore(12)

app = Flask(__name__, template_folder=f'{os.getcwd()}/{FRONTEND_PATH}/templates', static_folder=f'{os.getcwd()}/{FRONTEND_PATH}/static')

cache = {}
# create map from problem names to file paths
# assumes problems are a
def get_prob_names():
    names_to_paths = OrderedDict()
    for name in glob.glob("fpp/*.py"):
        if name not in utility_files:
            with open(name, "r") as f:
                cur_lines = f.readlines()
                for line in cur_lines:
                    cur_words = line.lstrip().split()
                    if cur_words[0] == 'def':
                        func_sig = cur_words[1]
                        names_to_paths[func_sig[:func_sig.index('(')]] = name[4:-3]
                        break
    return names_to_paths

names_to_paths = get_prob_names()
                
@app.route('/code_skeleton/<path:problem_name>')
def code_skeleton(problem_name):
    return parsons(problem_name, code_skeleton=False)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/code_arrangement/<path:problem_name>')
def parsons(problem_name, code_skeleton=False):
    problem_config = load_config(names_to_paths[problem_name])
    language = problem_config.get('language', 'python')
    with read_semaphore:
        time.sleep(.4)

    #   code_lines = problem_config['code_lines'] + \
    #         '\nprint(!BLANK)' * 2 + '\n# !BLANK' * 2
    code_lines = problem_config['code_lines'] + '\nprint(!BLANK)'
    repr_fname = f'{FPP_FOLDER_PATH}/{names_to_paths[problem_name]}_repr'
    if os.path.exists(repr_fname):
        with open(repr_fname, "r") as f:
            code_lines = f.read()

    cur_prob_index = list(names_to_paths.keys()).index(problem_name)
    not_last_prob = cur_prob_index < len(names_to_paths) - 1
    not_first_prob = cur_prob_index > 0
    return render_template('parsons.html',
                         problem_name=problem_name,
                         algorithm_description=problem_config[
                             'algorithm_description'],
                         problem_description=problem_config[
                             'problem_description'],
                         test_cases=problem_config['test_cases'],
                         # TODO(nweinman): Better UI for this (and comment
                         # lines as well)
                         code_lines=code_lines,
                         next_problem=None,
                         back_url=None,
                         code_skeleton=code_skeleton,
                         language=language,
                         not_first_prob=not_first_prob,
                         not_last_prob=not_last_prob
                         )

@app.route('/next_problem/<path:problem_name>', methods=['GET'])
def next_problem(problem_name):
    new_prob_name = list(names_to_paths.keys())[list(names_to_paths.keys()).index(problem_name) + 1]
    return redirect(url_for('code_skeleton', problem_name=new_prob_name))


@app.route('/prev_problem/<path:problem_name>', methods=['GET'])
def prev_problem(problem_name):
    new_prob_name = list(names_to_paths.keys())[list(names_to_paths.keys()).index(problem_name) - 1]
    return redirect(url_for('code_skeleton', problem_name=new_prob_name))

@app.route('/get_problems/', methods=['GET'])
def get_problems():
    problem_paths = [f'/code_skeleton/{key}' for key in names_to_paths]
    return { 'names': list(names_to_paths.values()), 'paths': problem_paths}

@app.route('/submit/', methods=['POST'])
def submit():
    problem_name = request.form['problem_name']
    submitted_code = request.form['submitted_code']
    parsons_repr_code = request.form['parsons_repr_code']
    write_fpp_prob_locally(problem_name, submitted_code, parsons_repr_code, True)
    test_results = grade_and_backup(problem_name)
    return jsonify({'test_results': test_results})

@app.route('/analytics_event', methods=['POST'])
def analytics_event():
    """
    {
        problem_name: string,
        event: 'start' | 'stop'
    }
    Triggered when user starts interacting with the problem and when they stop (e.g. switch tabs). 
    This data can be used to get compute analytics about time spent on fpp.
    """
    e, problem_name = request.json['event'], request.json['problem_name']
    msgs = messages.Messages()
    args = cache['args']
    args.question = [problem_name]
    with DisableStdout():
        assign = load_assignment(args.config, args)
    if e == 'start':
        msgs['action'] = 'start'
    elif e == 'stop':
        msgs['action'] = 'stop'

    msgs['problem'] = problem_name
    analytics_protocol = assign.protocol_map['analytics']
    backup_protocol = assign.protocol_map['backup']
    # with DisableStdout():
    analytics_protocol.run(msgs)
    backup_protocol.run(msgs)

    msgs['timestamp'] = str(datetime.now())

    return jsonify({})

def write_fpp_prob_locally(prob_name, code, parsons_repr_code, write_repr_code):
    cur_line = -1
    in_docstring = False
    fname = f'{FPP_FOLDER_PATH}/{names_to_paths[prob_name]}.py'
    lines_so_far = []
    with open(fname, "r") as f:
        for i, line in enumerate(f):
            lines_so_far.append(line)
            if '"""' in line.strip():
                if in_docstring:
                    cur_line = i
                    break
                in_docstring = True

    assert cur_line >= 0, "Problem not found in file"

    code_lines = code.split("\n")
    code_lines.pop(0) # remove function def statement, is relied on elsewhere

    with open(fname, "w") as f:
        for line in lines_so_far:
            f.write(line)
        for line in code_lines:
            f.write(line + "\n")

    # write parsons repr code
    # used our own representation instead of Nate's most_recent_parsons()
    if write_repr_code:
        repr_fname = f'{FPP_FOLDER_PATH}/{names_to_paths[prob_name]}_repr'
        with open(repr_fname, "w") as f:
            f.write(parsons_repr_code)

def grade_and_backup(problem_name):
    args = cache['args']
    args.question = [problem_name]
    msgs = messages.Messages()
    
    # remove syntax errors so assignment can load
    num_retries = len(names_to_paths)
    reloaded = []
    assign = None
    while num_retries > 0:
        try:
            assign = load_assignment(args.config, args)
            break
        except ex.LoadingException as e:
            fname = str(e).split(" ")[-1]
            rel_path = fname.split("/")[1]
            prob_name = path_to_name(rel_path[:-3])
            reloaded.append(prob_name)
            # replace code with syntax error
            write_fpp_prob_locally(prob_name, "def dummy():\n  print('Syntax Error')\n", None, False)
            num_retries -= 1
    assert num_retries > 0, "Rewriting '' to fpp files failed"
    
    if assign:
        for name, proto in assign.protocol_map.items():
            log.info('Execute {}.run()'.format(name))
            proto.run(msgs)
        msgs['timestamp'] = str(datetime.now())
        feedback = {}
        feedback['passed'] = assign.specified_tests[0].console.cases_passed
        feedback['failed'] = assign.specified_tests[0].console.cases_total - feedback['passed']

    with open(FPP_OUTFILE, "r") as f:
        all_lines = f.readlines()
        # 8 assumes no docstring, this is a little sketch
        feedback['doctest_logs'] = "".join([all_lines[1]] + all_lines[8:])
    return feedback

def path_to_name(path):
    for key, val in names_to_paths.items():
        if val == path:
            return key

def open_browser():
    webbrowser.open_new(f'http://127.0.0.1:{PORT}/')

def open_in_browser(args):
    cache['args'] = args
    Timer(1, open_browser).start()
    run_server(PORT)

def run_server(port):
    # disable flask logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    os.environ['WERKZEUG_RUN_MAIN'] = 'true'
    app.run(port=port)