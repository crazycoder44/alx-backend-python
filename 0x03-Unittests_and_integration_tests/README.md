# 0x03. Unittests and Integration Tests

This project contains unit tests and integration tests for various utility functions in Python.

## Description

This project focuses on understanding and implementing unit tests and integration tests using Python's unittest framework and parameterized testing.

## Requirements

- All files are interpreted/compiled on Ubuntu 18.04 LTS using python3 (version 3.7)
- All files must end with a new line
- The first line of all files should be exactly `#!/usr/bin/env python3`
- A README.md file at the root of the project folder is mandatory
- Code should use the pycodestyle style (version 2.5)
- All files must be executable
- All modules should have documentation
- All classes should have documentation
- All functions (inside and outside a class) should have documentation
- All functions and coroutines must be type-annotated

## Files

- `utils.py` - Contains utility functions including access_nested_map
- `test_utils.py` - Unit tests for the utils module

## Tasks

### Task 0: Parameterize a unit test
- Create TestAccessNestedMap class that inherits from unittest.TestCase
- Implement test_access_nested_map method using @parameterized.expand decorator
- Test the access_nested_map function with different inputs

### Task 1: Parameterize a unit test for exceptions
- Implement TestAccessNestedMap.test_access_nested_map_exception method
- Use assertRaises context manager to test KeyError exceptions
- Verify that correct exception messages are raised for invalid paths
- Test with empty nested_map and invalid nested paths

### Task 2: Mock HTTP calls
- Create TestGetJson class that inherits from unittest.TestCase
- Implement test_get_json method to test utils.get_json function
- Use unittest.mock.patch to mock requests.get and avoid actual HTTP calls
- Test that mocked get method is called exactly once with correct URL
- Verify that get_json returns the expected payload from the mock

## Usage

To run the tests:
```bash
python3 -m unittest test_utils.py
```

To run specific test:
```bash
python3 -m unittest test_utils.TestAccessNestedMap.test_access_nested_map
```

## Dependencies

- parameterized library for parameterized testing

Install with:
```bash
pip3 install parameterized
```