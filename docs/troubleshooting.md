# Troubleshooting

Most problems show up in one of four places. Start with these commands on the
master:

```bash
sudo systemctl status trcrd-master        # or trcrd-agent, on an agent
sudo journalctl -u trcrd-master -n 100    # the last 100 log lines
sudo trcrd agents
sudo trcrd validate --config /etc/trcr/master.yaml
```

If the problem happened during an install, read `/var/log/trcr-install.log`
first. It holds the full output of every installer run, including the package
manager's.

To tell a real problem from normal noise in the master's log, see
[What a healthy master log looks like](operations.md#what-a-healthy-master-log-looks-like).
For more detail in the log, set `log.level: debug` in `master.yaml`, restart
the master, and set it back afterwards.

## Installing

### The installer stops with a signature or OpenSSL error

The installer checks the download's signature before it installs anything, and
it needs OpenSSL 1.1.1 or later to do that. Check with `openssl version`. On an
older system, install a newer OpenSSL package; the installer names the one to
install. On macOS, the built-in LibreSSL doesn't work: run
`brew install openssl` and try again.

If OpenSSL is recent and the signature check still fails, nothing was
installed, and that's on purpose. Fetch the installer again and retry, from
another network if you can. If it keeps failing, stop and email
support@trcr.dev. Don't work around the check.

### `curl … | sh --all-in-one` ignores my options

Options need `sh -s --` in front of them. Without it, `sh` keeps the options
for itself and the installer never sees them:

```bash
curl -fsSL https://trcr.dev/install/install.sh | sh -s -- --all-in-one
```

### The install finished but nothing is running

That's expected if you installed with `--email`. The master can't start until
your license arrives, and it arrives when you click the link in the
verification email. Click it, and within about 15 seconds the host finishes
setting itself up. To follow along:

```bash
sudo journalctl -fu trcr-firstboot
```

To finish by hand instead, run:

```bash
sudo /etc/trcr/finish-setup.sh
```

If you skipped the email question, or installed a master with no options,
there's no license yet. The installer's last lines list the steps that are
left; [Install TRCR](install.md#a-master-with-a-database-you-already-run) has
them too.

### `sudo` says `trcrd: command not found`

On RHEL and its relatives, `sudo` doesn't look in `/usr/local/bin`, where
`trcrd` is installed. Current installers link `/usr/bin/trcrd` to it so
`sudo trcrd` works. If your host was installed by an older installer, run the
installer again, or use the full path, `/usr/local/bin/trcrd`.

If you're logged in as root on a host without `sudo`, leave `sudo` off the
commands.

### The all-in-one install says it can't install TimescaleDB

There's no TimescaleDB package for your PostgreSQL version. This is common with
the PostgreSQL 13 that Enterprise Linux 9 ships. The installer carries on with
standard partitioning, which works well, and there's nothing else to do.

### `--postgres-dsn` says it can't connect

When `psql` is installed on the master, the installer checks the database
connection before it carries on, and stops if it fails. It prints the error
`psql` gave. Check the host, port, database name, user and password, and that
your database server accepts connections from the master's address. The
password must be on the first line of the file you gave, and it can't contain
a quote mark or a backslash.

## The master

### The master won't start

The log says why. Run `sudo journalctl -u trcrd-master -n 50`. The usual
causes:

| The message mentions | Cause and fix |
|---|---|
| license missing, expired or invalid | See [Licensing](licensing.md#if-something-goes-wrong). Check the host's clock too. |
| `bundle_not_licensed` | A probe uses a type your license doesn't include. Remove it or upgrade your license. |
| `monitor_limit_exceeded` | More targets in a bundle than your license allows. The message lists every one over the limit. |
| an unknown key, with a file name | A misspelled or unsupported setting. Configuration is strict, so fix the key it names. |
| an unknown backend name | A probe's `backends:` names a results store that isn't defined in `master.yaml`. Remove the `backends:` line or fix the name. |
| `read fragment …: permission denied` | The `trcr` user can't read a file in `conf.d`, usually because it was copied with `cp`. `sudo trcrd validate` prints the exact fix. |
| key file permissions | A key file is readable by other users. Run `sudo chmod 600` on the file it names. |
| address already in use | Another program has port 8443 or 8444, or your health check port. Find it with `sudo ss -ltnp`. |

`sudo trcrd validate` finds most of these without starting anything, and lists
every problem at once.

### The master fails with `203/EXEC` on an SELinux host

SELinux stopped the service from running `trcrd`, because the file has the
wrong label. `finish-setup.sh` spots this and prints the fix. To fix the label
and try again, run:

```bash
sudo restorecon -Fv $(command -v trcrd)
sudo systemctl reset-failed trcrd-master
sudo /etc/trcr/finish-setup.sh
```

### The master is running but there's no data

A master can be running without saving anything. If it can't open your
results store, it starts anyway and logs that every result will be DISCARDED.
To check, search the log:

```bash
sudo journalctl -u trcrd-master | grep -iE "discard|backend"
```

On an all-in-one host, `finish-setup.sh` waits up to 90 seconds for the first
results. If none arrive, it says
`No results have reached the database after 90 seconds` and lists the commands
that usually show why.

Check these, in order:

1. Is there an agent? Run `sudo trcrd agents`. The master never runs probes
   itself, so it needs at least one agent that's `up`.
2. Are there probes? Run `sudo trcrd probes`. Remember that `_samples.yaml` is
   ignored until you copy it to a name without the underscore, and that the
   master only loads new probes when it restarts.
3. Did the database password reach the service? Run
   `sudo systemctl show trcrd-master -p EnvironmentFiles`. It should list your
   `.env` file, for example `/etc/trcr/postgres.env`.
4. Can the master reach the database? Try the same address, user and password
   with `psql` or `curl` from the master.
5. Is the results store still `stdout`? Then results are in the journal, not
   in a database. See [Storing results](backends.md).

### I changed the configuration and nothing happened

The master reads its configuration only when it starts. Restart it:

```bash
sudo systemctl restart trcrd-master
```

`trcrd probes` reads the files on disk, so it shows your change even before
the restart. That doesn't mean the master has loaded it.

### The log says the TRCR API is refusing the license

Your monitoring isn't affected. See
[Licensing](licensing.md#the-masters-log-says-the-trcr-api-is-refusing-the-license).

## Agents

### Enrolling an agent fails

The installer prints `This host could not enroll with the master.` A failed
attempt leaves nothing behind, so you can retry straight away:

1. Get a fresh command. Each token works once and expires after an hour. Run
   `sudo trcrd enroll-agent` on the master and paste the new command on the
   agent.
2. If the new command fails too, check the agent can reach the master's
   enrollment port. On the agent, run
   `nc -vz trcr-master.example.com 8444`.
3. If `nc` can't connect, open 8443 and 8444 on the master's firewall and in
   any cloud firewall or security group. Check that the address after `--join`
   is one the agent can reach. If it's a private address and the agent is
   elsewhere, fix `master.advertise_addr`.
4. If the master's log says `enroll: license agent limit reached`, your
   license allows no more agents. Revoke one you no longer need with
   `sudo trcrd agents revoke <name>`, or see [Licensing](licensing.md).

Nothing in the master's log hints at a firewall problem, because the master is
healthy and can't be reached.

### An agent is stuck at `never-seen`

The agent enrolled, then never made a successful call. `trcrd agents` prints
the usual causes under the table. Most likely first:

1. `master.advertise_addr` isn't set, or is wrong. The master's certificate is
   then valid only for connections from its own host, so every call after
   enrollment fails. The agent's log shows a certificate error saying the
   certificate is valid for `127.0.0.1` and not for the master's address.

   Set `advertise_addr` to an address the agents use, with the enrollment
   port, and restart the master. See
   [Configuration](configuration.md#advertise_addr-is-required-for-remote-agents).
   You don't need to enroll the agent again.
2. Port 8443 is blocked while 8444 is open. Enrollment uses 8444, and
   everything after that uses 8443.
3. The agent's service isn't running. On the agent, run
   `sudo systemctl status trcrd-agent`. If the service is missing, paste the
   join command again. On an enrolled host, it installs and starts the service
   without enrolling a second time.

### An agent shows `down`

Look on the agent:

```bash
sudo systemctl status trcrd-agent
sudo journalctl -u trcrd-agent -n 50
```

Look for connection errors (network or firewall), certificate errors (was the
master rebuilt, or the agent revoked?), or a full disk.

### `trcrd join` says the host is already enrolled

That's a local check, not a network problem. On a host that's already enrolled
with the same master, `trcrd join` keeps the existing identity, says
`already enrolled (/var/lib/trcr/agent); keeping that identity`, and only makes
sure the service is running.

To enroll the host with a different master, run `sudo trcrd leave` first. See
[Agents](agents.md#move-an-agent-to-another-master). If `join` refuses with
`config /etc/trcr/agent.yaml already exists; pass --force to overwrite`, an
earlier enrollment didn't finish. `--force` throws the old enrollment away;
use it only when that's what you want.

### The pairing code is rejected

- The code and fingerprint belong together. To print both again, run
  `sudo trcrd join --pending --show-code` on the agent.
- After several wrong codes, the agent stops accepting attempts for a short
  while. Wait a minute, then try again.
- If the agent was installed with `--accept-from`, the master must connect
  from one of those addresses.
- Check port 8445 is open on the agent.

### I rebuilt the master and no agent connects

A new master has a new certificate authority, so it doesn't recognize the old
agents' certificates. Run `sudo trcrd enroll-agent` on the new master and paste
its join command on each agent. Each agent sees the different `--ca-hash` and
enrolls again.

To avoid this next time, back up `/var/lib/trcr` and restore it onto the new
master. See [Operations](operations.md#backups).

## Probes

### A probe fails with `private_target_refused`

The target resolves to a private or special address, which probes refuse by
default. Add `allow_private_targets: true` to that probe. See
[Probes](probes.md#private-and-internal-targets).

### Ping works from the shell but the probe fails

- Test the way the agent does. On the agent host, run
  `trcrd run ping <target>`.
- The target or a firewall may limit ICMP. Try a lower `count` or a longer
  `interval`.
- In a container, the agent needs permission to send ICMP (`NET_RAW`). See
  [Containers](containers.md).

### Traceroute shows stars or stops early

Routers often don't answer traceroute packets, and firewalls drop them. A path
that ends in stars while `ping` and `http` to the same target succeed is
normal. The path-change alert can compare the networks crossed instead, with
`path_level: as`, which copes better with silent hops.

### An HTTP probe fails but the site works in my browser

On the agent, run `trcrd run http <url>` and read the result.

- `unexpected_status`: the site returns a redirect or another code. Add it to
  `expected_status`, or probe the final URL.
- A certificate error: the agent's host doesn't trust the certificate's
  issuer. For a private certificate authority, check the system's trusted
  certificates.
- A timeout from one agent only: that's a finding, not a fault. The site is
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
- The passphrase variables must start with `TRCR_SNMP_`, and they must be set
  on the agent that runs the probe, in that agent's service environment.
- Devices usually have private addresses, so add `allow_private_targets: true`.
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

- Widen the time range, and check the filters at the top aren't excluding
  everything.
- Some dashboards fill later than others, or need a second agent. See
  [Dashboards](dashboards.md#what-you-should-see-in-the-first-hour).
- No probe of that type may be running. Check with
  `sudo trcrd probes --type <type>`.
- You may be using the wrong edition. The PostgreSQL dashboards don't work
  against InfluxDB, and the other way round.

### I can't open Grafana

On an all-in-one host, Grafana listens on 127.0.0.1 only. Use an SSH tunnel
(`ssh -L 3000:127.0.0.1:3000 <host>`), or run the installer again with
`--open-grafana`. The admin password is in `/etc/trcr/grafana-admin.env`, and
`sudo /etc/trcr/finish-setup.sh` shows it again.

## License

See [Licensing](licensing.md#if-something-goes-wrong).

## Ask for help

Before you [open an issue](https://github.com/trcrdev/trcr-docs/issues/new/choose),
collect this from the master:

```bash
trcrd version
cat /etc/os-release | head -2
sudo systemctl status trcrd-master --no-pager | head -15
sudo journalctl -u trcrd-master -n 80 --no-pager
sudo trcrd agents
sudo trcrd validate --config /etc/trcr/master.yaml
```

For an install problem, add the end of `/var/log/trcr-install.log`.

Issues are public. Before you post, remove:

- license files and anything starting `TRCR-ENROLL-`
- passwords, tokens and webhook URLs
- real IP addresses, hostnames and email addresses you don't want published

Never post the contents of `/var/lib/trcr`. For anything about your account,
or a security concern, email support@trcr.dev instead.
