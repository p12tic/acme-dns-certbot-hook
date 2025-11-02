# acme-dns-certbot-hook

A [Certbot](https://certbot.eff.org) client hook for [acme-dns](https://github.com/joohoi/acme-dns).

This authentication hook automatically registers acme-dns accounts and prompts the user to manually add the CNAME records to their main DNS zone on initial run. Subsequent automatic renewals by Certbot cron job / systemd timer run in the background non-interactively.

Requires Certbot >= 0.10, Python requests library.

## Installation

1) Install Certbot using instructions at [https://certbot.eff.org](https://certbot.eff.org)

2) Make sure you have the [python-requests](http://docs.python-requests.org/en/master/) library installed.

3) Download the authentication hook script and make it executable:
```
$ curl -o /etc/letsencrypt/acme-dns-auth.py https://raw.githubusercontent.com/p12tic/acme-dns-certbot-hook/master/acme-dns-auth.py
$ chmod 0700 /etc/letsencrypt/acme-dns-auth.py
```

4) Configure the hook script file to point to your acme-dns instance. Either put configuration file at `/etc/letsencrypt/acme-dns-certbot-hook-config.json`, or pass configuration via environment variables. Example contents of `/etc/letsencrypt/acme-dns-certbot-hook-config.json`:

```
{
    "url": "https://custom.example.com",
    "allow_from": ["192.168.1.0/24", "10.0.0.0/8"],
    "force_register": true
}
```

Equivalent environment variables that need to be setup before running certbot:

```
ACMEDNS_URL="https://custom.example.com"
ACMEDNS_ALLOW_FROM='["192.168.1.0/24", "10.0.0.0/8"]'
ACMEDNS_FORCE_REGISTER=true
```

## Usage

On initial run:
```
$ certbot certonly --manual --manual-auth-hook /etc/letsencrypt/acme-dns-auth.py \
   --preferred-challenges dns --debug-challenges                                 \
   -d example.org -d \*.example.org
```
Note that the `--debug-challenges` is mandatory here to pause the Certbot execution before asking Let's Encrypt to validate the records and let you to manually add the CNAME records to your main DNS zone.

After adding the prompted CNAME records to your zone(s), wait for a bit for the changes to propagate over the main DNS zone name servers. This takes anywhere from few seconds up to a few minutes, depending on the DNS service provider software and configuration. Hit enter to continue as prompted to ask Let's Encrypt to validate the records.

After the initial run, Certbot is able to automatically renew your certificates using the stored per-domain acme-dns credentials.
