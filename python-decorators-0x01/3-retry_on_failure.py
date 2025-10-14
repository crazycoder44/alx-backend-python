import time
import sqlite3 
import functools

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

def retry_on_failure(retries=3, delay=2):
    """
    Decorator that retries database operations if they fail due to transient errors.
    
    Retries the function a specified number of times with a delay between attempts
    if it raises an exception. If all retries are exhausted, the last exception
    is re-raised.
    
    Args:
        retries (int): Number of retry attempts (default: 3)
        delay (int/float): Delay in seconds between retry attempts (default: 2)
        
    Returns:
        The decorator function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            # Try the function retries + 1 times (initial attempt + retries)
            for attempt in range(retries + 1):
                try:
                    # Attempt to execute the function
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    last_exception = e
                    
                    # If this is not the last attempt, wait and try again
                    if attempt < retries:
                        print(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay} seconds...")
                        time.sleep(delay)
                    else:
                        # All retries exhausted, log final failure
                        print(f"All {retries + 1} attempts failed. Final error: {e}")
            
            # Re-raise the last exception if all attempts failed
            raise last_exception
        
        return wrapper
    return decorator

@with_db_connection
@retry_on_failure(retries=3, delay=1)
def fetch_users_with_retry(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    return cursor.fetchall()

#### attempt to fetch users with automatic retry on failure

users = fetch_users_with_retry()
print(users)