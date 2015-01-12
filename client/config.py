sources = {
    # file pattern: serialize module
    'tests': 'ok_tests'
    '*.py': 'doctests',
    '*.scm': 'stk',
}

protocols = [
    'file_contents',
    'unlock',
    'lock',
    'grading',
    'scoring',
    'analytics',
]
