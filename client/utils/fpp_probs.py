# from app import db, lock, read_semaphore
from flask import request, Flask, render_template, jsonify
# from flask_login import current_user, login_required, login_user, logout_user
from client.utils.fpp_utils import load_config, most_recent_parsons
from client.utils.fpp_routes import get_next_problem
import time
from multiprocessing import Semaphore
from threading import Timer
import webbrowser
import os
import json

from client.api.assignment import load_assignment
from client.cli.common import messages
from datetime import datetime
import importlib
import logging

# done in Nate's init
read_semaphore = Semaphore(12)
# db.init_app(app)
# app = Flask(__name__)
app = Flask(__name__, template_folder=f'{os.getcwd()}/templates', static_folder=f'{os.getcwd()}/static')

gargs = [None]
@app.route('/code_skeleton/<path:problem_name>')
# @login_required
def code_skeleton(problem_name):
  # return parsons(problem_name, code_skeleton=True)
  return parsons(problem_name, code_skeleton=False)


@app.route('/code_arrangement/<path:problem_name>')
# @login_required
def parsons(problem_name, code_skeleton=False):
  next_problem = get_next_problem(problem_name, "code_arrangement")
  back_url = None
  if request.args.get('final'):
    back_url = '/{}'.format(request.args.get('final'))

  # timer_start = get_problem_start('parsons', problem_name)
  timer_start = 0
  problem_config = load_config(problem_name)

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
                         language=language
                         )


@app.route('/submit/', methods=['POST'])
def submit():
    problem_name = request.form['problem_name']
    submitted_code = request.form['submitted_code']
    problem_config = load_config(problem_name)
    print("1")
    pre_test_code = problem_config['pre_test_code'] or ''
    test_code = problem_config['test_code'] or ''
    print(submitted_code)
    write_fpp_prob_locally(problem_name, submitted_code)
    print("wrote locally")
    #   try:
    #     grader_results = submit_to_grader(
    #         pre_test_code + submitted_code + test_code,
    #         problem_config['test_cases'], problem_config['test_fn'],
    #         problem_config['language'])
    #   except Exception as e:
    #     test_results = '<div class="testcase {}"><span class="msg">{}</span></div>'.format(
    #         "error", str(e))
    #     return json.dumps({'correct': 0, 'test_results': test_results})
    # test_results, correct = parse_results(grader_results)
    # print('\n')
    # print(current_user.sid_hash, current_user.consent, correct)
    # print('\n')

    feedback = grade_and_backup()
    test_results = '<div class="testcase {}"><span class="msg">{}</span></div>'.format("success", str("demo!"))
    correct = 0
    return jsonify({'feedback': feedback, 'test_results': test_results})
    # return "hi"
    # return json.dumps({'feedback': feedback, 'test_results': test_results})

def write_fpp_prob_locally(prob_name, code):
    cur_line = -1
    fname = f'fpp/{prob_name}.py'
    lines_so_far = []
    with open(fname, "r") as f:
        for i, line in enumerate(f):
            lines_so_far.append(line)
            if line.strip() == '# Enter your code here.':
                cur_line = i
                break

    assert cur_line >= 0, "Problem not found in file"

    code_lines = code.split("\n")
    code_lines.pop(0)

    with open(fname, "w") as f:
        for line in lines_so_far:
            f.write(line)
        for line in code_lines:
            f.write(line + "\n")

def grade_and_backup():
    args = gargs[0] # should be class variable later
    print("before load assign")
    assign = load_assignment(args.config, args)
    print("after load assign")

    msgs = messages.Messages()
    # proto_name = "grading"
    # module = importlib.import_module(assign._PROTOCOL_PACKAGE + '.' + proto_name)

    # proto = module.protocol(assign.cmd_args, assign)
    # log.info('Loaded protocol "{}"'.format(proto_name))
    # log.info('Execute {}.run()'.format(proto_name))
    # proto.run(msgs)
    print(msgs)
    msgs['timestamp'] = str(datetime.now())
    print(msgs)
    for name, proto in assign.protocol_map.items():
        print(name)
        log.info('Execute {}.run()'.format(name))
        proto.run(msgs)
    msgs['timestamp'] = str(datetime.now())
    feedback = 'Correct!'
    return feedback
    
def open_browser():
    demo_question = 'all_true'
    webbrowser.open_new(f'http://127.0.0.1:3000/code_skeleton/{demo_question}')


def open_in_browser(args):
    print("open in browser")
    gargs[0] = args
    port = 3000
    Timer(1, open_browser).start()
    app.run(port=port)

# disable flask logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
os.environ['WERKZEUG_RUN_MAIN'] = 'true'