# from connectdb import engine
# from sqlalchemy.sql import text

# # Query the database
# def query_supported_printers():
#     with engine.connect() as conn:
#         sql = "SELECT * FROM supported_printers"
#         result = conn.execute(text(sql))
        
#         # Fetch all rows from the result set
#         rows = result.fetchall()

#         results = []
#         for row in rows:
#             results.append({
#                 'id': row[0],              # Assuming the first column is the ID
#                 'printer_name': row[1],    # Access by column index or name
#                 # Add more columns as needed
#             })

#         print(results)
