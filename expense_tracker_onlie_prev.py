from flask import Flask, request, session, render_template, redirect, url_for, jsonify
import mysql.connector
import pymongo
import os
import jwt
import json
from flask_bcrypt import Bcrypt
from flask_cors import CORS


app = Flask(__name__)
bcrypt = Bcrypt(app)
CORS(app)

app.secret_key = os.environ.get('APP_SECRET_KEY')
MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME')
MONGO_DB_PW = os.environ.get('MONGO_PW')
MONGO_DB_DB = os.environ.get('MONGO_DB')
MONGO_DB_COL = os.environ.get('MONGO_COL')

db_config = {
    'host': os.environ.get('AWS_RDS_URI'),
    'user': os.environ.get('RDS_USERNAME'),
    'password': os.environ.get('RDS_PASSWORD'),
    'database': os.environ.get('RDS_DB_NAME'),
}

uri = f"mongodb+srv://{MONGO_DB_NAME}:{MONGO_DB_PW}@cluster0.wvhyisx.mongodb.net/?retryWrites=true&w=majority"
client = pymongo.MongoClient(uri)
db = client[MONGO_DB_DB]
col = db[MONGO_DB_COL]

def encode(user_id):
    payload = {
        'sub': user_id
    }
    return jwt.encode(payload, "123456" ,algorithm='HS256')

def decode(payload):
    decoded_payload = jwt.decode(payload, "123456" , algorithms=['HS256'])
    return decoded_payload

###DEFINE INITIAL TEMPLATE ROUTES
@app.route('/')
def home():
    return redirect("https://expense-tracker-landing.netlify.app/")


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
            dbID = cursor.fetchone()
            dbID = dbID[0]
            session["user"] = dbID
            encoded_id = encode(dbID)
            return jsonify({'message': 'Login successful','encoded_id':encoded_id}), 200
        #If the credentials are incorrect the page refrehes with an error message
        else:
            response = jsonify({'message': 'Invalid username or password'})
            return response



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
    if "user" not in session:
         return redirect(url_for('home'))
    return render_template('dashboard.html')

@app.route('/get_income_v_expense', methods = ['POST'])
def get_income_v_expense():
    dbID = session["user"]
    income = []
    expenses = []

    query = f"SELECT SUM(amount) AS total_income, DATE_FORMAT(STR_TO_DATE(day_month_year, '%Y-%m-%d'), '%Y-%m') AS month FROM user_income WHERE user_id = {dbID} GROUP BY month ORDER BY month desc LIMIT 12;"
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(query)
    data = cursor.fetchall()    
    for row in data:
        income.append(dict(zip([column[0] for column in cursor.description], row)))

    query = f"SELECT SUM(amount) AS total_expenses, DATE_FORMAT(STR_TO_DATE(day_month_year, '%Y-%m-%d'), '%Y-%m') AS month FROM user_expenses WHERE user_id = {dbID} GROUP BY month ORDER BY month desc LIMIT 12;"

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(query)
    data = cursor.fetchall()    
    for row in data:
        expenses.append(dict(zip([column[0] for column in cursor.description], row)))
    conn.close

    income_expense = {"income": income, "expenses": expenses}
    return jsonify(income_expense)

@app.route('/get_income_breakdown', methods = ['POST'])
def get_income_breakdown():
    dbID = session["user"]
    incomes = []

    query = f"SELECT DATE_FORMAT(STR_TO_DATE(day_month_year, '%Y-%m-%d'), '%Y-%m') AS month, income_type, SUM(amount) AS income_type_sum FROM user_income WHERE user_id = {dbID} GROUP BY month, income_type ORDER BY month, income_type LIMIT 12;"
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(query)
    data = cursor.fetchall()    
    for row in data:
        incomes.append(dict(zip([column[0] for column in cursor.description], row)))
    conn.close
    return jsonify(incomes)

@app.route('/get_expense_breakdown', methods = ['POST'])
def get_expense_breakdown():
    dbID = session["user"]
    expenses = []

    query = f"SELECT DATE_FORMAT(STR_TO_DATE(day_month_year, '%Y-%m-%d'), '%Y-%m') AS month, expense_type, SUM(amount) AS expense_type_sum FROM user_expenses WHERE user_id = {dbID} GROUP BY month, expense_type ORDER BY month, expense_type LIMIT 12;"
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(query)
    data = cursor.fetchall()    
    for row in data:
        expenses.append(dict(zip([column[0] for column in cursor.description], row)))

    conn.close
    return jsonify(expenses)

@app.route('/get_budget_recent_expenses', methods = ['POST'])
def get_budget_recent_expenses():
    dbID = session["user"]
    monthly_expenses = []

    budget_targets = col.find_one({"_id": dbID})
    budget_targets = budget_targets['budget']

    query = f"SELECT expense_type, SUM(amount) AS total_amount FROM user_expenses WHERE user_id = {dbID} AND YEAR(day_month_year) = YEAR(CURDATE()) AND MONTH(day_month_year) = MONTH(CURDATE()) GROUP BY expense_type;"
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(query)
    data = cursor.fetchall()    
    for row in data:
        monthly_expenses.append(dict(zip([column[0] for column in cursor.description], row)))

    conn.close
    return jsonify({'budget' : budget_targets, 'monthly_expenses' : monthly_expenses})


####INCOME
#########################################################################
### REDIRECT USER TO INCOME HUB 
@app.route('/income', methods = ['GET'])
def income():
    if "user" not in session:
         return redirect(url_for('home'))
    return render_template('add_income.html')

### ADDS USER INCOME TO SQL DATABASE USING INFORMATION PORVIDED BY JAVASCRIPT REQUEST
@app.route('/add_income', methods = ['POST'])
def add_income():
    #PARSE DATA FROM JAVASCRIPT REQUEST
    incomeType = request.json.get('incomeType')
    amount = request.json.get('amount')
    date = request.json.get('date')
    user = session['user']

    #DATA INSERTION INTO SQL DATABSE
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(f"INSERT INTO user_income VALUES (DEFAULT, '{user}', '{date}','{incomeType}','{amount}');")
    conn.commit()
    conn.close
    return jsonify({'message' : 'success'})

###FUNCTIONALITY TO GET THE VAROIUS INCOME TYPES THAT A USER HAS STORED IN 
# THEIR NOSQL DOCUMENT AND RETURNS THE RESULTS TO THE JAVASCRIPT FONT-END
@app.route('/get_income_types', methods = ['GET'])
def get_income_types():
    dbID = session["user"]
    incomeTypes = col.find_one({"_id": dbID})
    incomeTypes = incomeTypes['income_types']
    return jsonify({'types':incomeTypes})

###FUNCTIONALITY TO ADD A NEW INCOMETYPE TO THE USER'S NOSQL DOCUMENT
@app.route('/add_income_type', methods = ['POST'])
def add_income_type():
    newIncomeType = request.json.get('newIncomeType')
    dbID = session["user"]

    #Gets all the INCOME TYPES in the current user's NoSQL document
    incomeTypes = col.find_one({"_id": dbID})
    incomeTypes = incomeTypes['income_types'] 

    #If the income type trying to be added already exists, return an "exists" message to the JavaScript front-end
    if(newIncomeType in incomeTypes):
        return jsonify({'message' : 'exists'})

    #If the income type doesn't exist in the document, it is pushed onto user's NoSQL document
    col.update_one({"_id" : dbID}, { "$push" : {"income_types" : newIncomeType}})
    return jsonify({'message' : 'success'})

### FUNCTIONALITY TO REMOVE AN INCOME TYPE FROM THE USER'S NOSQL DOCUMENT
@app.route('/remove_income_type', methods=['POST'])
def remove_income_type():
    # Get the income type to be removed from the JavaScript request
    incomeTypeTBR = request.form.get('incomeTypeTBR')

    dbID = session["user"]
    # Removes the selected income type from the user's NoSQL document
    col.update_one({"_id" : dbID}, { "$pull" : {"income_types" : incomeTypeTBR}})

    # Resturns a "success" response message to the JavaScript front-end
    return jsonify({'status': 'success'})

### FUNCTIONALITY TO GET THE RECENT INCOME ENTRIES THE USER HAS ADDED TO THE SQL DATABSE
@app.route('/get_recent_income', methods = ['GET'])
def get_recent_income():
    #Retrieves user's id from session
    dbID = session["user"]
    recent_income_entries = []

    # Queries the database to fetch all income entries for the current user
    query = f"SELECT income_id, user_id, income_type, amount FROM user_income WHERE user_id = {dbID};"
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
    incomeEntryTBR = request.form.get('incomeEntryTBR')
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    # Crestes and commits a quesry to delete the entry from the database
    cursor.execute(f"DELETE FROM user_income WHERE income_id = {incomeEntryTBR};")
    conn.commit()
    conn.close

    # Return "succes message to the Javascript front-end"
    return jsonify({'status': 'success'})


##EXPENSES
#################################################################

### REDIRECT USER TO EXPENSES HUB
@app.route('/expenses', methods = ['GET'])
def expenses():
    if "user" not in session:
         return redirect(url_for('home'))
    return render_template('add_expense.html')

### FUNCTIONALITY TO ADD A NEW EXPENSE TO THE SQL DATABASE
@app.route('/add_expense', methods = ['POST'])
def add_expense():
    # Parse data from Javascript request
    expenseType = request.json.get('expenseType')
    amount = request.json.get('amount')
    date = request.json.get('date')
    user = session['user']

    # Create and execute a query that will insert the data into the SQL databse
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(f"INSERT INTO user_expenses VALUES (DEFAULT, '{user}', '{date}','{expenseType}','{amount}');")
    conn.commit()
    conn.close
    return jsonify({'message' : 'success'})

###FUNCTIONALITY TO GET ALL THE USER'S EXPENSE TYPES FOR THIER NOSQL DOCUMENT
@app.route('/get_expense_types', methods = ['GET'])
def get_expense_types():
    dbID = session["user"]
    expenseTypes = col.find_one({"_id": dbID})
    expenseTypes = expenseTypes['expense_types']
    return jsonify({'types':expenseTypes})

### FUNCTINALITY TO ADD AN EXPENSE TYPE THE USER'S NOSQL DOCUMENT
@app.route('/add_expense_type', methods = ['POST'])
def add_expense_type():
    newExpenseType = request.json.get('newExpenseType')
    dbID = session["user"]

    #Gets all expense types in the current user's NoSQL document
    expenseTypes = col.find_one({"_id": dbID})
    expenseTypes = expenseTypes['expense_types'] 

    #If expense type exists, return "exists" message to JavaScript front-end
    if(newExpenseType in expenseTypes):
        return jsonify({'message' : 'exists'})

    #If the expense types doesn't exist in the document, it is pushed onto the user's NoSQL document
    col.update_one({"_id" : dbID}, { "$push" : {"expense_types" : newExpenseType}})
    return jsonify({'message' : 'success'})

### FUNCTIONALITY TO REMOVE AN EXPENSE TYPE FROM THE USER'S NOSQL DOCUMENT
@app.route('/remove_expense_type', methods=['POST'])
def remove_expense_type():
    # Get the expense type to be reomved from the JavaScript request
    
    expenseTypeTBR = request.form.get('expenseTypeTBR')

    # Get user id from session
    dbID = session["user"]
    
    # Remove the selected expense type from the user's NOSQL document
    col.update_one({"_id" : dbID}, { "$pull" : {"expense_types" : expenseTypeTBR}})

    # Return a "success" response to the JavaScript front-end
    return jsonify({'status': 'success'})

### FUNCTIONALITY TO GET ALL THE EXPENSE ENTRIES THE USER INPUTTED INTO THE SQL DATABASAE
@app.route('/get_recent_expenses', methods = ['GET'])
def get_recent_expenses():
    # Gets user's id from session
    dbID = session["user"]
    recent_expense_entries = []

    # Creates and executes query to return all expense entries inputted by the user
    query = f"SELECT expense_id, user_id, expense_type, amount FROM user_expenses WHERE user_id = {dbID};"
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
    expenseEntryTBR = request.form.get('expenseEntryTBR')
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # Creates and executes a query to delete the expense entry selected by the user
    cursor.execute(f"DELETE FROM user_expenses WHERE expense_id = {expenseEntryTBR};")
    conn.commit()
    conn.close

    # Return "success" message to front-end
    return jsonify({'status': 'success'})

##BUDGET
#################################################################
### REDIRECT USER TO EXPENSES HUB
@app.route('/budget', methods = ['GET'])
def budget():
    if "user" not in session:
         return redirect(url_for('home'))
    return render_template('budget.html')

@app.route('/get_budget_targets', methods = ['GET'])
def get_budget_targets():
    dbID = session["user"]
    budget_targets = col.find_one({"_id": dbID})
    budget_targets = budget_targets['budget']
    return jsonify({'types':budget_targets})

@app.route('/save_budget', methods = ['POST'])
def save_budget():
    dbID = session["user"]
    expenseType = request.json.get('expenseType')
    newBudgetAmount = request.json.get('newBudgetAmount')
    newBudgetAmount = int(newBudgetAmount)   
    nested = "budget."+expenseType

    result = col.update_one({'_id': dbID},{'$set': {nested: newBudgetAmount}}, upsert=True)

    if result.upserted_id:
        return jsonify({'status':'success'})
    else:
        return jsonify({'status':'success'})

####LOGOUT FUNCTOINALITY
@app.route('/logout', methods=['POST'])
def logout():
    #Remove the current user's unique identifyer from the session object
    session.pop("user",None)

    #Redirects user back to the home landing page after logging out
    return jsonify({'status':'loggedOUT'})

if __name__ == '__main__':
    app.run(debug=True)