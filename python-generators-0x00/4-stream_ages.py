#!/usr/bin/python3
"""
Memory-efficient age streaming module for calculating aggregate functions.
This module provides functions to stream user ages and calculate average without loading entire dataset into memory.
"""

import mysql.connector
from mysql.connector import Error


def stream_user_ages():
    """
    Generator function that yields user ages one by one from the user_data table.
    
    Yields:
        int: User age from the database
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
            cursor = connection.cursor()
            cursor.execute("SELECT age FROM user_data")
            
            # Loop 1: Fetch and yield ages one by one
            for row in cursor:
                yield row[0]  # row[0] contains the age value
                
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


def calculate_average_age():
    """
    Calculate the average age using the generator without loading entire dataset into memory.
    
    Returns:
        float: The average age of all users
    """
    total_age = 0
    count = 0
    
    # Loop 2: Process ages one by one to calculate average
    for age in stream_user_ages():
        total_age += age
        count += 1
    
    if count == 0:
        return 0
    
    return total_age / count


def main():
    """
    Main function to calculate and print the average age.
    """
    try:
        average_age = calculate_average_age()
        print(f"Average age of users: {average_age}")
    except Exception as e:
        print(f"Error calculating average age: {e}")


if __name__ == "__main__":
    main()