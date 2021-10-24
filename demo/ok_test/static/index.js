const answer1 = 'A';
const answer2 = 'B'

const mcq = ['A', 'B', 'C', 'D']
const qids = [['q1-A', 'q1-B', 'q1-C', 'q1-D'], ['q2-A', 'q2-B', 'q2-C', 'q2-D']]
const save = () => {
    const whichChecked = question_num => {
        options = qids[question_num]
        for (let i = 0; i < options.length; i++) {
            console.log(options[i])

            if (document.getElementById(options[i]).checked) {
                return mcq[i];
            }
        }
        return 'E';
    }
    const data = {
        'identity': {
            'code': whichChecked(0)
        },
        'negate': {
            'code' : whichChecked(1)
        }
    };
    fetch("/save", {
        method: "POST", 
        body: JSON.stringify(data),
        headers: {
            'Content-Type': 'application/json'
        }
      }).then(res => {
        console.log("Saved code!", res);
    });
}