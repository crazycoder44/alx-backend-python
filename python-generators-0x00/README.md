# Python Generators - Database Seeding

This project implements a database seeding system for the ALX_prodev MySQL database, designed to set up the database schema and populate it with user data from a CSV file.

## Project Overview

The main objective is to create a generator that can stream rows from an SQL database one by one. This project focuses on the initial database setup and data population phase.

## Files

- `seed.py` - Main database setup and seeding module
- `README.md` - Project documentation

## Database Schema

### Database: `ALX_prodev`

### Table: `user_data`
| Field | Type | Constraints |
|-------|------|-------------|
| user_id | CHAR(36) | PRIMARY KEY, UUID, Indexed |
| name | VARCHAR(255) | NOT NULL |
| email | VARCHAR(255) | NOT NULL |
| age | DECIMAL(3,0) | NOT NULL |

## Functions

The `seed.py` module implements the following functions:

### `connect_db()`
- **Purpose**: Connects to the MySQL database server
- **Returns**: MySQL connection object if successful, None otherwise
- **Usage**: Initial connection to MySQL server before database creation

### `create_database(connection)`
- **Purpose**: Creates the database `ALX_prodev` if it does not exist
- **Parameters**: 
  - `connection`: MySQL connection object
- **Features**: Checks for existing database before creation

### `connect_to_prodev()`
- **Purpose**: Connects to the ALX_prodev database in MySQL
- **Returns**: MySQL connection object for the ALX_prodev database
- **Usage**: Specific connection to the ALX_prodev database for table operations

### `create_table(connection)`
- **Purpose**: Creates the user_data table if it does not exist
- **Parameters**:
  - `connection`: MySQL connection object
- **Features**: Creates table with proper schema including UUID primary key and index

### `insert_data(connection, csv_file)`
- **Purpose**: Inserts data from CSV file into the database if it does not exist
- **Parameters**:
  - `connection`: MySQL connection object
  - `csv_file`: Path to the CSV file containing user data
- **Features**:
  - Checks for existing data to avoid duplicates
  - Validates data before insertion
  - Generates UUID for user_id if not present
  - Handles errors gracefully

## Requirements

### Dependencies
- `mysql-connector-python`: MySQL database connector
- `csv`: CSV file handling (built-in)
- `uuid`: UUID generation (built-in)

### Installation
```bash
pip install mysql-connector-python
```

### MySQL Setup
- MySQL server running on localhost
- Default user: `root`
- Default password: `` (empty) - adjust in code as needed
- Sufficient privileges to create databases and tables

## Usage

### Basic Usage
```python
#!/usr/bin/python3
import seed

# Connect to MySQL server
connection = seed.connect_db()
if connection:
    # Create database
    seed.create_database(connection)
    connection.close()
    
    # Connect to ALX_prodev database
    connection = seed.connect_to_prodev()
    if connection:
        # Create table and insert data
        seed.create_table(connection)
        seed.insert_data(connection, 'user_data.csv')
        connection.close()
```

### Expected CSV Format
The CSV file should contain the following columns:
- `user_id` (optional - will be generated if missing)
- `name` (required)
- `email` (required)
- `age` (required - numeric)

Example CSV structure:
```csv
user_id,name,email,age
00234e50-34eb-4ce2-94ec-26e3fa749796,Dan Altenwerth Jr.,Molly59@gmail.com,67
006bfede-724d-4cdd-a2a6-59700f40d0da,Glenda Wisozk,Miriam21@gmail.com,119
```

## Features

### Error Handling
- Comprehensive error handling for database connections
- Graceful handling of missing or invalid CSV data
- Transaction rollback on insertion errors
- Validation of required fields

### Data Integrity
- UUID validation and generation
- Duplicate data prevention
- Data type validation
- Transaction-based insertions

### Performance Considerations
- Batch insertion with commit
- Index on user_id for faster lookups
- Efficient duplicate checking

## Testing

The module can be tested using the provided test framework:

```python
#!/usr/bin/python3
seed = __import__('seed')

connection = seed.connect_db()
if connection:
    seed.create_database(connection)
    connection.close()
    print("Connection successful")

    connection = seed.connect_to_prodev()
    if connection:
        seed.create_table(connection)
        seed.insert_data(connection, 'user_data.csv')
        
        # Verify database and data
        cursor = connection.cursor()
        cursor.execute("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = 'ALX_prodev'")
        result = cursor.fetchone()
        if result:
            print("Database ALX_prodev is present")
        
        cursor.execute("SELECT * FROM user_data LIMIT 5")
        rows = cursor.fetchall()
        print(rows)
        
        cursor.close()
        connection.close()
```

## Configuration

### Database Configuration
Update the connection parameters in the functions as needed:
- Host: Default `localhost`
- User: Default `root`
- Password: Default empty string
- Port: Default MySQL port (3306)

### CSV File Path
Ensure the CSV file path is correct when calling `insert_data()`. The default expectation is `user_data.csv` in the same directory.

## Security Considerations

- Use environment variables for database credentials in production
- Implement proper SQL injection prevention (using parameterized queries)
- Validate and sanitize input data
- Use appropriate database user permissions

## Future Enhancements

- Configuration file support for database settings
- Support for different CSV formats
- Batch processing for large datasets
- Logging system for better debugging
- Connection pooling for better performance

## Repository Information

- **Repository**: alx-backend-python
- **Directory**: python-generators-0x00
- **Files**: seed.py, README.md