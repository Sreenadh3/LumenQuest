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
        cursor.execute("SELECT t.TABLE_SCHEMA, t.TABLE_NAME, c.COLUMN_NAME, c.DATA_TYPE, c.CHARACTER_MAXIMUM_LENGTH, c.NUMERIC_PRECISION, c.NUMERIC_SCALE, c.IS_NULLABLE, c.COLUMN_DEFAULT FROM INFORMATION_SCHEMA.TABLES t JOIN INFORMATION_SCHEMA.COLUMNS c ON t.TABLE_NAME = c.TABLE_NAME AND t.TABLE_SCHEMA = c.TABLE_SCHEMA WHERE t.TABLE_TYPE = 'BASE TABLE' ORDER BY t.TABLE_SCHEMA, t.TABLE_NAME, c.ORDINAL_POSITION;")
        cursor.execute("SELECT * FROM Users;")

        rows = cursor.fetchall()

        for row in rows:
            print(row)


except Exception as e:
    print("Error connecting to the database:", e)

def get_connection():
    return pyodbc.connect(connection_string)