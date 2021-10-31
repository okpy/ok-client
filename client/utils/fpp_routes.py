from client.utils.fpp_utils import problem_to_hash
from flask import render_template, current_app, request, session, redirect, url_for
from datetime import datetime
from multiprocessing import Lock, Semaphore
import time
# from flask_login import current_user, login_required, login_user, logout_user

# found in nates __init__.py 
read_semaphore = Semaphore(12)

def get_next_problem(current_problem_name, current_problem_type):
  if current_problem_name == 'cs88_sp20/demographics_12':
    return "/multi/cs88_sp20/survey_12_fin"
  next_arg = request.args.get('next')
  final_arg = request.args.get('final')
  final_url_arg = '?'
  if final_arg:
    final_url_arg = '?final={}'.format(final_arg)
  if next_arg:
    return "/{}{}".format(next_arg, final_url_arg)

  # Unless otherwise specified, always show the solution (breaks some old studies :/)
  # if 'flow' not in session and current_problem_type in ['coding', 'code_arrangement', 'tracing']:
  if current_problem_type in ['coding', 'code_arrangement', 'tracing']:
    return '/solution/{}{}&disable_new_tab=1'.format(problem_to_hash(current_problem_name), final_url_arg)

# # If this problem has been loaded previously, get the time of the inital
# # loading.
# def get_problem_start(question_type, problem_name):
#   if 'disable_timer' in request.args:
#     return None
#   if question_type == 'multi' and problem_name == 'pre_test_comp_2':
#     if 'comp_start' in session:
#       return int((datetime.utcnow() - session['comp_start']).total_seconds())
#   with read_semaphore:
#     time.sleep(.4)
#     # TODO: See if this will mess up query limits significantly :/
#     try:
#       print("get problem start for user {}".format(current_user.id))
#       first_load = retry_query(lambda: Event.query.filter_by(
#           user_id=current_user.id,
#           question_name='{' + problem_name + '}',
#           question_type='{' + question_type + '}',
#           event_type='{load}'
#       ).order_by(Event.ts.asc()).first())
#     except:
#       first_load = None
#     if question_type == 'multi' and problem_name == 'pre_test_comp_2':
#       comp_start = datetime.utcnow()
#       if first_load:
#         comp_start = first_load.ts
#       session['comp_start'] = comp_start
#       int((datetime.utcnow() - session['comp_start']).total_seconds())
#     if first_load:
#       return int((datetime.utcnow() - first_load.ts).total_seconds())
#     return 1