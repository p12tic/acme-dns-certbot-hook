#!/usr/bin/env python3
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from acme_dns_auth import build_acme_dns_config_from_env


class TestBuildAcmeDnsConfigFromEnv(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_config_file.close()

    def tearDown(self) -> None:
        if os.path.exists(self.temp_config_file.name):
            os.unlink(self.temp_config_file.name)

    @patch.dict(
        os.environ,
        {
            'ACMEDNS_URL': 'https://acme-dns.env.example.com',
            'ACMEDNS_ALLOW_FROM': '["192.168.1.0/24", "10.0.0.0/8"]',
            'ACMEDNS_FORCE_REGISTER': 'true',
        },
    )
    def test_config_from_environment_variables(self) -> None:
        config = build_acme_dns_config_from_env(self.temp_config_file.name)

        self.assertEqual(config.url, 'https://acme-dns.env.example.com')
        self.assertEqual(config.allow_from, ['192.168.1.0/24', '10.0.0.0/8'])
        self.assertTrue(config.force_register)

    @patch.dict(os.environ, {}, clear=True)
    def test_config_from_file(self) -> None:
        config_data = {
            'url': 'https://acme-dns.file.example.com',
            'allow_from': ['192.168.1.0/24'],
            'force_register': True,
        }

        with open(self.temp_config_file.name, 'w') as f:
            json.dump(config_data, f)

        config = build_acme_dns_config_from_env(self.temp_config_file.name)

        self.assertEqual(config.url, 'https://acme-dns.file.example.com')
        self.assertEqual(config.allow_from, ['192.168.1.0/24'])
        self.assertTrue(config.force_register)

    @patch.dict(os.environ, {}, clear=True)
    def test_config_from_file_minimal(self) -> None:
        config_data = {'url': 'https://acme-dns.minimal.example.com'}

        with open(self.temp_config_file.name, 'w') as f:
            json.dump(config_data, f)

        config = build_acme_dns_config_from_env(self.temp_config_file.name)

        self.assertEqual(config.url, 'https://acme-dns.minimal.example.com')
        self.assertEqual(config.allow_from, [])  # Default empty list
        self.assertFalse(config.force_register)  # Default false

    @patch.dict(os.environ, {}, clear=True)
    def test_config_from_file_missing_url(self) -> None:
        config_data = {'allow_from': ['192.168.1.0/24'], 'force_register': True}

        with open(self.temp_config_file.name, 'w') as f:
            json.dump(config_data, f)

        config = build_acme_dns_config_from_env(self.temp_config_file.name)

        self.assertIsNone(config.url)
        self.assertEqual(config.allow_from, ['192.168.1.0/24'])
        self.assertTrue(config.force_register)

    @patch.dict(os.environ, {}, clear=True)
    def test_no_config_available(self) -> None:
        os.unlink(self.temp_config_file.name)

        with self.assertRaises(RuntimeError) as context:
            build_acme_dns_config_from_env(self.temp_config_file.name)

        self.assertIn('No configuration supplied', str(context.exception))

    @patch.dict(os.environ, {}, clear=True)
    def test_invalid_json_in_config_file(self) -> None:
        with open(self.temp_config_file.name, 'w') as f:
            f.write('{ invalid json }')

        with self.assertRaises(RuntimeError) as context:
            build_acme_dns_config_from_env(self.temp_config_file.name)

        self.assertIn('Invalid configuration', str(context.exception))

    @patch.dict(
        os.environ,
        {
            'ACMEDNS_URL': 'https://acme-dns.example.com',
            'ACMEDNS_ALLOW_FROM': 'invalid_json',
            'ACMEDNS_FORCE_REGISTER': 'true',
        },
    )
    def test_invalid_json_in_environment(self) -> None:
        with self.assertRaises(RuntimeError) as context:
            build_acme_dns_config_from_env(self.temp_config_file.name)

        self.assertIn('Invalid configuration', str(context.exception))

    @patch.dict(
        os.environ,
        {
            'ACMEDNS_URL': 'https://acme-dns.example.com',
            'ACMEDNS_ALLOW_FROM': '["192.168.1.0/24"]',
            'ACMEDNS_FORCE_REGISTER': 'not_a_boolean',
        },
    )
    def test_invalid_boolean_in_environment(self) -> None:
        with self.assertRaises(RuntimeError) as context:
            build_acme_dns_config_from_env(self.temp_config_file.name)

        self.assertIn('Invalid configuration', str(context.exception))

    @patch.dict(os.environ, {'ACMEDNS_URL': 'https://acme-dns.example.com'})
    def test_environment_priority_over_file(self) -> None:
        """Test that environment variables take priority over file configuration"""
        config_data = {
            'url': 'https://acme-dns.file.example.com',
            'allow_from': ['should-be-ignored'],
            'force_register': True,
        }

        with open(self.temp_config_file.name, 'w') as f:
            json.dump(config_data, f)

        config = build_acme_dns_config_from_env(self.temp_config_file.name)

        # Should use environment values, not file values
        self.assertEqual(config.url, 'https://acme-dns.example.com')
        self.assertEqual(config.allow_from, [])  # Default from env
