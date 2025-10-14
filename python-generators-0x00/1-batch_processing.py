#!/usr/bin/python3
"""
Batch processing module for streaming and filtering user data from MySQL database.
This module provides functions to fetch data in batches and process them efficiently.
"""

import mysql.connector
from mysql.connector import Error


def stream_users_in_batches(batch_size):
    """
    Generator function that fetches rows in batches from the user_data table.
    
    Args:
        batch_size (int): Number of rows to fetch in each batch
        
    Yields:
        list: A list of dictionaries containing user data for each batch
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
            cursor.execute("SELECT user_id, name, email, age FROM user_data")
            
            # Loop 1: Fetch data in batches
            while True:
                batch = cursor.fetchmany(batch_size)
                if not batch:
                    break
                yield batch
                
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


def batch_processing(batch_size):
    """
    Processes each batch to filter users over the age of 25.
    
    Args:
        batch_size (int): Number of rows to process in each batch
    """
    # Loop 2: Process each batch
    for batch in stream_users_in_batches(batch_size):
        # Loop 3: Filter users in each batch
        for user in batch:
            if user['age'] > 25:
                print(user)