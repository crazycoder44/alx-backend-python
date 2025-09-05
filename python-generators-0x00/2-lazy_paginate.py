#!/usr/bin/python3
"""
Lazy pagination module for streaming user data from MySQL database.
This module provides functions to fetch paginated data lazily, loading each page only when needed.
"""

import mysql.connector
from mysql.connector import Error


def paginate_users(page_size, offset):
    """
    Fetches a specific page of users from the database.
    
    Args:
        page_size (int): Number of users to fetch per page
        offset (int): Number of rows to skip (for pagination)
        
    Returns:
        list: List of user dictionaries for the requested page
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
            cursor = connection.cursor(dictionary=True)
            cursor.execute(f"SELECT * FROM user_data LIMIT {page_size} OFFSET {offset}")
            rows = cursor.fetchall()
            return rows
            
    except Error as e:
        print(f"Database error: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []
    finally:
        # Clean up resources
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def lazy_paginate(page_size):
    """
    Generator function that implements lazy pagination, fetching pages only when needed.
    
    Args:
        page_size (int): Number of users to fetch per page
        
    Yields:
        list: A list of user dictionaries for each page
    """
    offset = 0
    
    # Single loop to fetch pages lazily
    while True:
        page = paginate_users(page_size, offset)
        if not page:  # No more data
            break
        yield page
        offset += page_size


# Alias for the function name used in the test
lazy_pagination = lazy_paginate