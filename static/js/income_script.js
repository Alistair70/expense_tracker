document.getElementById("dashButton").addEventListener("click", function() {
    window.location.href = "/dashboard";
});
document.getElementById("logout").addEventListener("click", function() {
    cookie_name = "expense_tracker_cookie_container"
    document.cookie = `${cookie_name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
    window.location.href = '/';
});

encoded_id = getEncodedID_or_Landing();

// Request the income types from the Python backend to populate the dropdown menu
var incomeTypeDropdown = document.getElementById("incomeType");
fetch('/get_income_types', {
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
    incomeTypeDropdown.add(option);
    for(x in data.types)
    {            
        var option = document.createElement("option");
        option.text = data.types[x];
        incomeTypeDropdown.add(option);
    }         
});

document.addEventListener('DOMContentLoaded', function () {
    // Fetch and display elements from the server
    getIncomeTypes();
    getIncomeEntries();
});

// Function to get all the user's income types and append each of them a HTML list with 
// a button to delete it if the user requests to do so.
function getIncomeTypes() {
    const incomeTypesList = document.getElementById('incomeTypesList');
    fetch('/get_income_types', {
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
            type = data.types[x];
            li.textContent = data.types[x];
            li.dataset.id = data.types[x];
            const deleteButton = document.createElement('button');
            deleteButton.textContent = 'Delete';
            deleteButton.classList.add('btn_remove');
            deleteButton.addEventListener('click', function () {
                remove_income_type(type);
                location.reload();
            });
            li.appendChild(deleteButton);
            incomeTypesList.appendChild(li);
        }         
    });
}

//Function that takes an INCOME TYPE and sends a request to delete it from the database
function remove_income_type(incomeType) {
    fetch('/remove_income_type', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ incomeTypeTBR:incomeType , encoded_id:encoded_id }),
    })
    .then(response => response.json())    
    .catch(error => {
        console.error('Error:', error);
    });
}


//////////ADD NEW INCOME FOR THE USER TO SQL DATABASE FUNCIONALITY
//VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV

// When the "Add Income" button is clicked, it displays the respective form and hides all others.
document.getElementById("addIncomeBtn").addEventListener("click", function() {
    document.getElementById("incomeForm").style.display = "block";
    document.getElementById("addIncomeType").style.display = "none";
    document.getElementById("incomeEntries").style.display = "none";
});

// When "Confirm Income" button is clicked the inputted values are validated  
// and if valid values are sent to be inserted into the respective database. 
document.getElementById("confirmIncomeBtn").addEventListener("click", function() {
    var selectedIncomeTypeInput = incomeTypeDropdown.value;
    var amountInput = document.getElementById("amount").value;
    var dateInput = document.getElementById("userDate").value;
    
    if(selectedIncomeTypeInput == "" || amountInput == "" || dateInput == "" || parseFloat(amountInput).toFixed(2) < 0)
    {
        document.getElementById("error").innerHTML = "Enter Missing/Valid Values";
    }
    else
    {
        saveIncomeToDatabase(selectedIncomeTypeInput, amountInput, dateInput);
    }   
});

// Function to request the back-end to save to validated inputs from above and 
// saves them to the repesctive database.
function saveIncomeToDatabase(incomeType, amount, date) {    
    fetch('/add_income', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ incomeType: incomeType, amount: amount, date: date, encoded_id:encoded_id})
    })
    .then(response => response.json())
    .then(data => {
        if(data.message === 'success')
            location.reload();
    });
}

//////////DISPLAY ADD INCOME FROM WHEN BUTTON IS CLICKED
//VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV

//// Setion for adding new income type. Eg. Salary, Gift, Bonuses, ect...
// When the "Add Income Type" button is clicked, it displays the respective form and hides all others.
document.getElementById("addIncomeTypeBtn").addEventListener("click", function() {
    document.getElementById("incomeForm").style.display = "none";    
    document.getElementById("incomeEntries").style.display = "none";
    document.getElementById("addIncomeType").style.display = "block";
});

// When "Confirm Income Type" button is clicked the inputted values and if valid values are 
// sent to be inserted into the respective database. 
document.getElementById("confirmNewIncomeType").addEventListener("click", function() {
    var newIncomeTypeInput = document.getElementById("newIncome");    
    var newIncomeType = newIncomeTypeInput.value;
    if(newIncomeType == "")
    {
        document.getElementById("error").innerHTML = "Enter New Income Type";
    }
    else
    {
        saveIncomeTypeToDatabase(newIncomeType);
        location.reload();
    }   
});

// Function to request the back-end to save to validated inputs from above and 
// saves them to the repesctive database.
function saveIncomeTypeToDatabase(newIncomeType) {    
    fetch('/add_income_type', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ newIncomeType: newIncomeType , encoded_id:encoded_id})
    })
    .then(response => response.json())
    .then(data => {
        if(data.message === 'exists')
            document.getElementById("message").innerHTML = "Income Type Already Exists";
        else
            location.reload();
    });
}

//////////DELETE EXISTING INCOME ENTRIES FUNCIONALITY
//VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV

//// Section for retreiving currently saved income entries
// When the "Edit Income Entries" button is clicked, it displays the respective form and hides all others.
document.getElementById("editIncome").addEventListener("click", function() {
    document.getElementById("incomeForm").style.display = "none";
    document.getElementById("addIncomeType").style.display = "none";
    document.getElementById("incomeEntries").style.display = "block";
});

// Function to retrieve each of the user's recent income entries and appends them to a HTML table 
// as well as button to delete it if the user reques to do so.
function getIncomeEntries() {
    const dataGrid = document.getElementById('dataGrid');
    fetch('/get_recent_income', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({encoded_id:encoded_id})       
    })
    .then(response => response.json())
    .then(data => {
        console.log(data.entries)
        const tbody = dataGrid.querySelector('tbody');
        tbody.innerHTML = '';
        for(x in data.entries)
        {   
            const row = document.createElement('tr');

            row.innerHTML = `
            <td>${data.entries[x]['income_type']}</td>
            <td>${data.entries[x]['amount']}</td>
            <td>${data.entries[x]['date']}</td>
            <td><button class="delete-btn" onclick="deleteEntry(${data.entries[x]['income_id']})">Delete</button></td>
            `;
            tbody.appendChild(row);            
        }         
    });
}

//Function that takes the ID of a singular income entry and sends a request to delete it from the database
function deleteEntry(id) {
    fetch('/delete_income_entry', {        
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({incomeEntryTBR:id , encoded_id:encoded_id}) 
    })
    .then(response => response.json())
    .then(data => {
        if(data.status === 'success')
            getIncomeEntries();
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