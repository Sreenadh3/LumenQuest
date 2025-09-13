import pyodbc

server = 'lumenhackathonsample.database.windows.net'
database = 'lumenhackathon45'  # Replace with your actual database name
username = 'lumen'               # Your SQL Server admin login
password = 'Password@123'       # Your password
driver = '{ODBC Driver 17 for SQL Server}'  # Ensure this driver is installed

connection_string = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'

def get_connection():
    return pyodbc.connect(connection_string)