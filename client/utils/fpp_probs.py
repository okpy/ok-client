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
# done in Nate's init
read_semaphore = Semaphore(12)
# db.init_app(app)
# app = Flask(__name__)
app = Flask(__name__, template_folder=f'{os.getcwd()}/templates', static_folder=f'{os.getcwd()}/static')
print(f'{os.getcwd()}/templates', "is the path")
@app.route('/code_skeleton/<path:problem_name>')
# @login_required
def code_skeleton(problem_name):
  print("skeleton", problem_name)
  return parsons(problem_name, code_skeleton=True)


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


def open_browser():
    demo_question = 'q1'
    webbrowser.open_new(f'http://127.0.0.1:3000/code_skeleton/{demo_question}')


def open_in_browser(args):
    print("open in browser")
    port = 3000
    Timer(1, open_browser).start()
    app.run(port=port)