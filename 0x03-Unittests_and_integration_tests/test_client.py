#!/usr/bin/env python3
"""Unit tests for client module.
"""
import unittest
from unittest.mock import patch
from parameterized import parameterized
from client import GithubOrgClient


class TestGithubOrgClient(unittest.TestCase):
    """Test class for GithubOrgClient.
    """

    @parameterized.expand([
        ("google",),
        ("abc",),
    ])
    @patch('client.get_json')
    def test_org(self, org_name, mock_get_json):
        """Test that GithubOrgClient.org returns the correct value.
        """
        test_payload = {"org": org_name}
        mock_get_json.return_value = test_payload
        
        client = GithubOrgClient(org_name)
        result = client.org
        
        expected_url = f"https://api.github.com/orgs/{org_name}"
        mock_get_json.assert_called_once_with(expected_url)
        self.assertEqual(result, test_payload)

    def test_public_repos_url(self):
        """Test that _public_repos_url returns the expected URL.
        """
        expected_repos_url = "https://api.github.com/orgs/test/repos"
        payload = {"repos_url": expected_repos_url}
        
        with patch.object(GithubOrgClient, 'org', new_callable=lambda: payload):
            client = GithubOrgClient("test")
            result = client._public_repos_url
            self.assertEqual(result, expected_repos_url)

    @patch('client.get_json')
    def test_public_repos(self, mock_get_json):
        """Test that public_repos returns expected list of repos.
        """
        test_payload = [
            {"name": "repo1"},
            {"name": "repo2"},
            {"name": "repo3"},
        ]
        mock_get_json.return_value = test_payload
        
        with patch.object(
            GithubOrgClient, '_public_repos_url',
            new_callable=lambda: "https://api.github.com/orgs/test/repos"
        ) as mock_public_repos_url:
            client = GithubOrgClient("test")
            result = client.public_repos()
            
            expected_repos = ["repo1", "repo2", "repo3"]
            self.assertEqual(result, expected_repos)
            mock_public_repos_url.assert_called_once()
            mock_get_json.assert_called_once()


if __name__ == '__main__':
    unittest.main()