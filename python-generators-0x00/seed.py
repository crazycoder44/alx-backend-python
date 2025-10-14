#!/usr/bin/python3
"""
Database setup and data seeding module for ALX_prodev database.
This module provides functions to connect to MySQL, create database and tables,
and populate the user_data table with CSV data.
"""

import mysql.connector
import csv
import uuid
from mysql.connector import Error


def connect_db():
    """
    Connects to the MySQL database server.
    
    Returns:
        mysql.connector.connection: Database connection object if successful, None otherwise
    """
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password=''  # Default password, adjust as needed
        )
        
        if connection.is_connected():
            print("Successfully connected to MySQL server")
            return connection
            
    except Error as e:
        print(f"Error connecting to MySQL server: {e}")
        return None


def create_database(connection):
    """
    Creates the database ALX_prodev if it does not exist.
    
    Args:
        connection: MySQL connection object
    """
    try:
        cursor = connection.cursor()
        
        # Check if database exists
        cursor.execute("SHOW DATABASES LIKE 'ALX_prodev'")
        result = cursor.fetchone()
        
        if not result:
            # Create database if it doesn't exist
            cursor.execute("CREATE DATABASE ALX_prodev")
            print("Database ALX_prodev created successfully")
        else:
            print("Database ALX_prodev already exists")
            
        cursor.close()
        
    except Error as e:
        print(f"Error creating database: {e}")


def connect_to_prodev():
    """
    Connects to the ALX_prodev database in MySQL.
    
    Returns:
        mysql.connector.connection: Database connection object if successful, None otherwise
    """
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',  # Default password, adjust as needed
            database='ALX_prodev'
        )
        
        if connection.is_connected():
            print("Successfully connected to ALX_prodev database")
            return connection
            
    except Error as e:
        print(f"Error connecting to ALX_prodev database: {e}")
        return None


def create_table(connection):
    """
    Creates a table user_data if it does not exist with the required fields.
    
    Args:
        connection: MySQL connection object
    """
    try:
        cursor = connection.cursor()
        
        # Create table with specified schema
        create_table_query = """
        CREATE TABLE IF NOT EXISTS user_data (
            user_id CHAR(36) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            age DECIMAL(3,0) NOT NULL,
            INDEX idx_user_id (user_id)
        )
        """
        
        cursor.execute(create_table_query)
        print("Table user_data created successfully")
        cursor.close()
        
    except Error as e:
        print(f"Error creating table: {e}")


def insert_data(connection, csv_file):
    """
    Inserts data into the database from CSV file if it does not exist.
    
    Args:
        connection: MySQL connection object
        csv_file (str): Path to the CSV file containing user data
    """
    try:
        cursor = connection.cursor()
        
        # Check if data already exists
        cursor.execute("SELECT COUNT(*) FROM user_data")
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"Data already exists in user_data table ({count} records)")
            cursor.close()
            return
        
        # Read CSV file and insert data
        insert_query = """
        INSERT INTO user_data (user_id, name, email, age)
        VALUES (%s, %s, %s, %s)
        """
        
        records_inserted = 0
        
        try:
            with open(csv_file, 'r', newline='', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                
                for row in csv_reader:
                    # Generate UUID for user_id if not present or invalid
                    user_id = row.get('user_id')
                    if not user_id or len(user_id) != 36:
                        user_id = str(uuid.uuid4())
                    
                    name = row.get('name', '').strip()
                    email = row.get('email', '').strip()
                    age = row.get('age', 0)
                    
                    # Validate required fields
                    if name and email and age:
                        try:
                            age = int(float(age))  # Convert to integer
                            cursor.execute(insert_query, (user_id, name, email, age))
                            records_inserted += 1
                        except ValueError:
                            print(f"Invalid age value for user {name}: {age}")
                            continue
                    else:
                        print(f"Skipping incomplete record: {row}")
                        continue
                
                # Commit all insertions
                connection.commit()
                print(f"Successfully inserted {records_inserted} records into user_data table")
                
        except FileNotFoundError:
            print(f"CSV file '{csv_file}' not found")
        except Exception as e:
            print(f"Error reading CSV file: {e}")
            
        cursor.close()
        
    except Error as e:
        print(f"Error inserting data: {e}")
        if connection.is_connected():
            connection.rollback()


def main():
    """
    Main function to demonstrate the database setup process.
    """
    # Connect to MySQL server
    connection = connect_db()
    if not connection:
        return
    
    # Create database
    create_database(connection)
    connection.close()
    
    # Connect to ALX_prodev database
    connection = connect_to_prodev()
    if not connection:
        return
    
    # Create table
    create_table(connection)
    
    # Insert data from CSV
    insert_data(connection, 'user_data.csv')
    
    # Close connection
    connection.close()
    print("Database setup completed successfully")


if __name__ == "__main__":
    main()