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

def transactional(func):
    """
    Decorator that manages database transactions automatically.
    
    Wraps the function in a database transaction. If the function executes
    successfully, the transaction is committed. If an exception occurs,
    the transaction is rolled back.
    
    Args:
        func: The function to be decorated (should accept conn as first parameter)
        
    Returns:
        The wrapper function that manages transactions
    """
    @functools.wraps(func)
    def wrapper(conn, *args, **kwargs):
        try:
            # Begin transaction (implicit with first statement)
            result = func(conn, *args, **kwargs)
            # If function executes successfully, commit the transaction
            conn.commit()
            return result
        except Exception as e:
            # If an error occurs, rollback the transaction
            conn.rollback()
            # Re-raise the exception to maintain original error behavior
            raise e
    
    return wrapper

@with_db_connection 
@transactional 
def update_user_email(conn, user_id, new_email): 
    cursor = conn.cursor() 
    cursor.execute("UPDATE users SET email = ? WHERE id = ?", (new_email, user_id)) 

#### Update user's email with automatic transaction handling 

update_user_email(user_id=1, new_email='Crawford_Cartwright@hotmail.com')