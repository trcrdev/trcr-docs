# Troubleshooting

Start with these four commands. They answer most questions.

```bash
sudo systemctl status trcrd-master        # or trcrd-agent
sudo journalctl -u trcrd-master -n 100    # the last 100 log lines
sudo trcrd agents                         # on the master
sudo trcrd validate --config /etc/trcr/master.yaml
```

For more detail in the log, set `log.level: debug` and restart, and set it back
afterwards.

## Installing

### The installer stops with a signature or OpenSSL error

The installer verifies the download's signature and needs OpenSSL 1.1.1 or
later. Check with `openssl version`. On older systems install a newer OpenSSL
package; the installer names the one to install. On macOS the built-in LibreSSL
does not work: run `brew install openssl` and try again.

If OpenSSL is recent and the signature still fails, do not work around it. Try
again from another network, and if it keeps failing, email support@trcr.dev.

### `curl … | sh --all-in-one` ignores my options

Options need `sh -s --` in front of them:

```bash
curl -fsSL https://trcr.dev/install/install.sh | sh -s -- --all-in-one
```

### The install finished but nothing is running

That is expected when you asked for a free licence with `--email`. The master
cannot start without a licence, and the installer does not wait for you to
click the link. Open the verification email, then either wait up to 15 seconds
or run:

```bash
sudo /etc/trcr/finish-setup.sh
```

### The all-in-one install says it cannot install TimescaleDB

There is no TimescaleDB package for your PostgreSQL version. This is common
with the PostgreSQL 13 that Enterprise Linux 9 ships. The installer carries on
with standard partitioning, which works well. Nothing else is needed.

## The master

### The master will not start

Read the log: `sudo journalctl -u trcrd-master -n 50`. The usual causes:

| Message mentions | Cause and fix |
|---|---|
| licence missing, expired or invalid | See [Licensing](licensing.md#problems). Check the host's clock too. |
| `bundle_not_licensed` | A probe uses a type your licence does not include. Remove it or upgrade. |
| `monitor_limit_exceeded` | More targets in a bundle than the licence allows. The message lists every one over the limit. |
| an unknown key, with a file name | A misspelt or unsupported setting. Configuration is strict. Fix the key it names. |
| an unknown backend name | A probe's `backends:` names a store that is not defined. |
| key file permissions | A key file is readable by others. `sudo chmod 600` the file it names. |
| address already in use | Another program has port 8443, 8444 or 8080. Find it with `sudo ss -ltnp`. |

`sudo trcrd validate` finds most of these without starting anything, and lists
every problem at once.

### The master is running but there is no data

A master whose results store cannot be opened still starts, and throws results
away with a warning.

```bash
sudo journalctl -u trcrd-master | grep -iE "discard|backend"
```

Check, in order:

1. Is there an agent? `sudo trcrd agents`. The master never runs probes itself.
2. Are there probes? `sudo trcrd probes`. Remember that `_samples.yaml` is
   ignored until you copy it to a name without the underscore.
3. Did the secret reach the service?
   `sudo systemctl show trcrd-master -p EnvironmentFiles` should list your
   `.env` file.
4. Can the master reach the database? Try the same address, user and password
   with `psql` or `curl` from the master.
5. Is the results store still `stdout`? Then results are in the journal, not
   in a database.

### I changed the configuration and nothing happened

The master reads its configuration only at startup.
`sudo systemctl restart trcrd-master`. There is no reload signal.

## Agents

### `trcrd join` times out

The agent cannot reach the master's enrolment port.

- Open **both** 8443 and 8444 on the master's firewall, and in any cloud
  firewall or security group.
- From the agent: `nc -vz trcr-master.example.com 8444`.
- Check the address in the one-liner is one the agent can reach. If it is a
  private address and the agent is elsewhere, fix `master.advertise_addr`.

Nothing in the master's log will hint at this, because the master is healthy
and simply cannot be reached.

### An agent is stuck at `never-seen`

The agent enrolled and then never made a successful call. The causes, most
likely first:

1. **`master.advertise_addr` is not set, or is wrong.** The master's
   certificate is then valid only for connections from its own host, and
   every call after enrolment fails. The agent's log shows a certificate error
   saying the certificate is valid for `127.0.0.1` and not for the master's
   address.

   Set `advertise_addr` to an address the agents use, **with the enrolment
   port**, and restart the master. See
   [Configuration](configuration.md#advertise_addr-is-required-for-remote-agents).
   You do not need to enrol the agent again.
2. **Port 8443 is blocked while 8444 is open.** Enrolment uses 8444;
   everything after that uses 8443.
3. **The agent's service is not running.** On the agent:
   `sudo systemctl status trcrd-agent`. If the service is missing, run the
   installer one-liner again; it installs and starts the service without
   enrolling a second time.

### An agent shows `down`

On the agent: `sudo systemctl status trcrd-agent` and
`sudo journalctl -u trcrd-agent -n 50`. Look for connection errors (network or
firewall), certificate errors (was the master rebuilt, or the agent revoked?),
or a full disk.

### `trcrd join` says the host is already enrolled

```
trcrd join: config /etc/trcr/agent.yaml already exists; pass --force to overwrite
```

This is a local check, not a network problem. Run `sudo trcrd leave` first, or
use `--force` if the old enrolment is dead. See
[Agents](agents.md#moving-an-agent-to-another-master).

### The pairing code is rejected

- The code and fingerprint belong together. Print both again on the agent with
  `sudo trcrd join --pending --show-code`.
- Repeated wrong codes are blocked for a short time. Wait a minute and try
  again.
- If the agent was installed with `--accept-from`, the master must connect from
  one of those addresses.
- Check port 8445 is open on the agent.

### I rebuilt the master and no agent connects

A new master has a new certificate authority, so old agent certificates mean
nothing to it. Run `sudo trcrd enroll-agent` on the new master and paste the
one-liner on each agent. The agent sees a different `--ca-hash` and enrols
again. To avoid this, back up and restore `/var/lib/trcr`. See
[Operations](operations.md#backups).

## Probes

### A probe fails with `private_target_refused`

The target resolves to a private or special address. Add
`allow_private_targets: true` to that probe. See
[Probes](probes.md#private-and-internal-targets).

### Ping works from the shell but the probe fails

- Test the same way the agent does: `trcrd run ping <target>` on the agent
  host.
- The target or a firewall may limit ICMP. Try a lower `count` or a longer
  `interval`.
- In a container, the agent needs permission to send ICMP (`NET_RAW`).

### Traceroute shows stars or stops early

Routers often do not answer traceroute packets, and firewalls drop them. A path
that ends in stars while `ping` and `http` to the same target succeed is
normal. The path-change alert compares networks crossed with
`path_level: as`, which copes better with silent hops.

### An HTTP probe fails but the site works in my browser

Run `trcrd run http <url>` on the agent and read the result.

- `unexpected_status`: the site returns a redirect or another code. Add it to
  `expected_status`, or probe the final URL.
- A certificate error: the agent's host lacks the issuing authority. For a
  private authority, check the system's trusted certificates.
- A timeout from one agent only: that is a finding, not a fault. The site is
  slow or unreachable from there.

### A throughput probe fails

- The target agent needs `agent.throughput_server.enabled: true`, and a restart
  after you set it.
- Port 5202 must be open between the two agents.
- Tests longer than 60 seconds are refused, and an agent limits how many tests
  it accepts at once. Space bandwidth tests out.

### SNMP returns nothing

- TRCR uses SNMPv3 only. Check the user, both protocols and both passphrases on
  the device.
- The passphrase variables must start with `TRCR_SNMP_` and must be set on the
  **agent** that runs the probe, in that agent's service environment.
- Devices usually have private addresses: add `allow_private_targets: true`.
- Check the device's access list allows the agent's address.

## Dashboards

### Grafana says "datasource not found"

The datasource uid must be exactly `trcr-postgres` or `trcr-influxdb`. See
[Dashboards](dashboards.md).

### InfluxDB panels say "unauthorized"

Some Grafana versions need the token given twice in the datasource: once as the
token, and once as a custom `Authorization` header with the value
`Token <your token>`. The example datasource file in the
[dashboards repository](https://github.com/trcrdev/trcr-dashboards) sets both.
Also check the datasource's query language is **Flux**.

### A dashboard is empty

- Widen the time range, and check the filters at the top are not excluding
  everything.
- No probe of that type may be running: `sudo trcrd probes --type <type>`.
- You may be using the wrong edition. PostgreSQL dashboards do not work against
  InfluxDB, and the other way round.

### I cannot open Grafana

On an all-in-one host Grafana listens on `127.0.0.1` only. Use an SSH tunnel
(`ssh -L 3000:127.0.0.1:3000 <host>`), or install again with `--open-grafana`.
The admin password is in `/etc/trcr/grafana-admin.env`.

## Licence

See [Licensing](licensing.md#problems).

## Asking for help

Before you [open an issue](https://github.com/trcrdev/trcr-docs/issues/new/choose), collect:

```bash
trcrd version
cat /etc/os-release | head -2
sudo systemctl status trcrd-master --no-pager | head -15
sudo journalctl -u trcrd-master -n 80 --no-pager
sudo trcrd agents
sudo trcrd validate --config /etc/trcr/master.yaml
```

**Issues are public.** Before posting, remove:

- licence files and anything starting `TRCR-ENROLL-`
- passwords, tokens and webhook URLs
- real IP addresses, hostnames and email addresses you do not want published

Never post the contents of `/var/lib/trcr`. For anything about your account or
a security concern, email support@trcr.dev instead.
