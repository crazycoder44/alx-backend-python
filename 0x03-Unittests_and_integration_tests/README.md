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

### Task 3: Parameterize and patch
- Create TestMemoize class that inherits from unittest.TestCase
- Implement test_memoize method to test the memoize decorator
- Define a TestClass with a_method and memoized a_property inside the test
- Use unittest.mock.patch to mock a_method and verify memoization behavior
- Test that a_property returns correct result and a_method is called only once

### Task 4: Parameterize and patch as decorators
- Create new test_client.py file with TestGithubOrgClient class
- Implement test_org method to test GithubOrgClient.org property
- Use @patch as decorator to mock get_json and prevent HTTP calls
- Use @parameterized.expand as decorator to test with multiple org names
- Verify that get_json is called once with correct URL and returns expected value

### Task 5: Mocking a property
- Implement test_public_repos_url method in TestGithubOrgClient class
- Use patch as context manager to mock GithubOrgClient.org property
- Test that _public_repos_url returns the expected URL from mocked org payload
- Demonstrate how to mock properties created by the memoize decorator

### Task 6: More patching
- Implement test_public_repos method in TestGithubOrgClient class
- Use @patch as decorator to mock get_json with custom payload
- Use patch as context manager to mock _public_repos_url property
- Test that public_repos returns expected list of repository names
- Verify that both mocked property and mocked get_json are called exactly once

### Task 7: Parameterize
- Implement test_has_license method in TestGithubOrgClient class
- Use @parameterized.expand to test GithubOrgClient.has_license static method
- Test with different repo license configurations and license keys
- Parameterize both input values and expected return values
- Verify that has_license correctly identifies matching and non-matching licenses

### Task 8: Integration test: fixtures
- Create TestIntegrationGithubOrgClient class for integration testing
- Use @parameterized_class decorator with fixtures from fixtures.py
- Implement setUpClass to mock requests.get with side_effect for different URLs
- Implement tearDownClass to properly stop the patcher
- Set up integration test framework for testing with real-like data payloads

### Task 9: Integration tests
- Implement test_public_repos method in TestIntegrationGithubOrgClient class
- Test that public_repos returns expected list of repositories from fixtures
- Implement test_public_repos_with_license method to test license filtering
- Test that public_repos with apache-2.0 license filter returns correct repos
- Verify integration between GithubOrgClient methods using realistic fixtures

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