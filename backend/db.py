import pyodbc

server = 'lumenhackathonsample.database.windows.net'
database = 'lumenhackathon45'  # Replace with your actual database name
username = 'lumen'               # Your SQL Server admin login
password = 'Password@123'       # Your password
driver = '{ODBC Driver 17 for SQL Server}'  # Ensure this driver is installed

connection_string = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'

try:
    # Connect to the SQL Server
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()

        # Example query
        cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
        tables = cursor.fetchall()

        print("Tables in the database:")
        for table in tables:
            print(f"- {table[0]}")
        cursor.execute("INSERT INTO Users(UserID) VALUES(3);")
        cursor.execute("SELECT * FROM Users;")
        rows = cursor.fetchall()

        for row in rows:
            print(row)


except Exception as e:
    print("Error connecting to the database:", e)

def get_connection():
    return pyodbc.connect(connection_string)