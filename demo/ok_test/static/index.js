// document.body.onload = addElement;

const answer1 = 'A';
const answer2 = 'B'

const mcq = ['A', 'B', 'C', 'D']
const qids = [['q1-A', 'q1-B', 'q1-C', 'q1-D'], ['q2-A', 'q2-B', 'q2-C', 'q2-D']]
async function save () {
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
      })
      .then(res => res.json())
      .then(json => {
           console.log(json['feedback']);
           console.log("Saved code!", json);
           addElement(json['feedback']);
      });
}
function addElement(feedback) {
    // create a new div element
    const newDiv = document.createElement("div");

    // and give it some content
    const newContent = document.createTextNode(feedback);

    // add the text node to the newly created div
    newDiv.appendChild(newContent);

    // add the newly created element and its content into the DOM
    const currentDiv = document.getElementById("save_button");
    document.body.insertBefore(newDiv, currentDiv);
}
