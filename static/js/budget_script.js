/////////REDIRECT BUTTON FUNTIONALITY
document.getElementById("dashButton").addEventListener("click", function() {
    window.location.href = "/dashboard";
});

document.getElementById("logout").addEventListener("click", function() {
    cookie_name = "expense_tracker_cookie_container"
    document.cookie = `${cookie_name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
    window.location.href = '/';
});

encoded_id = getEncodedID_or_Landing();

// Request the expense types from the Python backend to populate the dropdown menu
var expenseTypeDropdown = document.getElementById("expenseType");
fetch('/get_expense_types', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({encoded_id:encoded_id}),         
})
.then(response => response.json())
.then(data => {
    var option = document.createElement("option");
    option.text = "";
    expenseTypeDropdown.add(option);
    for(x in data.types)
    {            
        var option = document.createElement("option");
        option.text = data.types[x];
        expenseTypeDropdown.add(option);
    }         
});

document.addEventListener('DOMContentLoaded', function () {
    // Fetch and display elements from the server
    
    getBudgetEntries();
});

function getBudgetEntries() {
    const dataGrid = document.getElementById('dataGrid');
    fetch('/get_budget_targets', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({encoded_id:encoded_id}),       
    })
    .then(response => response.json())
    .then(data => {        
        const tbody = dataGrid.querySelector('tbody');
        tbody.innerHTML = '';
        for (let key in data.types) 
        {
            const row = document.createElement('tr');

            row.innerHTML = `
            <td>${key}</td>
            <td>${data.types[key]}</td>
            `;
            tbody.appendChild(row); 
        }
               
    });
}

// When "Set/Update Budget" button is clicked the inputted values and if valid values are 
// sent to be inserted into the respective database. 
document.getElementById("confirmBudgetButton").addEventListener("click", function() {
    var expenseType = expenseTypeDropdown.value;
    var newBudgetAmount = document.getElementById("budgetAmount").value;

    if(expenseType == "")
    {
        document.getElementById("error").innerHTML = "Select Expense Type";
    }
    else if(newBudgetAmount == "")
    {
        document.getElementById("error").innerHTML = "Enter Valid Amount";
    }
    else
    {
        saveBudgetToDatabase(expenseType, newBudgetAmount);
        getBudgetEntries();
    }   
});

// Function to request the back-end to save to either update an existing budget value 
// amount or add a new entry depending on if one already exists.
function saveBudgetToDatabase(expenseType, newBudgetAmount) {  
      
    fetch('/save_budget', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ expenseType: expenseType, newBudgetAmount: newBudgetAmount, encoded_id:encoded_id})
    })
    .then(response => response.json())
}

function getEncodedID_or_Landing() {
    const cookies = document.cookie.split(';');
    cookie_name = "expense_tracker_cookie_container"
    for (const cookie of cookies) {
        const [name, value] = cookie.trim().split('=');

        if (name === cookie_name) {
            return value;
        }
    }
    location.href = '/';
}

