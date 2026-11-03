# Operations

This page covers running TRCR day to day: the services, the commands you'll
use most, how to read the log, and how to back up, upgrade and uninstall.

## Services

| Service | Host | What it is |
|---|---|---|
| `trcrd-master` | Master | The master. |
| `trcrd-agent` | Every agent, including the local one on an all-in-one host | The agent. |
| `trcr-firstboot` | Master, only after an install with `--email` | Waits for your license, finishes the setup, then switches itself off. |

These are the systemd commands you'll use most:

```bash
sudo systemctl status trcrd-master
sudo systemctl restart trcrd-master
sudo journalctl -u trcrd-master -f        # follow the log
sudo journalctl -u trcrd-agent --since "1 hour ago"
```

On macOS, agents run under launchd.

## Everyday commands

These run on the master. They read saved state, so they work even when the
master is stopped, which is often exactly when you need them.

```bash
sudo trcrd agents                 # what's enrolled, and is it reporting?
sudo trcrd agents --stale         # only agents that aren't reporting; exit status 1 if any
sudo trcrd probes                 # what's configured, and where does it run?
sudo trcrd probes --agent web-01  # what does this one agent run?
```

On a healthy deployment, `trcrd agents` lists every agent as `up`, and
`trcrd agents --stale` prints `all N agent(s) reporting within 1m30s` and
exits with status 0.

`probes` shows the configuration the way the master uses it: fragments merged,
defaults applied, inventory expanded. Filter with `--type`, `--bundle`,
`--agent` and `--enabled`. `--source` adds the file each probe came from. Both
commands take `--json`.

The full list:

| Command | What it does |
|---|---|
| `trcrd version` | Print the installed version. |
| `trcrd validate` | Check a configuration without starting anything. |
| `trcrd run <type> <target>` | Run one probe now and print the result. |
| `trcrd init` | Create `/etc/trcr` and the starter files. Never overwrites your configuration. The installer runs it for you. |
| `trcrd license request`, `claim`, `resend`, `status` | See [Licensing](licensing.md). |
| `trcrd enroll-agent` | On the master: add an agent. See [Agents](agents.md). |
| `trcrd join`, `trcrd leave` | On an agent: enroll with a master, or undo that. |
| `trcrd agents`, `agents revoke`, `agents remove` | On the master: list and retire agents. |
| `trcrd probes` | On the master: list configured probes. |
| `trcrd encrypt-password` | Encrypt a password for use in a probe. See [Security](security.md#secrets-in-configuration). |
| `trcrd metrics` | Print TRCR's own metrics, for debugging. |
| `trcrd master`, `trcrd agent` | Run in the foreground. The services do this for you. |

Every command takes `--help`. A wrong command or a missing argument prints
usage and exits with status 2. A command that fails exits with status 1.

## Change the configuration

The master reads its configuration only when it starts, so every change
follows the same three steps:

1. Edit `/etc/trcr/master.yaml` or a file in `/etc/trcr/conf.d/`. To copy in a
   new file, use `sudo install -o root -g trcr -m 0640`, so the `trcr` user can
   read it.
2. Check it: `sudo trcrd validate --config /etc/trcr/master.yaml`
3. Apply it: `sudo systemctl restart trcrd-master`

`validate` lists every problem it finds, then ends with
`trcrd validate: N problem(s); the master would not run correctly` and exit
status 1. When there's nothing wrong, it prints `config OK: …`, and
`license OK: …` if a license file is installed. It adds
`Restart the master to apply changes: sudo systemctl restart trcrd-master`
only when a file changed after the running master started; on a fresh
install, or when the master already runs what's on disk, there's no such
line. See
[Configuration](configuration.md#check-before-you-restart) for what each line
means.

Agents fetch the new probes within a minute and apply them without restarting.

Keep `/etc/trcr` in version control if you can. Leave the license file and any
`.env` file out of it.

## What a healthy master log looks like

The master logs one JSON object per line. To read the most recent lines, run:

```bash
sudo journalctl -u trcrd-master -n 50
```

When the master starts, look for these messages, in roughly this order:

- `license loaded`
- `master ready`. Agents can connect from this moment.
- `backend ready`, once for each results store that opened. A store can take a
  few seconds to open after `master ready`. Results that arrive in the
  meantime are held and handed over, not lost.

After that, you'll see `agent enrolled` when an agent joins, and
`received probe results` as agents report in.

On a healthy master, nearly every line is at level `INFO`. A `WARN` or `ERROR`
line means something needs a look, and most of them say what to do. The ones
you're most likely to meet:

| Message | What it means |
|---|---|
| `every probe result will be DISCARDED` (ERROR) | No results store could be opened, so nothing is being saved. The lines just before it say why. See [Troubleshooting](troubleshooting.md#the-master-is-running-but-theres-no-data). |
| `backend validation failed; skipping` (ERROR) | One results store wasn't started. The `err` field says why. If its password variable isn't set, the `fix` field says where to put it. See [Troubleshooting](troubleshooting.md#a-results-stores-password-doesnt-reach-the-master). |
| `some backends were skipped` (WARN) | One of several results stores didn't open. The others are still saving. |
| `master.advertise_addr is not set` (WARN) | Agents on other hosts will enroll and then fail. See [Configuration](configuration.md#advertise_addr-is-required-for-remote-agents). |
| `tightened directory permissions (world bits removed)` (WARN) | The master found one of its folders readable by every user and fixed it. You'll see it once, including once after an upgrade from an older release; there's nothing to do. |
| `heartbeat send failed` (WARN) | The master couldn't check in with `api.trcr.dev`. Monitoring carries on, and the master keeps trying. |
| `heartbeat: the TRCR API is refusing this license` (ERROR) | Three check-ins in a row were refused. Monitoring carries on. `sudo trcrd license status` shows the latest outcome. See [Licensing](licensing.md#the-masters-log-says-the-trcr-api-is-refusing-the-license). |
| `license renewed via heartbeat; restart to apply` (INFO) | A renewed license is waiting. Restart the master when it suits you. |

For more detail, set `log.level: debug` in `master.yaml`, restart the master,
and set it back afterwards.

## Health checks

To let a load balancer or uptime monitor check the master, give it a plain
HTTP health address in `master.yaml`, then restart the master:

```yaml
master:
  health_listen_addr: 127.0.0.1:8080
```

The master then answers `ok` at `/healthz` on that address. It's off until you
set it. Keep it on 127.0.0.1 unless the load balancer is on another host.

## Metrics

With `metrics.enabled: true`, TRCR publishes metrics about itself in
Prometheus format, on `127.0.0.1:9101` by default. Use them to watch TRCR
itself; to watch your targets, use alert rules.

| Metric | Meaning |
|---|---|
| `trcr_probe_runs_total` | Probe runs, by type, name and status. |
| `trcr_probe_duration_seconds` | How long probes take. |
| `trcr_probe_errors_total` | Failed runs, by error class. |
| `trcr_results_received_total` | Results the master received, by agent. |
| `trcr_backend_writes_total` | Writes to each results store, by status. |
| `trcr_backend_drops_total` | Results dropped because a store couldn't keep up. |
| `trcr_alert_fires_total` | Alerts fired, by rule and severity. |
| `trcr_alert_sink_sends_total` | Alert deliveries, by output and status. |
| `trcr_heartbeat_consecutive_failures` | Failed check-ins with `api.trcr.dev` in a row. |
| `trcr_heartbeat_failures_total` | Failed check-ins, by cause. |
| `trcr_revocation_list_stale` | 1 when license status couldn't be refreshed for too long. |
| `trcr_enrolled_agents` | Number of enrolled agents. |

Worth alerting on: failed writes or drops in `trcr_backend_*`, a growing
`trcr_heartbeat_consecutive_failures`, and a fall in `trcr_enrolled_agents`.

`trcrd metrics` prints the same numbers on the command line.

To publish your probe results to Prometheus instead, see
[Storing results](backends.md#prometheus).

## Backups

On the master, back up:

| What | Why |
|---|---|
| `/etc/trcr/` | Your configuration and the license. |
| `/var/lib/trcr/` | Your deployment's certificate authority and saved state. Without it, every agent has to enroll again. |
| Your results store | The data. Use the database's own tools: `pg_dump` or continuous archiving for PostgreSQL, snapshots for Elasticsearch, backups for InfluxDB. |

Treat the backup of `/var/lib/trcr` as a secret, because it holds private
keys.

After restoring a PostgreSQL backup, start the master as normal. It recreates
anything that's missing for the current period.

Agents hold nothing that can't be recreated. If you lose one, enroll it again.

## Upgrade TRCR

To upgrade, run the install command again on each host. It replaces `trcrd`,
refreshes `/etc/trcr/examples/` and the sample probes, and restarts the TRCR
services that were running, so they run the new version. Your configuration,
license and data are left alone, and there's nothing to restart by hand.

On the **master**, run the plain command:

```bash
curl -fsSL https://trcr.dev/install/install.sh | sh
```

With no options, the installer keeps the way the master was set up. An
all-in-one host is upgraded as one, TRCR dashboards included, and stays
reachable the way it was (`--open-grafana` or not). A master on your own
PostgreSQL keeps using it, with the address and password it already has.
The options you installed with work too, for example:

```bash
curl -fsSL https://trcr.dev/install/install.sh | sh -s -- --all-in-one
```

You can leave out `--email`, `--company` and `--license`; once a license is
installed, the installer uses it.

The master is restarted first. Once it's listening again, the local agent is
restarted, and only then does the installer check that everything works. On an
all-in-one host you'll see something like this:

```
==> Upgrading trcrd from v26.10.0 to v26.11.0 ...
==> Installed /usr/local/bin/trcrd (trcrd v26.11.0)
==> Restarting trcrd-master so it runs the new version ...
==> Restarting trcrd-agent so it runs the new version ...
...
==> Refreshed the sample probes in conf.d/_samples.yaml.
...
==> Waiting for the first results (up to 90 seconds) ...
    Data is flowing: ping http dns tcp ssl_expiry traceroute alive
...
==> Upgrade complete: trcrd-master and trcrd-agent are running v26.11.0.
```

When you see `Upgrade complete`, you're done. `Data is flowing` counts only
results saved since the restarted master started, so it shows the new version
is writing. The sample probes line appears only when the samples changed.
Grafana is restarted only if its TRCR settings or dashboards changed, and the
line says which, for example
`Restarting Grafana so it loads the new settings (this can take a minute) ...`.
An upgrade doesn't
print a new join command; it says
`To add another host, run this here on the master and paste the command it prints on that host:`
and points at `sudo trcrd enroll-agent`.

If the master's service file came from an older release, the installer keeps
it and adds a drop-in with the two settings newer service files carry, right
after installing the new `trcrd` and before the restart:

```
==> Installed /usr/local/bin/trcrd (trcrd v26.11.0)
==> Kept your existing trcrd-master service file (/etc/systemd/system/trcrd-master.service).
==> Added /etc/systemd/system/trcrd-master.service.d/10-trcr.conf so the kept service file reads /etc/trcr/master.env.
==> Restarting trcrd-master so it runs the new version ...
```

You see the `Kept` and `Added` lines only on the run that adds the drop-in.

In a kept service file that still links to an old documentation address, the
installer points the `Documentation=` line at these docs. It changes nothing
else in the file and doesn't mention it on screen.

You may see `tightened directory permissions` once in the master's log after
that restart; see [What a healthy master log looks like](#what-a-healthy-master-log-looks-like).

On each **agent**, run the plain command, the one the installer printed after
the join (`To upgrade this agent later, run: ...`). The installer sees that
the host is an agent and upgrades it, without writing any master
configuration. Running the join command again only says the host is already
enrolled.

```bash
curl -fsSL https://trcr.dev/install/install.sh | sh
```

You'll see:

```
==> Upgrading trcrd from v26.10.0 to v26.11.0 ...
==> Installed /usr/local/bin/trcrd (trcrd v26.11.0)
==> Restarting trcrd-agent so it runs the new version ...
==> Upgrade complete: trcrd-agent is running v26.11.0.
    To check: sudo systemctl status trcrd-agent
```

If `trcrd` was already up to date, the installer says
`trcrd v26.11.0 is already installed and up to date.` and restarts nothing. On
an agent, it adds `This host is an agent (enrolled as <name>); nothing else to do here.`
On an all-in-one master, or one on your own PostgreSQL, where everything is
running, it checks the services and the master's log instead of running the
full setup, so there's no wait for results and the run takes seconds. That's
the same with the plain command and with the options you installed with. On
an all-in-one host you'll see:

```
==> trcrd v26.11.0 is already installed and up to date.
...
==> Nothing to do: trcrd v26.11.0 is installed and everything is running.

  What is on this host now:
    PostgreSQL   database trcr_results on this host only (127.0.0.1:5432); password in /etc/trcr/postgres.env
    Grafana      Only reachable from this host. From your own computer, run:
                   ssh -L 3000:127.0.0.1:3000 <this-host>
                 then open http://localhost:3000 and look in the TRCR folder.
                 Sign in as admin / <password>  (also in /etc/trcr/grafana-admin.env)
                 To reach it directly instead, run the installer again with --open-grafana.
    Probes       7 starter probes in /etc/trcr/conf.d/standalone.yaml; change them whenever you like

    To add another host:  sudo trcrd enroll-agent     # run here; paste the command it prints on that host
    Check on things:      sudo trcrd agents, sudo trcrd probes
```

The `Probes` line grows as agents join, because the master adds automatic
agent-to-agent pings between them. With other agents it reads like
`7 in /etc/trcr/conf.d/ + 6 automatic agent-to-agent; change the ones in conf.d/ whenever you like`.

Every run is logged in `/var/log/trcr-install.log`, including the checks that
`finish-setup.sh` makes on the master. Each run's part of the log ends with
`=== install.sh exit status N ===`, where 0 means the run finished without an
error.

After upgrading:

- Bring every host to the same release. Don't leave agents on an older one.
- Run `sudo trcrd validate --config /etc/trcr/master.yaml` on the master. A new
  version may be stricter about a setting.
- Compare your configuration with the refreshed examples in
  `/etc/trcr/examples/` to find new options.

## Uninstall TRCR

The uninstaller removes TRCR and keeps your data unless you ask otherwise:

```bash
curl -fsSL https://trcr.dev/install/uninstall.sh | sh                  # keep data
curl -fsSL https://trcr.dev/install/uninstall.sh | sh -s -- --dry-run  # show what would happen
curl -fsSL https://trcr.dev/install/uninstall.sh | sh -s -- --purge    # delete everything
```

It lists what it found on the host and asks before it changes anything. With
no terminal to ask on, such as in a script or an `ssh` command, it stops and
prints the command to run instead, with `--yes` added:

```
error: no terminal for confirmation; re-run with --yes:
         curl -fsSL https://trcr.dev/install/uninstall.sh | sh -s -- --yes
```

It stops and removes the TRCR services and the binary, including the
`/usr/bin/trcrd` link if the installer made one. By default, `/etc/trcr`,
`/var/lib/trcr` and the `trcr` user stay.

On a **master**, running the installer again with the options you installed
with brings the deployment back with the same identity and license. An
all-in-one host comes back the same way, local agent included.

On an **agent**, the uninstaller first tells the master the agent is leaving,
while the agent's certificate still works. It does this with or without
`--purge`:

```
==> Telling the master this agent is leaving ...
    master 192.0.2.10:8443 retired this agent (revoked)
```

That retires the agent's credentials. Without `--purge`,
`/etc/trcr/agent.yaml` is kept, but running the installer again on the host
says
`This host was an agent (web-02) and has left its master, so it needs a new enrollment.`
and exits with status 1. To make it an agent again, run
`sudo trcrd enroll-agent` on the master and paste the command it prints on
the host.

The uninstaller's summary says `Re-running install.sh restores this deployment.`
only where that's true: on a master or an all-in-one host, and on an agent
that keeps its identity. Uninstalling an agent that has already left its
master says instead:

```
  Config and state are KEPT (/etc/trcr, /var/lib/trcr).
  This agent has already left its master. To make this host an agent
  again, run sudo trcrd enroll-agent on the master and paste the command
  it prints here. Use --purge to delete them.
```

To keep the agent's identity instead, add `--skip-leave`. The master then
keeps the agent's record and shows it as down after about 90 seconds. Run
the plain install command on the host again, and the agent comes back as it
was:

```
==> This host is an agent (enrolled as web-02), but its service was removed. Putting it back ...
...
==> The agent is running again. Nothing else to do here.
```

With `--skip-leave --purge`, the master isn't told and the identity is
deleted, so the master keeps a record that nothing can bring back. The
uninstaller warns you and names the command to run on the master:

```
warning: with --skip-leave this host does not tell the master it is leaving, and --purge deletes its identity. On the master run: sudo trcrd agents remove web-02 --yes
```

If the master can't be reached during the leave step, nothing is retired and
the uninstall still finishes. It tells you to run
`sudo trcrd agents remove web-02 --yes` on the master. If `trcrd` was already
removed from the host, it can't tell the master at all, and says so:

```
warning: trcrd is not installed, so this host cannot tell the master it is leaving. On the master run: sudo trcrd agents remove web-02 --yes
```

On an all-in-one host, the uninstaller removes the TRCR dashboards and data
source from Grafana. It restarts Grafana for that, which can take a while:

```
    Restarting Grafana so it drops the TRCR data source (this can take a minute) ...
    removed /etc/grafana/provisioning/datasources/trcr.yaml
    removed the empty TRCR folder from Grafana
```

Once nothing is left in the TRCR folder, the folder goes too. If you saved a
dashboard of your own there, the folder and that dashboard stay. The
uninstaller leaves the PostgreSQL and Grafana packages, and your results
database, in place. Grafana keeps listening on 127.0.0.1 only, with sign-up
and anonymous access off, unless you installed with `--open-grafana`. At the
end, the uninstaller prints the two `psql` commands that delete the results
database and its user, in case you want them gone too. On a host without
`sudo`, they start with `runuser -u postgres --` instead of
`sudo -u postgres`.

On a master that uses your own PostgreSQL (`--postgres-dsn`), the uninstaller
leaves that database alone as well, with or without `--purge`. If the
database is on the same host, it prints the same two `psql` commands, with
your database and user names. If it's on another host, there's nothing to
run here, so it only names it:

```
==> The PostgreSQL results database was left untouched.
    Results remain in trcr_results on db.example.com:5432; drop it there if you no longer need it.
```

`--purge` also deletes `/etc/trcr`, `/var/lib/trcr`, the TRCR logs
(`/var/log/trcr` and `/var/log/trcr-install.log`) and the `trcr` user. On an
all-in-one host, Grafana's admin password still works, but the copies TRCR
kept are gone. The closing note says so and shows the command that sets a
new one:

```
    Its admin password is unchanged, but the copy TRCR kept went with /etc/trcr and the install log.
    If you no longer have it, set a new one (read from stdin, never on the command line):
```

Grafana's other TRCR settings stay, so it still listens only where it did
before.

> **Warning:** Before you purge a master, copy `/etc/trcr/license.lic`
> somewhere safe. `--purge` deletes `/var/lib/trcr`, which holds your
> deployment's certificate authority. It can't be undone: every agent's
> certificate stops working, and you'll have to enroll each agent again
> against a rebuilt master.

Other options: `--yes` skips the question, `--skip-leave` doesn't contact the
master, and `--keep-binary` leaves `trcrd` installed.

## Stop the master

When you stop it, the master finishes what it's doing, writes any results
still waiting, and sends any alerts still waiting. That can take up to half a
minute. Let `systemctl stop` finish rather than killing the process.

Next, make sure your deployment is locked down: [Security](security.md).
