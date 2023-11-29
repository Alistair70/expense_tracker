
document.getElementById('loginForm').addEventListener('submit', function(event) {
    event.preventDefault();

    // Gets user inputted credentials from form
    var username = document.getElementById('username').value;
    var password = document.getElementById('password').value;

    // Checks if username feild is blank
    if(username === "")
    {
        document.getElementById("output").innerHTML = "Input Username";
    }

    //Check if password feild is blank
    else if(password === "")
    {
        document.getElementById("output").innerHTML = "Input Password";
    }

    //If checks are cleared request is sent to backend to validate credentials
    else{
        fetch('/user_login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username: username, password: password })
        })
        .then(response => {
                //If Request is successful user is redirected to dashboard page
                if(response.status === 200) 
                {
                    location.href="dashboard"
                }  
                // If credentials are not valid, message is displayed to user showing "Incorrect Username/Password"
                else
                {
                    document.getElementById("output").innerHTML = "Incorrect Username/Password";
                } 
            })
        }
});