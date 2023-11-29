
document.getElementById('signupForm').addEventListener('submit', function(event) {
    event.preventDefault();

    // Gets user inputted credentials from form
    var username = document.getElementById('username').value;
    var password = document.getElementById('password').value;
    var conf_password = document.getElementById('confirm_password').value;
    
    // Checks if username feild is blank
    if(username === "")
    {
        document.getElementById("output").innerHTML = "Input Username";
    }
    
    //Check if password feilds are blank
    else if(password === "" || conf_password === "")
    {
        document.getElementById("output").innerHTML = "Input Password(s)";
        //Checks of both passwords match
        if(password != conf_password)
            error = "Passwords Don't Match";
            document.getElementById("output").innerHTML = error;
    }
    
    //If checks are cleared request is sent to add account to database
    else{
        fetch('/signup_user', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username: username, password: password })
        })
        .then(response => response.json())
        .then(data => {
            //If the username already exists then user is promted to choose another one.
            if(data.message === 'exists')
                document.getElementById("output").innerHTML = "Username Exists";
            else if(data.message === 'success')
                //If account creation is successful, user is redirected to login page.
                location.href="login"
        });
    }
});