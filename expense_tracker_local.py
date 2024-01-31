from flask import Flask,render_template,request, redirect, url_for, make_response, session, jsonify

import mysql.connector
import pymongo
import jwt
import os
import json
from flask_bcrypt import Bcrypt
from flask_cors import CORS


app = Flask(__name__)
bcrypt = Bcrypt(app)
CORS(app)

with open("C:/Users/Alistair/OneDrive/Desktop/keys.json") as config_file:
    config = json.load(config_file)

app.secret_key = config["api_keys"]["APP_SECRET_KEY"]
MONGO_DB = config["api_keys"]["MONGO_DB_NAME"]
MONGO_DB_PW = config["api_keys"]["MONGO_PW"]

###ININTAILIZE DATASE CREDENTIALS
db_config = {
    'host': config["api_keys"]["SQL_DATABASE_URL"],
    'user': config["api_keys"]["SQL_DATABASE_USERNAME"],
    'password': config["api_keys"]["SQL_DATABASE_PW"],
    'database': config["api_keys"]["SQL_DATABASE_NAME"],
}

COOKIE_NAME = 'expense_tracker_cookie_container'

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client[config["api_keys"]["LOCAL_DB_NAME"]]
col = db[config["api_keys"]["LOCAL_COL_NAME"]]

def encode(user_id):    
    payload = {
        'sub': user_id
    }
    return jwt.encode(payload, app.secret_key ,algorithm='HS256')

def decode(payload):
    decoded_payload = jwt.decode(payload, app.secret_key , algorithms=['HS256'])    
    return decoded_payload['sub']

###DEFINE INITIAL TEMPLATE ROUTES
@app.route('/')
def home():
    return render_template('landing.html')

@app.route('/success', methods = ['GET'])
def success():
    return render_template('success.html')

@app.route('/login', methods=['GET','POST'])
def login():
    return render_template('login.html')

###USER LOGIN FUNCTIONALITY
@app.route('/user_login', methods=['POST','GET'])
def user_login():
        #Recieves the username and password from user
        username = request.json.get('username')
        password = request.json.get('password')

        #Connects to SQL database for user information and retreives the password
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(f"SELECT pass FROM user_info WHERE userID = '{username}' LIMIT 1")
        pw = cursor.fetchone()
        conn.close

        #If the given credentials are correct, user is redirected to their dashoard
        if bcrypt.check_password_hash(pw[0], password):
            cursor.execute(f"SELECT id FROM user_info WHERE userID = '{username}' LIMIT 1")
            master_user_id = cursor.fetchone()
            master_user_id = master_user_id[0]
            encoded_id = encode(master_user_id)
            return jsonify({'message': 'Login successful','encoded_id':encoded_id}), 200
        #If the credentials are incorrect the page refrehes with an error message
        else:
            return jsonify({'message': 'Invalid username or password'}), 200


@app.route('/signup', methods=['GET','POST'])
def signup():
    return render_template('signup.html')

###Primary Sign-Up option is the traditional username-password method
@app.route('/signup_user', methods=['POST'])
def signup_user():    
    #Request the user input from the input fields  
    username = request.json.get('username')
    password = request.json.get('password')

    #Connects to the database to check if a username already exists
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(id) FROM user_info where userID = '{username}'")
    taken = cursor.fetchone()
        
    #If the username already exists the user is prompted to choose a different one
    if taken[0] > 0:
        return jsonify({'message' : 'exists'})
                     
    #Password encrpytion
    password = bcrypt.generate_password_hash(password).decode('utf-8')
    query = f"INSERT INTO user_info VALUES (DEFAULT, '{username}', '{password}');"
    #If all requirements are met then an entry is creaated in the SQL databse with the user's credentials
    cursor.execute(query)
    conn.commit()

    cursor.execute(f"SELECT id FROM user_info WHERE userID = '{username}'")
    nosqlID = cursor.fetchone()
    nosqlID = nosqlID[0]
    col.insert_one({"_id": nosqlID,"income_types":[],"expense_types":[],"budget":{}})
        
    #User is redirected to the login page to sign in
    return jsonify({'message' : 'success'})

####DASHBOARD
#########################################################################
@app.route('/dashboard', methods = ['GET'])
def dashboard():
    
    return render_template('dashboard.html')

@app.route('/get_income_v_expense', methods = ['POST'])
def get_income_v_expense():
    encoded_id = request.json.get('encoded_id')
    master_user_id = decode(encoded_id)
    income = []
    expenses = []

    query = f"SELECT SUM(amount) AS total_income, DATE_FORMAT(STR_TO_DATE(day_month_year, '%Y-%m-%d'), '%Y-%m') AS month FROM user_income WHERE user_id = {master_user_id} GROUP BY month ORDER BY month desc LIMIT 12;"
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(query)
    data = cursor.fetchall()    
    for row in data:
        income.append(dict(zip([column[0] for column in cursor.description], row)))

    query = f"SELECT SUM(amount) AS total_expenses, DATE_FORMAT(STR_TO_DATE(day_month_year, '%Y-%m-%d'), '%Y-%m') AS month FROM user_expenses WHERE user_id = {master_user_id} GROUP BY month ORDER BY month desc LIMIT 12;"

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(query)
    data = cursor.fetchall()    
    for row in data:
        expenses.append(dict(zip([column[0] for column in cursor.description], row)))        
    conn.close
    
    if len(income) == 0 and len(expenses) == 0:
        response = {'status' : 'no_data'}
        return jsonify(response)

    income_expense = {"income": income, "expenses": expenses}
    return jsonify(income_expense)

@app.route('/get_income_breakdown', methods = ['POST'])
def get_income_breakdown():
    encoded_id = request.json.get('encoded_id')
    master_user_id = decode(encoded_id)
    incomes = []

    query = f"SELECT DATE_FORMAT(STR_TO_DATE(day_month_year, '%Y-%m-%d'), '%Y-%m') AS month, income_type, SUM(amount) AS income_type_sum FROM user_income WHERE user_id = {master_user_id} GROUP BY month, income_type ORDER BY month, income_type LIMIT 12;"
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(query)
    data = cursor.fetchall()    
    for row in data:
        incomes.append(dict(zip([column[0] for column in cursor.description], row)))
        
    conn.close
    if len(incomes) == 0:
        response = {'status' : 'no_data'}
        return jsonify(response)
    return jsonify(incomes)

@app.route('/get_expense_breakdown', methods = ['POST'])
def get_expense_breakdown():
    encoded_id = request.json.get('encoded_id')
    master_user_id = decode(encoded_id)
    expenses = []

    query = f"SELECT DATE_FORMAT(STR_TO_DATE(day_month_year, '%Y-%m-%d'), '%Y-%m') AS month, expense_type, SUM(amount) AS expense_type_sum FROM user_expenses WHERE user_id = {master_user_id} GROUP BY month, expense_type ORDER BY month, expense_type LIMIT 12;"
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(query)
    data = cursor.fetchall()    
    for row in data:
        expenses.append(dict(zip([column[0] for column in cursor.description], row)))
    conn.close

    if len(expenses) == 0:
        response = {'status' : 'no_data'}
        return jsonify(response)
    return jsonify(expenses)

@app.route('/get_budget_recent_expenses', methods = ['POST'])
def get_budget_recent_expenses():
    encoded_id = request.json.get('encoded_id')
    master_user_id = decode(encoded_id)
    monthly_expenses = []

    budget_targets = col.find_one({"_id": master_user_id})
    budget_targets = budget_targets['budget']
    print(budget_targets)

    query = f"SELECT expense_type, SUM(amount) AS total_amount FROM user_expenses WHERE user_id = {master_user_id} AND YEAR(day_month_year) = YEAR(CURDATE()) AND MONTH(day_month_year) = MONTH(CURDATE()) GROUP BY expense_type;"
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(query)
    data = cursor.fetchall() 
    print(data)   
    for row in data:
        monthly_expenses.append(dict(zip([column[0] for column in cursor.description], row)))
    conn.close

    if len(budget_targets) == 0 or len(monthly_expenses) == 0:
        response = {'status' : 'no_data'}
        return jsonify(response)
    return jsonify({'budget' : budget_targets, 'monthly_expenses' : monthly_expenses})


####INCOME
#########################################################################
### REDIRECT USER TO INCOME HUB 
@app.route('/income', methods = ['GET'])
def income():
    return render_template('add_income.html')

### ADDS USER INCOME TO SQL DATABASE USING INFORMATION PORVIDED BY JAVASCRIPT REQUEST
@app.route('/add_income', methods = ['POST'])
def add_income():
    #PARSE DATA FROM JAVASCRIPT REQUEST
    incomeType = request.json.get('incomeType')
    amount = request.json.get('amount')
    date = request.json.get('date')
    encoded_id = request.json.get('encoded_id')
    user = decode(encoded_id)

    #DATA INSERTION INTO SQL DATABSE
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(f"INSERT INTO user_income VALUES (DEFAULT, '{user}', '{date}','{incomeType}','{amount}');")
    conn.commit()
    conn.close
    return jsonify({'message' : 'success'})

###FUNCTIONALITY TO GET THE VARIOUS INCOME TYPES THAT A USER HAS STORED IN 
# THEIR NOSQL DOCUMENT AND RETURNS THE RESULTS TO THE JAVASCRIPT FONT-END
@app.route('/get_income_types', methods = ['POST'])
def get_income_types():
    encoded_id = request.json.get('encoded_id')
    master_user_id = decode(encoded_id)
    incomeTypes = col.find_one({"_id": master_user_id})
    incomeTypes = incomeTypes['income_types']
    print(incomeTypes)
    return jsonify({'types':incomeTypes})

###FUNCTIONALITY TO ADD A NEW INCOMETYPE TO THE USER'S NOSQL DOCUMENT
@app.route('/add_income_type', methods = ['POST'])
def add_income_type():
    newIncomeType = request.json.get('newIncomeType')
    encoded_id = request.json.get('encoded_id')
    master_user_id = decode(encoded_id)

    #Gets all the INCOME TYPES in the current user's NoSQL document
    incomeTypes = col.find_one({"_id": master_user_id})
    incomeTypes = incomeTypes['income_types'] 

    #If the income type trying to be added already exists, return an "exists" message to the JavaScript front-end
    if(newIncomeType in incomeTypes):
        return jsonify({'message' : 'exists'})

    #If the income type doesn't exist in the document, it is pushed onto user's NoSQL document
    col.update_one({"_id" : master_user_id}, { "$push" : {"income_types" : newIncomeType}})
    return jsonify({'message' : 'success'})

### FUNCTIONALITY TO REMOVE AN INCOME TYPE FROM THE USER'S NOSQL DOCUMENT
@app.route('/remove_income_type', methods=['POST'])
def remove_income_type():
    # Get the income type to be removed from the JavaScript request
    incomeTypeTBR = request.json.get('incomeTypeTBR')
    encoded_id = request.json.get('encoded_id')
    master_user_id = decode(encoded_id)

    # Removes the selected income type from the user's NoSQL document
    col.update_one({"_id" : master_user_id}, { "$pull" : {"income_types" : incomeTypeTBR}})

    # Resturns a "success" response message to the JavaScript front-end
    return jsonify({'status': 'success'})

### FUNCTIONALITY TO GET THE RECENT INCOME ENTRIES THE USER HAS ADDED TO THE SQL DATABSE
@app.route('/get_recent_income', methods = ['POST'])
def get_recent_income():
    encoded_id = request.json.get('encoded_id')
    master_user_id = decode(encoded_id)
    recent_income_entries = []

    # Queries the database to fetch all income entries for the current user
    query = f"SELECT income_id, user_id, income_type, amount FROM user_income WHERE user_id = {master_user_id};"
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    
    for row in data:
        recent_income_entries.append(dict(zip([column[0] for column in cursor.description], row)))

    # Returns the results of the query to the Javascript front-end
    return jsonify({'entries' : recent_income_entries})

###FUNCTIONALITY TO REMOVE A SPECIFIC ENTRY FROM THE SQL DATABSE OF INCOME ENTRIES
@app.route('/delete_income_entry',methods = ['POST'])
def delete_income_entry():
    # Retreives the unique id of the income entry that is to be deleted
    incomeEntryTBR = request.json.get('incomeEntryTBR')
    encoded_id = request.json.get('encoded_id')
    master_user_id = decode(encoded_id)
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    # Creates and commits a query to delete the entry from the database
    cursor.execute(f"DELETE FROM user_income WHERE income_id = {incomeEntryTBR} AND user_id = {master_user_id};")
    conn.commit()
    conn.close

    # Return "succes message to the Javascript front-end"
    return jsonify({'status': 'success'})


##EXPENSES
#################################################################

### REDIRECT USER TO EXPENSES HUB
@app.route('/expenses', methods = ['GET'])
def expenses():
    return render_template('add_expense.html')

### FUNCTIONALITY TO ADD A NEW EXPENSE TO THE SQL DATABASE
@app.route('/add_expense', methods = ['POST'])
def add_expense():
    # Parse data from Javascript request
    expenseType = request.json.get('expenseType')
    amount = request.json.get('amount')
    date = request.json.get('date')
    encoded_id = request.json.get('encoded_id')
    user = decode(encoded_id)

    # Create and execute a query that will insert the data into the SQL databse
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(f"INSERT INTO user_expenses VALUES (DEFAULT, '{user}', '{date}','{expenseType}','{amount}');")
    conn.commit()
    conn.close
    return jsonify({'message' : 'success'})

###FUNCTIONALITY TO GET ALL THE USER'S EXPENSE TYPES FOR THIER NOSQL DOCUMENT
@app.route('/get_expense_types', methods = ['POST'])
def get_expense_types():
    encoded_id = request.json.get('encoded_id')
    print('enc')
    print(encoded_id)
    master_user_id = decode(encoded_id)
    expenseTypes = col.find_one({"_id": master_user_id})
    expenseTypes = expenseTypes['expense_types']
    print(expenseTypes)
    return jsonify({'types':expenseTypes})

### FUNCTINALITY TO ADD AN EXPENSE TYPE THE USER'S NOSQL DOCUMENT
@app.route('/add_expense_type', methods = ['POST'])
def add_expense_type():
    newExpenseType = request.json.get('newExpenseType')
    encoded_id = request.json.get('encoded_id')
    master_user_id = decode(encoded_id)

    #Gets all expense types in the current user's NoSQL document
    expenseTypes = col.find_one({"_id": master_user_id})
    expenseTypes = expenseTypes['expense_types'] 

    #If expense type exists, return "exists" message to JavaScript front-end
    if(newExpenseType in expenseTypes):
        return jsonify({'message' : 'exists'})

    #If the expense types doesn't exist in the document, it is pushed onto the user's NoSQL document
    col.update_one({"_id" : master_user_id}, { "$push" : {"expense_types" : newExpenseType}})
    return jsonify({'message' : 'success'})

### FUNCTIONALITY TO REMOVE AN EXPENSE TYPE FROM THE USER'S NOSQL DOCUMENT
@app.route('/remove_expense_type', methods=['POST'])
def remove_expense_type():
    # Get the expense type to be removed from the JavaScript request    
    expenseTypeTBR = request.json.get('expenseTypeTBR')
    encoded_id = request.json.get('encoded_id')

    master_user_id = decode(encoded_id)

    # Remove the selected expense type from the user's NOSQL document
    col.update_one({"_id" : master_user_id}, { "$pull" : {"expense_types" : expenseTypeTBR}})

    # Return a "success" response to the JavaScript front-end
    return jsonify({'status': 'success'})

### FUNCTIONALITY TO GET ALL THE EXPENSE ENTRIES THE USER INPUTTED INTO THE SQL DATABASAE
@app.route('/get_recent_expenses', methods = ['POST'])
def get_recent_expenses():
    # Gets user's id from session
    encoded_id = request.json.get('encoded_id')
    master_user_id = decode(encoded_id)
    recent_expense_entries = []

    # Creates and executes query to return all expense entries inputted by the user
    query = f"SELECT expense_id, user_id, expense_type, amount FROM user_expenses WHERE user_id = {master_user_id};"
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    
    for row in data:
        recent_expense_entries.append(dict(zip([column[0] for column in cursor.description], row)))
    conn.close
    
    # Returns te expense entries to the JavaScript from-end
    return jsonify({'entries' : recent_expense_entries})

### FUNCTIONALITY TO DELETE A SPECIFIC EXPENSE ENTRY FROM THE SQL DATASE
@app.route('/delete_expense_entry',methods = ['POST'])
def delete_expense_entry():
    expenseEntryTBR = request.json.get('expenseEntryTBR')
    encoded_id = request.json.get('encoded_id')
    master_user_id = decode(encoded_id)
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # Creates and executes a query to delete the expense entry selected by the user
    cursor.execute(f"DELETE FROM user_income WHERE income_id = {expenseEntryTBR} AND user_id = {master_user_id};")
    conn.commit()
    conn.close

    # Return "success" message to front-end
    return jsonify({'status': 'success'})

##BUDGET
#################################################################
### REDIRECT USER TO EXPENSES HUB
@app.route('/budget', methods = ['GET'])
def budget():
    return render_template('budget.html')

@app.route('/get_budget_targets', methods = ['POST'])
def get_budget_targets():
    encoded_id = request.json.get('encoded_id')
    master_user_id = decode(encoded_id)
    budget_targets = col.find_one({"_id": master_user_id})
    budget_targets = budget_targets['budget']
    return jsonify({'types':budget_targets})

@app.route('/save_budget', methods = ['POST'])
def save_budget():    
    expenseType = request.json.get('expenseType')
    newBudgetAmount = request.json.get('newBudgetAmount')
    encoded_id = request.json.get('encoded_id')
    master_user_id = decode(encoded_id)
    newBudgetAmount = int(newBudgetAmount)   
    nested = "budget."+expenseType

    result = col.update_one({'_id': master_user_id},{'$set': {nested: newBudgetAmount}}, upsert=True)

    if result.upserted_id:
        return jsonify({'status':'success'})
    else:
        return jsonify({'status':'fail'})

####LOGOUT FUNCTOINALITY
@app.route('/logout', methods=['POST'])
def logout():
    #Remove the current user's unique identifyer from the session object
    session.pop("user",None)

    #Redirects user back to the home landing page after logging out
    return jsonify({'status':'loggedOUT'})

if __name__ == '__main__':
    app.run(debug=True)