#!/usr/bin/env python3
import json
import os
import sys
from typing import Any

import requests

### EDIT THESE: Configuration values ###

# URL to acme-dns instance
ACMEDNS_URL = 'https://auth.acme-dns.io'
# Path for acme-dns credential storage
STORAGE_PATH = '/etc/letsencrypt/acmedns.json'
# Whitelist for address ranges to allow the updates from
# Example: ALLOW_FROM = ["192.168.10.0/24", "::1/128"]
ALLOW_FROM: list[str] = []
# Force re-registration. Overwrites the already existing acme-dns accounts.
FORCE_REGISTER = False

###   DO NOT EDIT BELOW THIS POINT   ###
###         HERE BE DRAGONS          ###


class AcmeDnsClient:
    """
    Handles the communication with ACME-DNS API
    """

    def __init__(self, acmedns_url: str) -> None:
        self.acmedns_url = acmedns_url

    def register_account(self, allowfrom: list[str]) -> Any:
        """Registers a new ACME-DNS account"""

        if allowfrom:
            # Include whitelisted networks to the registration call
            reg_data = {'allowfrom': allowfrom}
            res = requests.post(self.acmedns_url + '/register', data=json.dumps(reg_data))
        else:
            res = requests.post(self.acmedns_url + '/register')
        if res.status_code == 201:
            # The request was successful
            return res.json()
        else:
            raise RuntimeError(
                'Encountered an error while trying to register a new acme-dns '
                f'account. HTTP status {res.status_code}, Response body: {res.text}'
            )

    def update_txt_record(self, account: dict[str, str], txt: str) -> None:
        """Updates the TXT challenge record to ACME-DNS subdomain."""
        update = {'subdomain': account['subdomain'], 'txt': txt}
        headers = {
            'X-Api-User': account['username'],
            'X-Api-Key': account['password'],
            'Content-Type': 'application/json',
        }
        res = requests.post(self.acmedns_url + '/update', headers=headers, data=json.dumps(update))
        if res.status_code == 200:
            # Successful update
            return
        else:
            s_headers = json.dumps(headers, indent=2, sort_keys=True)
            s_update = json.dumps(update, indent=2, sort_keys=True)
            s_body = json.dumps(res.json(), indent=2, sort_keys=True)
            raise RuntimeError(
                'Encountered an error while trying to update TXT record in acme-dns. \n'
                f'------- Request headers:\n{s_headers}\n'
                f'------- Request body:\n{s_update}\n'
                f'------- Response HTTP status: {res.status_code}\n'
                f'------- Response body: {s_body}'
            )


class Storage:
    def __init__(self, storagepath: str) -> None:
        self.storagepath = storagepath
        self._data = self.load()

    def load(self) -> dict:
        """Reads the storage content from the disk to a dict structure"""
        data = dict()
        filedata = ''
        try:
            with open(self.storagepath) as fh:
                filedata = fh.read()
        except OSError as e:
            if os.path.isfile(self.storagepath):
                # Only error out if file exists, but cannot be read
                raise ValueError('ERROR: Storage file exists but cannot be read') from e
        try:
            data = json.loads(filedata)
        except ValueError:
            if len(filedata) > 0:
                raise RuntimeError('ERROR: Storage JSON is corrupted')
        return data

    def save(self) -> None:
        try:
            with open(self.storagepath, 'w') as f:
                json.dump(self._data, f)
        except OSError as e:
            raise RuntimeError('ERROR: Could not write storage file.') from e

    def put(self, key: str, value: Any) -> None:
        """Puts the configuration value to storage and sanitize it"""
        # If wildcard domain, remove the wildcard part as this will use the
        # same validation record name as the base domain
        if key.startswith('*.'):
            key = key[2:]
        self._data[key] = value

    def fetch(self, key: str) -> Any | None:
        """Gets configuration value from storage"""
        try:
            return self._data[key]
        except KeyError:
            return None


def main() -> None:
    try:
        domain = os.environ['CERTBOT_DOMAIN']
        if domain.startswith('*.'):
            domain = domain[2:]
        validation_domain = '_acme-challenge.' + domain
        validation_token = os.environ['CERTBOT_VALIDATION']

        # Init
        client = AcmeDnsClient(ACMEDNS_URL)
        storage = Storage(STORAGE_PATH)

        # Check if an account already exists in storage
        account = storage.fetch(domain)
        if FORCE_REGISTER or not account:
            # Create and save the new account
            account = client.register_account(ALLOW_FROM)
            storage.put(domain, account)
            storage.save()

            print(
                'Please add the following CNAME record to your main DNS zone:\n'
                + f'{validation_domain}. CNAME {account["fulldomain"]}.'
            )

        # Update the TXT record in acme-dns instance
        client.update_txt_record(account, validation_token)
    except Exception as e:
        print(str(e))
        sys.exit(1)


if __name__ == '__main__':
    main()
