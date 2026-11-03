# Licensing

The master needs a license file before it can start. The license lives on the
master only: agents don't need one, and they don't need an email address
either.

## What the license controls

Probe types are grouped into four bundles. Your license says which bundles you
can use, how many targets each one may monitor, and how many agents you can
enroll.

| Bundle | Probe types |
|---|---|
| `web` | `http`, `ssl_expiry`, `dns` |
| `reachability` | `ping`, `batch_ping`, `tcp`, `traceroute`, `alive`, `ntp`, `mtu` |
| `performance` | `throughput`, `dns_propagation`, `snmp` |
| `routing` | `bgp` |

Results stores are free in every tier. If a probe uses a bundle your license
doesn't include, the master won't start, and its log names the probe with the
error `bundle_not_licensed`.

## The free tier

- Up to five agents. On an all-in-one host, the local agent is one of them.
  Agents you've revoked don't count.
- All four bundles, with up to 15 web, 20 reachability, 10 performance and 5
  routing targets.
- A one-year term that renews by itself while the master can reach
  `api.trcr.dev`.
- One free license per verified email address. If you reinstall, verifying the
  address again downloads the same license.

## Get a free license

The all-in-one install can do this for you (see
[Install TRCR](install.md#install-everything-on-one-host)). To do it by hand,
run this on the master:

```bash
sudo trcrd license request --email you@example.com --company "Your Company" --wait
```

It shows what it's about to send and asks you to confirm; add `--yes` to skip
the question. Then we email you a verification link. While you open your
inbox, the command waits and says so:

```
waiting for the verification link sent to you@example.com to be opened; this finishes within seconds of the click (Ctrl-C is safe — resume with `trcrd license claim --wait`)
```

It isn't stuck. Click the link, and within a few seconds the license is saved
to `/etc/trcr/license.lic`:

```
license installed: /etc/trcr/license.lic
```

If you stop the command with Ctrl-C, nothing is lost. Pick it up again with:

```bash
sudo trcrd license claim --wait
```

If the master is already running, `claim` restarts it so the license takes
effect, and checks it came back up. Add `--no-restart` to restart it yourself
later. A master that's stopped stays stopped; start it with
`sudo /etc/trcr/finish-setup.sh`.

You can also split the two steps: run `license request` without `--wait`, click
the link, then run `sudo trcrd license claim`.

## Paid tiers

To ask for a paid license, run this on the master:

```bash
sudo trcrd license request --tier paid --email you@example.com --company "Your Company"
```

We review paid requests before issuing a license. Until it's ready,
`trcrd license claim` exits with status 3; once it's issued, the same command
installs it. We also email you the license file.

## Install a license file

If you have the license as a file, install it on the master so the `trcr`
user can read it, then restart the master:

```bash
sudo install -o root -g trcr -m 0640 license.lic /etc/trcr/license.lic
sudo systemctl restart trcrd-master
```

Use `install` rather than `cp`. A copy made with `sudo cp` is readable by root
only, and the master, which runs as the `trcr` user, then won't start. If that
happens, its log names the file and gives the `chgrp` and `chmod` that fix it.

## Check your license

To see the installed license, any renewed copy, the master's last check-in and
any request that's still waiting, run:

```bash
sudo trcrd license status
```

It needs `sudo`: run as an ordinary user, it prints only
`trcrd license: cannot read /etc/trcr/master.yaml (permission denied) — run it with sudo`,
not a misleading `installed license: none`. You'll see something like this:

```
installed license: /etc/trcr/license.lic (id=… tier=free expires=…)
last heartbeat:    2026-11-03 02:11 UTC — ok
```

The `last heartbeat:` line is the outcome of the master's most recent check-in
with `api.trcr.dev`:

| It says | What it means |
|---|---|
| `ok` | The check-in worked. |
| `refused (<code>: <detail>)` | The TRCR API refused the license. See [below](#the-masters-log-says-the-trcr-api-is-refusing-the-license). |
| `failed (…)` | The check-in didn't get through, for example because of the network. The master keeps trying. |
| `none recorded yet` | The master hasn't checked in since it last started on this version. The first check-in happens soon after it starts. |
| `never attempted (heartbeat disabled)` | Check-ins are turned off in `master.yaml`. |

## Renewal

The master renews a free license by itself during its hourly check-in with
`api.trcr.dev`. It saves the renewed file to `/var/lib/trcr/license.lic`,
because the service isn't allowed to write to `/etc/trcr`. The master finds
the renewed file by itself, and `trcrd license status` shows both.

A renewed license takes effect the next time the master starts. The master
doesn't restart itself; it logs `license renewed via heartbeat; restart to
apply` so you can choose when.

When a license expires, the master stops. A failed check-in doesn't stop it:
monitoring carries on, and the master keeps trying.

## If something goes wrong

### The verification email didn't arrive

Check your spam folder first. Then ask for a new link:

```bash
sudo trcrd license resend
```

The new link works for 24 hours, and the old one stops working.

Don't run `license request` again to get a new email. A new request cancels
the old one, even one made on a different host with the same address, and
you'd be left with two links of which only one works.

### `claim` says the request isn't recognized

Usually a second `license request` was made for the same email address, on
this host or another. Each new request replaces the one before. The command
shows the request it has on file and how old it is, and walks you through the
options: resend, claim on the other host, or start again on purpose. A request
can be claimed for 30 days.

### The master still says it has no license after you claimed one

The master reads its license once, when it starts. Restart it:

```bash
sudo systemctl restart trcrd-master
```

### The master's log says the TRCR API is refusing the license

The line looks like this:

```
heartbeat: the TRCR API is refusing this license (<code>: <detail>); monitoring continues unaffected — run `trcrd license status`, and contact support@trcr.dev if the license should be valid
```

The master logs it after three refused check-ins in a row. Your monitoring
isn't affected. Run `sudo trcrd license status` and look at the
`last heartbeat:` line. If it says `refused` and the license should be valid,
email support@trcr.dev with the code and detail it shows.

### Move a license to another host

Copy `/etc/trcr/license.lic` to the new master and install it there as shown
in [Install a license file](#install-a-license-file), or request it again with
the same email address. Before you uninstall with `--purge`, keep a copy of the
file somewhere safe.
