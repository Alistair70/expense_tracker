/////////REDIRECT BUTTON FUNTIONALITY
document.getElementById("dashButton").addEventListener("click", function() {
    window.location.href = "/dashboard";
});
document.getElementById("logout").addEventListener("click", function() {
    cookie_name = "expense_tracker_cookie_container"
    document.cookie = `${cookie_name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
    window.location.href = '/';
});

encoded_id = getEncodedID_or_Landing()

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
    getExpenseTypes();
    getExpenseEntries();
});

// Function to get all the user's expense types and append each of them a HTML list with 
// a button to delete it if the user requests to do so.
function getExpenseTypes() {
    const expenseTypesList = document.getElementById('expenseTypesList');
    fetch('/get_expense_types', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({encoded_id:encoded_id}),        
    })
    .then(response => response.json())
    .then(data => {
        
        for(x in data.types)
        {                    
            const li = document.createElement('li');
            li.textContent = data.types[x];
            type = data.types[x];
            li.dataset.id = data.types[x];
            const deleteButton = document.createElement('button');
            deleteButton.textContent = 'Delete';
            deleteButton.classList.add('btn_remove');
            deleteButton.addEventListener('click', function () {
                remove_expense_type(type);
                location.reload();
            });
            li.appendChild(deleteButton);
            expenseTypesList.appendChild(li);
        }         
    });
}

//Function that takes an INCOME TYPE and sends a request to delete it from the database
function remove_expense_type(expenseType) {
    fetch('/remove_expense_type', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ expenseTypeTBR:expenseType , encoded_id:encoded_id }), 
    })
    .then(response => response.json())
    .catch(error => {
        console.error('Error:', error);
    });
}

//////////ADD NEW EXPENSE FOR THE USER TO SQL DATABASE FUNCIONALITY
//VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV

// When the "Add Expense" button is clicked, it displays the respective form and hides all others.
document.getElementById("addExpenseBtn").addEventListener("click", function() {
    document.getElementById("expenseForm").style.display = "block";
    document.getElementById("addExpenseType").style.display = "none";
    document.getElementById("expenseEntries").style.display = "none";
});

// When "Confirm Expense" button is clicked the inputted values are validated  
// and if valid values are sent to be inserted into the respective database. 
document.getElementById("confirmExpenseBtn").addEventListener("click", function() {
    var expenseType = expenseTypeDropdown.value;
    var amount = document.getElementById("amount").value;
    var date = document.getElementById("userDate").value;


    if(expenseType == "" || amount == "" || date == "" || parseFloat(amount).toFixed(2) < 0)
    {
        document.getElementById("error").innerHTML = "Enter Missing/Valid Values";
    }
    else
    {
        saveExpenseToDatabase(expenseType, amount, date);
        location.reload();
    }   
});

// Function to request the back-end to save to validated inputs from above and 
// saves them to the repesctive database.
function saveExpenseToDatabase(expenseType, amount, date) {    
    fetch('/add_expense', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ expenseType: expenseType, amount: amount, date: date,encoded_id:encoded_id})
    })
    .then(response => response.json())
    
}

//////////CONFIRM NEW EXPENSE TYPE TO USER'S NOSQL DOCUMENT FUNCIONALITY
//VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV

//// Setion for adding new expense type. Eg. Groceires, Utilites, Tansporation, ect...
// When the "Add Expense Type" button is clicked, it displays the respective form and hides all others.
document.getElementById("addExpenseTypeBtn").addEventListener("click", function() {
    document.getElementById("expenseForm").style.display = "none";
    document.getElementById("addExpenseType").style.display = "block";
    document.getElementById("expenseEntries").style.display = "none";
});

// When "Confirm Expense Type" button is clicked the inputted values and if valid values are 
// sent to be inserted into the respective database. 
document.getElementById("confirmNewExpenseType").addEventListener("click", function() {
    var newExpenseTypeInput = document.getElementById("newExpense");    
    var newExpenseType = newExpenseTypeInput.value;
    if(newExpenseType == "")
    {
        document.getElementById("error").innerHTML = "Enter New Expense Type";
    }
    else
    {
        saveExpenseTypeToDatabase(newExpenseType);
        location.reload();
    }   
});

// Function to request the back-end to save to validated inputs from above and 
// saves them to the repesctive database.
function saveExpenseTypeToDatabase(newExpenseType) {    
    fetch('/add_expense_type', {
        method: 'POST',        
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ newExpenseType: newExpenseType,encoded_id:encoded_id})
    })
    .then(response => response.json())
    .then(data => {
        if(data.message === 'exists')
            document.getElementById("message").innerHTML = "Expense Type Already Exists";
        else
            location.reload();
    });
}


//////////DELETE EXISTING EXPENSE ENTRIES FUNCIONALITY
//VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV

//// Section for retreiving currently saved expense entries
// When the "Edit Expense Entries" button is clicked, it displays the respective form and hides all others.
document.getElementById("editExpense").addEventListener("click", function() {
    document.getElementById("expenseForm").style.display = "none";
    document.getElementById("addExpenseType").style.display = "none";
    document.getElementById("expenseEntries").style.display = "block";
});

// Function to retrieve each of the user's recent expense entries and appends them to a HTML table 
// as well as button to delete it if the user reques to do so.
function getExpenseEntries() {
    const dataGrid = document.getElementById('dataGrid');
    fetch('/get_recent_expenses', {
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
        for(x in data.entries)
        {   
            const row = document.createElement('tr');

            row.innerHTML = `
            <td>${data.entries[x]['expense_type']}</td>
            <td>${data.entries[x]['amount']}</td>
            <td><button class="delete-btn" onclick="deleteEntry(${data.entries[x]['expense_id']})">Delete</button></td>
            `;
            tbody.appendChild(row);          
        }         
    });
}

//Function that takes the ID of a singular expense entry and sends a request to delete it from the database
function deleteEntry(id) {
    fetch('/delete_expense_entry', {        
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({expenseEntryTBR:id , encoded_id:encoded_id}) 
    })
    .then(response => response.json())
    .then(data => {
        if(data.status === 'success')
            getExpenseEntries();
    })
    .catch(error => {
        console.error('Error:', error);
    });    
}

// Function used to set the date to today's date
function setTodayDate() {
    var dateInput = document.getElementById("userDate");
    var today = new Date();
    var dd = String(today.getDate()).padStart(2, '0');
    var mm = String(today.getMonth() + 1).padStart(2, '0'); 
    var yyyy = today.getFullYear();
    today = yyyy + '-' + mm + '-' + dd;
    dateInput.value = today;
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