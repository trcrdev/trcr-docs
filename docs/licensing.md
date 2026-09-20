# Licensing

The master needs a valid licence file to start. Agents need nothing: the
licence lives on the master.

## What the licence controls

Probe types are grouped into four bundles. A licence says which bundles you may
use and how many monitored targets each one allows.

| Bundle | Probe types |
|---|---|
| `web` | `http`, `ssl_expiry`, `dns` |
| `reachability` | `ping`, `batch_ping`, `tcp`, `traceroute`, `alive`, `ntp`, `mtu` |
| `performance` | `throughput`, `dns_propagation`, `snmp` |
| `routing` | `bgp` |

Agents and results stores are free in every tier. A probe in a bundle you are
not licensed for stops the master from starting, with the error
`bundle_not_licensed`.

## The free tier

- 5 agents and all four bundles.
- Up to 15 web, 20 reachability, 10 performance and 5 routing targets.
- A one-year term that renews automatically while the master can reach
  `api.trcr.dev`.
- One free licence per verified email address. Reinstalling verifies the
  address again and downloads the same licence.

## Getting a free licence

```bash
sudo trcrd license request --email you@example.com --company "Your Company"
```

Open the verification link in the email, then:

```bash
sudo trcrd license claim --wait
```

This downloads the signed licence to `/etc/trcr/license.lic`. If the master is
already running, `claim` restarts it so the licence takes effect, and checks
that it came back up. Add `--no-restart` to do that yourself later. A master
that is stopped is left stopped.

`--wait` on `request` does both steps in one command: it sends the request and
waits for you to click the link.

```bash
sudo trcrd license request --email you@example.com --company "Your Company" --wait
```

## Paid tiers

```bash
sudo trcrd license request --tier paid --email you@example.com --company "Your Company"
```

Paid requests are reviewed before a licence is issued. `trcrd license claim`
exits with status 3 while the licence is not ready yet, and installs it once it
is. You also receive the licence file by email.

## Checking a licence

```bash
sudo trcrd license status
```

## Renewal

The master renews a free licence automatically during its regular check-in with
`api.trcr.dev`. The renewed file is saved to `/var/lib/trcr/license.lic`, not
next to the original in `/etc/trcr`, because the service may not write to
`/etc/trcr`. The master finds the renewed file by itself, and
`trcrd license status` reports both.

A renewed licence takes effect at the next restart of the master. The master
does not restart itself; it logs a reminder.

When a licence expires, the master stops. A failed check-in does not stop it.

## Problems

### I did not get the verification email

```bash
sudo trcrd license resend
```

This sends a new link, valid for 24 hours, and the old link stops working.
Check your spam folder first.

Do **not** run `license request` again to get a new email. A second request
cancels the first one, including on another host using the same address.

### `claim` says the request is not recognised

The usual cause is a second `license request` for the same email address, on
this host or another. Each new request replaces the one before. The command
prints the request it has on file and its age, and walks you through the
options: resend, claim on the other host, or start again on purpose. A request
can be claimed for 30 days.

### The master still says it has no licence after I claimed one

The licence is read once, when the master starts. Restart it:

```bash
sudo systemctl restart trcrd-master
```

### Moving a licence to another host

Copy `/etc/trcr/license.lic` to the new master, or request it again with the
same email address. Keep a copy of the file before you uninstall with
`--purge`.
