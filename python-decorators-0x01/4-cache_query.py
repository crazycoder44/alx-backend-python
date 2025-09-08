import time
import sqlite3 
import functools


query_cache = {}

def with_db_connection(func):
    """
    Decorator that automatically handles opening and closing database connections.
    
    Opens a database connection, passes it to the function as the first argument,
    and ensures the connection is properly closed afterward.
    
    Args:
        func: The function to be decorated
        
    Returns:
        The wrapper function that manages database connections
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Open database connection
        conn = sqlite3.connect('users.db')
        
        try:
            # Call the original function with connection as first argument
            result = func(conn, *args, **kwargs)
            return result
        finally:
            # Always close the connection, even if an exception occurs
            conn.close()
    
    return wrapper

def cache_query(func):
    """
    Decorator that caches query results based on the SQL query string.
    
    Caches the results of database queries to avoid redundant calls.
    The cache key is based on the SQL query string passed to the function.
    
    Args:
        func: The function to be decorated (should accept query parameter)
        
    Returns:
        The wrapper function that handles caching
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Extract the query from function arguments
        query = None
        
        # Check if 'query' is in kwargs
        if 'query' in kwargs:
            query = kwargs['query']
        else:
            # Look for query in positional arguments (skip conn which is first)
            for arg in args[1:]:  # Skip the first argument (conn)
                if isinstance(arg, str) and arg.strip().upper().startswith(('SELECT', 'WITH')):
                    query = arg
                    break
        
        # Use the query as cache key if found
        if query:
            cache_key = query.strip()
            
            # Check if result is already cached
            if cache_key in query_cache:
                print(f"Cache hit! Using cached result for query: {query}")
                return query_cache[cache_key]
            
            # Execute the function and cache the result
            print(f"Cache miss! Executing and caching query: {query}")
            result = func(*args, **kwargs)
            query_cache[cache_key] = result
            return result
        else:
            # If no query found, execute without caching
            print("No SQL query found in arguments, executing without caching")
            return func(*args, **kwargs)
    
    return wrapper

@with_db_connection
@cache_query
def fetch_users_with_cache(conn, query):
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetchall()

#### First call will cache the result
users = fetch_users_with_cache(query="SELECT * FROM users")

#### Second call will use the cached result
users_again = fetch_users_with_cache(query="SELECT * FROM users")