import json

strFileToWriteTo = 'simple-test.json'

dictJson = {
  'dictAssessId2WA2DictInfo': {
    "Test\n\n>>> 1 + 1 # OK will accept 'black' as right answer\ne74918d4310bb6cbc896676f20dc20de\n# locked\n>>> 2 + 2 # OK will accept 'black' as right answer\ne74918d4310bb6cbc896676f20dc20de\n# locked\n": {
      "['-2']": {
        'lstMisU': ["negation"],
        'ki': 1,
        'dictMisU2ReteachMsg': {
          'negation': 3,
        }
      },
      "['0']": {
        'lstMisU': ["offbytwo", "negation"],
        'ki': 1,
        'dictMisU2ReteachMsg': {
          'offbytwo': 2,
          'negation': 3,
        }
      },
      "['1']": {
        'lstMisU': ["offbyone"],
        'ki': 1,
        'dictMisU2ReteachMsg': {
          'offbyone': 2,
        }
      },
      "['3']": {
        'lstMisU': ["offbyone"],
        'ki': 1,
        'dictMisU2ReteachMsg': {
          'offbyone': 2,
        }
      },
      "['4']": {
        'lstMisU': ["offbytwo"],
        'ki': 1,
        'dictMisU2ReteachMsg': {
          'offbytwo': 2,
        }
      },
      "['100']": {
        'lstMisU': ["offbyone", "offbytwo"],
        'ki': 1,
        'dictMisU2ReteachMsg': {
          'offbyone': 2,
          'offbytwo': 2,
        }
      },
    },
  },
  'dictId2Msg': {
    1: 'KI: Try using your fingers to add',
    2: 'Reteach: Addition',
    3: 'Reteach: Negation',
  },
  'dictTg2Func': {
    0: "lambda info,strMisU: None",
    1: "lambda info,strMisU: info['ki']", # KI msg
    2: "lambda info,strMisU: info['dictMisU2ReteachMsg'][strMisU]", # Reteach msg
  },
  'url': 'TODO',
  'wrongAnsThresh': 2,
}
with open(strFileToWriteTo, 'w+') as f_out:
  json.dump(dictJson, f_out, sort_keys=True, indent=2, separators=(',', ': '))
