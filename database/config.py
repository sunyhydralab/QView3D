from decouple import config
from getpass import getpass
from mysql.connector import connect, Error

DB_HOST = config('DB_HOST')
DB_USER = config('DB_USER')
DB_PASSWORD = config('DB_PASSWORD')
DB_DATABASE = config('DB_DATABASE')

try:
    with connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_DATABASE,
    ) as connection:
        print(connection)
except Error as e:
    print(e)