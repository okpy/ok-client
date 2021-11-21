# from app import db, lock, read_semaphore
import glob
from flask import request, Flask, render_template, jsonify, redirect, url_for

# from flask_login import current_user, login_required, login_user, logout_user
from client.utils.fpp_utils import load_config, FPP_FOLDER_PATH
from client.utils.fpp_routes import get_next_problem

import time
from multiprocessing import Semaphore
from threading import Timer
import webbrowser
import logging
from client.api.assignment import load_assignment
from client.cli.common import messages
from datetime import datetime
import importlib
import logging
from collections import OrderedDict
import os

PORT = 3000

FPP_OUTFILE = f"{FPP_FOLDER_PATH}/test_log"

# done in Nate's init
read_semaphore = Semaphore(12)

app = Flask(__name__, template_folder=f'{os.getcwd()}/templates', static_folder=f'{os.getcwd()}/static')

gargs = [None]
cache = {}
# removing whitespace makes me look at all lines. i could read one line at a time until MAX_LINES but is this better?
def get_prob_names():
    names_to_paths = OrderedDict()
    for name in glob.glob("fpp/*.py"):
        with open(name, "r") as f:
            cur_lines = f.readlines()
            for line in cur_lines:
                cur_words = line.split()
                if cur_words:
                    func_sig = cur_words[1]
                    names_to_paths[func_sig[:func_sig.index('(')]] = name[4:-3]
                    # names_to_paths[name[4:-3]] = func_sig[:func_sig.index('(')]
                    break
    return names_to_paths

# problem_names = [name[4:-3] for name in glob.glob("fpp/*.py") if name[4:-3] != '__init__']
names_to_paths = get_prob_names()
                
@app.route('/code_skeleton/<path:problem_name>')
# @login_required
def code_skeleton(problem_name):
  return parsons(problem_name, code_skeleton=False)

@app.route('/')
def index():
    return render_template('index.html')  

@app.route('/code_arrangement/<path:problem_name>')
# @login_required
def parsons(problem_name, code_skeleton=False):
  next_problem = get_next_problem(problem_name, "code_arrangement")
  back_url = None
  if request.args.get('final'):
    back_url = '/{}'.format(request.args.get('final'))

  # timer_start = get_problem_start('parsons', problem_name)
  timer_start = 0
  # problem_config = load_config(problem_name)
  problem_config = load_config(names_to_paths[problem_name])

  language = problem_config.get('language', 'python')

  with read_semaphore:
    time.sleep(.4)
    # most_recent_code = Event.most_recent_code(
    #     current_user.id, problem_name, 'parsons')
  if language == 'ruby':
    code_lines = problem_config['code_lines'] + \
        '\np !BLANK' * 3 + '\n# !BLANK' * 3
  elif language == 'js':
    code_lines = problem_config['code_lines'] + \
        '\nconsole.log(!BLANK)' * 3 + '\n// !BLANK' * 3
  else:
    code_lines = problem_config['code_lines'] + \
        '\nprint(!BLANK)' * 3 + '\n# !BLANK' * 3
  # if most_recent_code:
  #   code_lines = most_recent_parsons(most_recent_code, code_lines)
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
                         next_problem=next_problem,
                         back_url=back_url,
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
    # problem_config = load_config(problem_name)
    problem_config = load_config(names_to_paths[problem_name])
    pre_test_code = problem_config['pre_test_code'] or ''
    test_code = problem_config['test_code'] or ''
    write_fpp_prob_locally(problem_name, submitted_code)

    # test_results = '<div class="testcase {}"><span class="msg">{}</span></div>'.format("success", str("demo!"))
    test_results = grade_and_backup(problem_name)
    # test_results['num_cases'] = len(problem_config['test_cases'])
    return jsonify({'test_results': test_results})

def write_fpp_prob_locally(prob_name, code):
    cur_line = -1
    fname = f'{FPP_FOLDER_PATH}/{names_to_paths[prob_name]}.py'
    lines_so_far = []
    in_docstring = False
    with open(fname, "r") as f:
        for i, line in enumerate(f):
            lines_so_far.append(line)
            if line.strip() == '"""':
                if in_docstring:
                    cur_line = i
                    break
                in_docstring = True

    assert cur_line >= 0, "Problem not found in file"

    code_lines = code.split("\n")
    code_lines.pop(0) # remove function def statement

    with open(fname, "w") as f:
        for line in lines_so_far:
            f.write(line)
        for line in code_lines:
            f.write(line + "\n")

def grade_and_backup(problem_name):
    args = cache['args']
    args.question = [problem_name]
    assign = load_assignment(args.config, args)

    assign = load_assignment(args.config, args)
    msgs = messages.Messages()
    for name, proto in assign.protocol_map.items():
        # log.info('Execute {}.run()'.format(name))
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