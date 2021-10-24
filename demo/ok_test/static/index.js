const answer1 = 'A';
const answer2 = 'B'

const options = ['A', 'B', 'C', 'D']
const save = () => {
    const whichChecked = () => {
        for (const opt of options) {
            if (document.getElementById(opt).checked) {
                return opt;
            }
        }
        return 'E';
    }
    const data = {
        'identity': {
            'code': whichChecked()
        },
        'negate': {
            'code' : whichChecked()
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