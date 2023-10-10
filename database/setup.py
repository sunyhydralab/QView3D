import os
from decouple import config, Csv
from mysql.connector import connect, Error
            
def create_database():
        try:          
            # Create the HVAMC database  
            DB_HOST = config('DB_HOST')
            DB_USER = config('DB_USER')
            DB_PASSWORD = config('DB_PASSWORD')
            DB_NAME = config('DB_NAME')
            with connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD
            )as connection:
                cursor = connection.cursor()
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME};")
                cursor.execute(f"USE {DB_NAME};")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS registered_bots (
                        bot_id INT AUTO_INCREMENT PRIMARY KEY, 
                        model VARCHAR(30) NOT NULL, 
                        date_registered DATETIME DEFAULT CURRENT_TIMESTAMP, 
                        build_volume VARCHAR(20), 
                        jobs_passed INT, 
                        jobs_failed INT, 
                        success_rate DECIMAL(5, 2) GENERATED ALWAYS AS ((jobs_passed / (jobs_passed + jobs_failed)) * 100) STORED, 
                        notes TEXT
                    )
                """)

                cursor.execute("""
                        CREATE TABLE IF NOT EXISTS jobs (
                            job_id INT AUTO_INCREMENT PRIMARY KEY, 
                            file_name VARCHAR(30), 
                            label VARCHAR(30), 
                            quantity INT, 
                            color VARCHAR(15), 
                            priority TINYINT(1),
                            date_added DATETIME DEFAULT CURRENT_TIMESTAMP
                        )
                        """)
                
            print("Database and table created successfully!")

        except Error as e:
            print(f"Error: {e}")

def createEnv(): 
    try: 
    # Prompt the user to enter database credentials
        DB_HOST = input("Enter database host (Ex. localhost): ")
        DB_USER = input("Enter database username (Ex. root): ")
        DB_PASSWORD = input("Enter database password: ")
        DB_NAME = input("Enter database name (Ex. hvamc): ")
        
        with open("../.env", "w") as env_file:
            env_file.write(f"DB_HOST={DB_HOST}\n")
            env_file.write(f"DB_USER={DB_USER}\n")
            env_file.write(f"DB_PASSWORD={DB_PASSWORD}\n")
            env_file.write(f"DB_NAME={DB_NAME}\n")

    except Exception as e: 
        print(f"Error: {e}")

if __name__ == "__main__":
    
    # Create .env file 
    if not os.path.isfile("../.env"):
        createEnv()
    else:
    # If .env file already exists, delete and recreate it
        os.remove("../.env")
        createEnv()  
        
    create_database() # now create, use, and generate database tables
        

