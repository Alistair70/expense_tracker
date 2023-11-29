/////////REDIRECT BUTTON FUNTIONALITY
document.getElementById("toIncome").addEventListener("click", function() {
    window.location.href = "/income";
});
document.getElementById("toExpense").addEventListener("click", function() {
    window.location.href = "/expenses";
});
document.getElementById("toBudget").addEventListener("click", function() {
    window.location.href = "/budget";
});
document.getElementById("logout").addEventListener("click", function() {
    fetch('/logout', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if(data.status === 'loggedOUT')
            window.location.href = "/";
    });
});

document.addEventListener('DOMContentLoaded', function () {
    // Fetch and display elements from the server
    income_v_expense();
    income_breakdown();
    expense_breakdown();
    budget_progress();
});

function income_v_expense() {
    fetch('/get_income_v_expense', {
        method: 'GET'        
    })
    .then(response => response.json())    
    .then(combinedData => {
        // Process combined data for Plotly
        const dates = combinedData.income.map(item => item.month);
        const incomeValues = combinedData.income.map(item => item.total_income);
        const expenseValues = combinedData.expenses.map(item => item.total_expenses);

        // Create Plotly chart
        const trace1 = {
            x: dates,
            y: incomeValues,
            type: 'scatter',
            mode: 'lines',
            name: 'Income',
            line: {color: 'blue'}
        };

        const trace2 = {
            x: dates,
            y: expenseValues,
            type: 'scatter',
            mode: 'lines',
            name: 'Expenses',
            line: {color: 'red'}
        };

        const layout = {
            title: 'Income and Expenses Over Time',
            xaxis: {
                title: 'Date'
            },
            yaxis: {
                title: 'Amount'
            }
        };

        Plotly.newPlot('income_expense_comparison', [trace1, trace2], layout);
    });
}

function income_breakdown() {
    fetch('/get_income_breakdown', {
        method: 'GET'        
    })
    .then(response => response.json())    
    .then(data => {        
        // Extract unique income types
        const incomeTypes = [...new Set(data.map(entry => entry.income_type))];

        // Prepare data for Plotly
        const incomes = incomeTypes.map(income_type => {
            const filteredData = data.filter(entry => entry.income_type === income_type);
            const xValues = filteredData.map(entry => entry.month);
            const yValues = filteredData.map(entry => entry.income_type_sum);

            return {
                type: 'scatter',
                mode: 'lines+markers',
                name: income_type,
                x: xValues,
                y: yValues
            };
        });

        // Layout configuration for the plot
        const layout = {
            title: 'Monthly Income Comparison',
            xaxis: {
                title: 'Month'
            },
            yaxis: {
                title: 'Total Income'
            }
        };

        // Create the plot
        Plotly.newPlot('income_breakdown', incomes, layout);
                        
    });
}

function expense_breakdown() {
    fetch('/get_expense_breakdown', {
        method: 'GET'        
    })
    .then(response => response.json())    
    .then(data => {        
        // Extract unique income types
        const expenseTypes = [...new Set(data.map(entry => entry.expense_type))];

        // Prepare data for Plotly
        const expenses = expenseTypes.map(expense_type => {
            const filteredData = data.filter(entry => entry.expense_type === expense_type);
            const xValues = filteredData.map(entry => entry.month);
            const yValues = filteredData.map(entry => entry.expense_type_sum);

            return {
                type: 'scatter',
                mode: 'lines+markers',
                name: expense_type,
                x: xValues,
                y: yValues
            };
        });

        // Layout configuration for the plot
        const layout = {
            title: 'Monthly Expense Comparison',
            xaxis: {
                title: 'Month'
            },
            yaxis: {
                title: 'Total Expense'
            }
        };

        // Create the plot
        Plotly.newPlot('expense_breakdown', expenses, layout);
                        
    });
}

function budget_progress() {
    fetch('/get_budget_recent_expenses', {
        method: 'GET'        
    })
    .then(response => response.json())    
    .then(data => {
        const budgetsArray = Object.entries(data.budget).map(([expenseType, amount]) => ({ expense_type: expenseType, total_amount: amount }));
        
        
        const progressBarsContainer = document.getElementById('progressBars');

        data.monthly_expenses.forEach((expense) => {
            const budget = budgetsArray.find(b => b.expense_type === expense.expense_type);
            
            if (budget) {
                const actualprogress = 20;
                const progress = Math.min(((expense.total_amount / budget.total_amount) * 100), 100);
                const progressBar = document.createElement('div');
                
                progressBar.className = 'progressBars';

                const progressBarTitle = document.createElement('div');
                progressBarTitle.textContent = expense.expense_type; // Display the title
                progressBar.appendChild(progressBarTitle);

                const progressBarInner = document.createElement('div');
                progressBarInner.className = 'progress-bar-inner';
                progressBarInner.style.width = `${progress}%`;
                progressBarInner.textContent = `${progress.toFixed(2)}%`;

                if (progress >= 90) {
                    progressBarInner.style.backgroundColor = '#ff3333'; // Red
                  } else if (progress >= 60) {
                    progressBarInner.style.backgroundColor = '#ffa500'; // Orange
                  } else {
                    progressBarInner.style.backgroundColor = '#4caf50'; // Green
                  }

                progressBar.appendChild(progressBarInner);
                progressBarsContainer.appendChild(progressBar);
            }       
        })
    });
}