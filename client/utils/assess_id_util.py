import re

def canon(assessId):
  """
  Takes an assessment/question's ID and canonicalizes it across iterations of
  a course.

  >>> canon(u'>>> foo\\n')
  '>>> foo\\n'
  >>> canon(u'cal/cs61a/fa15/lab01\\nVeritasiness\\n\\n>>> True and 13\\n72c74b6c7ed80d51f9fa7defbf7ed121\\n# locked\\n')
  '>>> True and 13\\nLOCKED_ANSWER\\n'
  >>> canon(u'cal/cs61a/fa15/lab01\\nVeritasiness\\n\\n>>> True and 13\\n13\\n>>> False or 0\\nb0754f6baafe74512d1be0bd5c8098ed\\n# locked\\n>>> not 10\\n5dfeeb9ca37d955606d40c6553cd4956\\n# locked\\n>>> not None\\n5154670fa295caf18cafa4245c1358a9\\n# locked\\n')
  '>>> True and 13\\n13\\n>>> False or 0\\nLOCKED_ANSWER\\n>>> not 10\\nLOCKED_ANSWER\\n>>> not None\\nLOCKED_ANSWER\\n'
  >>> canon(u'cal/cs61a/fa15/lab09\\nWhat would Scheme print?\\n\\nscm> (+ 3 5)\\n8\\nscm> (- 10 4)\\n6\\nscm> (* 7 6)\\n42\\nscm> (/ 28 2)\\n14\\nscm> (+ 1 2 3 4)\\n10\\nscm> (/ 8 2 2)\\n2\\nscm> (quotient 29 5)\\n5\\nscm> (remainder 29 5)\\neb5438773fa3774b23f3a524c49c4eb1\\n# locked\\n')
  'scm> (+ 3 5)\\n8\\nscm> (- 10 4)\\n6\\nscm> (* 7 6)\\n42\\nscm> (/ 28 2)\\n14\\nscm> (+ 1 2 3 4)\\n10\\nscm> (/ 8 2 2)\\n2\\nscm> (quotient 29 5)\\n5\\nscm> (remainder 29 5)\\nLOCKED_ANSWER\\n'
  >>> canon(u'cal/cs61a/fa15/lab09\\nWhat would Scheme print?\\n\\nscm> (+ 3 5) ; comment\\n8\\n')
  'scm> (+ 3 5)\\n8\\n'
  >>> canon(u'cal/cs61a/fa15/lab09\\nWhat would Scheme print?\\n\\nscm> (and #t #t)\\nTrue\\n')
  'scm> (and #t #t)\\nTrue\\n'
  """

  pHashAns = re.compile('[0-9,a-z,A-Z]{32}')

  aryLines = assessId.split('\n')
  aryCanonLines = []
  chrComment = '#'
  
  bHaveSeenFirstCodeLine = False
  for line in aryLines:
    line = line.strip()

    if not bHaveSeenFirstCodeLine:
      if len(line) > 0 and (line[0:3] == '>>>' or line[0:4] == "scm>"):
        bHaveSeenFirstCodeLine = True

      if line[0:4] == "scm>":
        chrComment = ';'

    # If False still in preamble and do not include in canon
    if bHaveSeenFirstCodeLine:
      # Remove any comments
      iComment = line.find(chrComment)
      if iComment >= 0:
        line = line[0:iComment]
        line = line.strip()

      # If a hashed answer, replace with constant since these vary by semester
      if pHashAns.match(line):
        line = 'LOCKED_ANSWER'

      # Remove any '# locked' text since these are here regardless of language
      if line == '# locked':
        line = ''

      if len(line) > 0:
        aryCanonLines.append(line+'\n')

  return ''.join(aryCanonLines)
