#!/usr/bin/python3
"""
Generator module for streaming user data from MySQL database.
This module provides a generator function to fetch rows one by one from the user_data table.
"""

import mysql.connector
from mysql.connector import Error


def stream_users():
    """
    Generator function that streams rows one by one from the user_data table.
    
    Yields:
        dict: A dictionary containing user data with keys: user_id, name, email, age
        
    Example:
        >>> for user in stream_users():
        ...     print(user)
        {'user_id': '12345...', 'name': 'John Doe', 'email': 'john@example.com', 'age': 30}
    """
    connection = None
    cursor = None
    
    try:
        # Connect to the ALX_prodev database
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',  # Adjust as needed
            database='ALX_prodev'
        )
        
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)  # Use dictionary cursor for easy access
            
            # Execute query to fetch all users
            cursor.execute("SELECT user_id, name, email, age FROM user_data")
            
            # Use single loop to fetch and yield rows one by one
            for row in cursor:
                yield row
                
    except Error as e:
        print(f"Database error: {e}")
        return
    except Exception as e:
        print(f"Unexpected error: {e}")
        return
    finally:
        # Clean up resources
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()