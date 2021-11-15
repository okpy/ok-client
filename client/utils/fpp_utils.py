import ast
import glob
import hashlib
import os
import time
import yaml
from yaml import Loader
import re

from collections import defaultdict
from pathlib import PosixPath

FPP_FOLDER_PATH = './fpp'
# PROBLEM_PATHS = ['problems/', 'app/cs88_parsons/problems/']
PROBLEM_PATHS = [FPP_FOLDER_PATH]
def load_config_file(paths):
  """
  Loads a YAML file.
  Args:
      path: A path to a YAML file.

  Returns: The contents of the YAML file as a defaultdict, returning None
      for unspecified attributes.

  """
  if type(paths) != list:
    paths = [paths]
  for path in paths:
    try:
      with open(os.path.abspath(path), 'r') as file:
        # investigate safe load later
        config = yaml.load(file, Loader=Loader)
        # config = yaml.safe_load(file)
      if type(config) == dict:
        config = defaultdict(lambda: None, config)
      return config
    except IOError as e:
      pass
  raise Exception("Cannot find files {0}".format(paths))


def load_config(file_name):
  """
  Loads a YAML file, assuming that the YAML file is located in the problems/PROBLEM_NAME.yaml directory.
  Args:
      file_name: The name of the directory in the data directory.
      root_path: Optional argument that specifies the root_path for problems.

  Returns: The contents of the YAML file as a defaultdict, returning None
      for unspecified attributes.
  """
  config_files = []
  for path in PROBLEM_PATHS:
    config_files.append(os.path.join(os.path.abspath(path), file_name + ".yaml"))
  return load_config_file(config_files)


def retry_query(query_fn):
  """
  Given a function, tries to run it 3 (+1) times. This is to help with flaky database issues.
  """
  # TODO: Instead of a flat-out retry, this should handle rollbacks more
  # appropriately.
  for _ in range(3):
    try:
      return query_fn()
    except:
      time.sleep(1)
  return query_fn()

# Dictionary where keys are hashes computed from problem_names and values
# are problem_names
hash_dict = {}


def md5_hash(s):
  return hashlib.md5(str.encode('88' + s)).hexdigest()


def problem_to_hash(problem_name):
  return md5_hash(problem_name)


def problems_iter():
  for path in PROBLEM_PATHS:
    # Find the number of folders defined in the paths to remove
    # fromt he assumed path prefix for hashing.
    folders_drop = path.count('/')
    for problem in PosixPath(path).glob('**/*.yaml'):
      # Remove problems/ from the path and .yaml from the filename.
      yield str(PosixPath(*problem.parts[folders_drop:]))[:-5]


def hash_to_problem(problem_hash):
  if problem_hash in hash_dict:
    return hash_dict[problem_hash]
  for problem_name in problems_iter():
    hash_dict[problem_to_hash(problem_name)] = problem_name
  return hash_dict[problem_hash]


def most_recent_parsons(most_recent_code, code_lines):
  recent_lines = most_recent_code.split('\n')[:-1]
  og_lines = code_lines.split('\n')
  given_regex = r'#(\d+)given\s*'
  blank_regex = r'#blank([^#]*)'
  original_regex = r'#!ORIGINAL(.*)'
  # Remove "#_given" and #blank_ in code_lines so we can find
  # each line from most_recent_code in code_lines
  for i, og_line in enumerate(og_lines):
    if re.search(given_regex, og_line):
      og_lines[i] = re.sub(given_regex, '', og_line).rstrip()
    if re.search(blank_regex, og_line):
      og_lines[i] = re.sub(blank_regex, '', og_lines[i]).rstrip()
  for i, recent_line in enumerate(recent_lines):
    split_by_tabs = recent_line.split('  ')
    num_tabs = len(split_by_tabs) - 1
    if re.search(original_regex, recent_line):
      original = re.findall(original_regex, recent_line)[0]
      index_of = og_lines.index(re.sub(blank_regex, '', original).rstrip())
      og_lines[index_of] = original
    else:
      index_of = og_lines.index(recent_line.lstrip())
    og_lines[index_of] += " #" + str(num_tabs) + "given"
    og_lines[i], og_lines[index_of] = og_lines[index_of], og_lines[i]
  return '\n'.join(og_lines)
