import sqlite3
from typing import Optional, Any, Tuple, List, Union


class ExecuteQuery:
    """
    A reusable context manager class for executing database queries with automatic
    connection and query execution management.
    
    This class provides automatic connection opening, query execution, and resource
    cleanup using the context manager protocol (__enter__ and __exit__ methods).
    """
    
    def __init__(self, db_path: str = "database.db", query: str = "", parameters: Union[Tuple, List] = ()):
        """
        Initialize the ExecuteQuery context manager.
        
        Args:
            db_path (str): Path to the SQLite database file
            query (str): SQL query to execute
            parameters (Union[Tuple, List]): Parameters for the SQL query
        """
        self.db_path = db_path
        self.query = query
        self.parameters = parameters
        self.connection: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        self.results: Optional[List[Tuple]] = None
    
    def __enter__(self) -> List[Tuple]:
        """
        Enter the context manager, establish database connection, and execute query.
        
        Returns:
            List[Tuple]: Results of the executed query
        """
        try:
            # Establish database connection
            self.connection = sqlite3.connect(self.db_path)
            self.cursor = self.connection.cursor()
            print(f"Database connection established to {self.db_path}")
            
            # Execute the query with parameters
            if self.parameters:
                self.cursor.execute(self.query, self.parameters)
            else:
                self.cursor.execute(self.query)
            
            # Fetch all results
            self.results = self.cursor.fetchall()
            print(f"Query executed successfully: {self.query}")
            
            return self.results
            
        except sqlite3.Error as e:
            print(f"Database error occurred: {e}")
            raise
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            raise
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Exit the context manager and clean up database resources.
        
        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred  
            exc_tb: Exception traceback if an exception occurred
        """
        if self.cursor:
            self.cursor.close()
            print("Database cursor closed")
        
        if self.connection:
            if exc_type is None:
                # No exception occurred, commit the transaction
                self.connection.commit()
                print("Transaction committed")
            else:
                # Exception occurred, rollback the transaction
                self.connection.rollback()
                print("Transaction rolled back due to exception")
            
            self.connection.close()
            print("Database connection closed")


# Use the context manager to execute the required query
try:
    with ExecuteQuery(query="SELECT * FROM users WHERE age > ?", parameters=(25,)) as results:
        # Print the results
        print(f"\n--- Query Results: SELECT * FROM users WHERE age > ? with parameter 25 ---")
        if results:
            print(f"Found {len(results)} users with age > 25:")
            print("-" * 60)
            
            for row in results:
                print(row)
        else:
            print("No users found with age > 25.")
            
except sqlite3.Error as e:
    print(f"Database error occurred: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")