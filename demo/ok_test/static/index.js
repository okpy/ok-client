const code = 
`
def identity(x):
    return x
`;

const save = () => {
    const data = {
        'q1': {
            'code': code
        },
        'q2': {
            'code' : code
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