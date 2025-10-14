import sqlite3
from typing import Optional, Any


class DatabaseConnection:
    """
    A context manager class for handling database connections automatically.
    
    This class provides automatic connection opening and closing using the
    context manager protocol (__enter__ and __exit__ methods).
    """
    
    def __init__(self, db_path: str = "database.db"):
        """
        Initialize the DatabaseConnection context manager.
        
        Args:
            db_path (str): Path to the SQLite database file
        """
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
    
    def __enter__(self) -> sqlite3.Cursor:
        """
        Enter the context manager and establish database connection.
        
        Returns:
            sqlite3.Cursor: Database cursor for executing queries
        """
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.cursor = self.connection.cursor()
            print(f"Database connection established to {self.db_path}")
            return self.cursor
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
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


def main():
    """
    Main function demonstrating the usage of DatabaseConnection context manager.
    """
    # Use the context manager to perform database operations
    try:
        with DatabaseConnection() as cursor:
            # Execute the SELECT query for users
            cursor.execute("SELECT * FROM users")
            results = cursor.fetchall()
            
            # Print the results
            print("\n--- Query Results: SELECT * FROM User ---")
            if results:
                # Get column names for better display
                column_names = [description[0] for description in cursor.description]
                print(f"Columns: {', '.join(column_names)}")
                print("-" * 50)
                
                for row in results:
                    print(row)
            else:
                print("No users found in the database.")
                
    except sqlite3.Error as e:
        print(f"Database error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()