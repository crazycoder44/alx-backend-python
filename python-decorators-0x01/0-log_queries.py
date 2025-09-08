import sqlite3
import functools
from datetime import datetime

#### decorator to log SQL queries
def log_queries(func):
    """
    Decorator that logs SQL queries before executing the function.
   
    Args:
        func: The function to be decorated
       
    Returns:
        The wrapper function that logs queries and executes the original function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Extract the query from function arguments
        # Check if 'query' is in kwargs first, then check positional args
        query = None
        if 'query' in kwargs:
            query = kwargs['query']
        elif args:
            # Assuming the first argument is the query if not in kwargs
            for arg in args:
                if isinstance(arg, str) and arg.strip().upper().startswith(('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER')):
                    query = arg
                    break
       
        # Log the query if found
        if query:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] Executing SQL Query: {query}")
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] Executing database function (query not found in arguments)")
       
        # Execute the original function
        return func(*args, **kwargs)
   
    return wrapper

@log_queries
def fetch_all_users(query):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results

#### fetch users while logging the query
users = fetch_all_users(query="SELECT * FROM users")