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
- `backend ready`, once for each results store that opened
- `master ready`

After that, you'll see `agent enrolled` when an agent joins, and
`received probe results` as agents report in.

Most lines are at level `INFO`. Lines at `WARN` or `ERROR` are worth reading.
The ones you're most likely to meet:

| Message | What it means |
|---|---|
| `every probe result will be DISCARDED` (ERROR) | No results store could be opened, so nothing is being saved. The lines just before it say why. See [Troubleshooting](troubleshooting.md#the-master-is-running-but-theres-no-data). |
| `some backends were skipped` (WARN) | One of several results stores didn't open. The others are still saving. |
| `master.advertise_addr is not set` (WARN) | Agents on other hosts will enroll and then fail. See [Configuration](configuration.md#advertise_addr-is-required-for-remote-agents). |
| `tightened directory permissions (world bits removed)` (WARN) | The master found one of its folders readable by every user and fixed it. You'll see it once; there's nothing to do. |
| `heartbeat send failed` (WARN) | The master couldn't check in with `api.trcr.dev`. Monitoring carries on, and the master keeps trying. |
| `heartbeat: the TRCR API is refusing this license` (ERROR) | See [Licensing](licensing.md#the-masters-log-says-the-trcr-api-is-refusing-the-license). Monitoring carries on. |
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

To upgrade, run the installer again. It replaces `trcrd`, refreshes
`/etc/trcr/examples/`, and leaves your configuration, license and data alone.
If the version changed, it restarts the TRCR services that were running, so
they run the new version.

On the **master**, run:

```bash
curl -fsSL https://trcr.dev/install/install.sh | sh
```

On an all-in-one host, add `--all-in-one`. That also brings the TRCR
dashboards up to date:

```bash
curl -fsSL https://trcr.dev/install/install.sh | sh -s -- --all-in-one
```

On each **agent**, upgrade the binary only:

```bash
curl -fsSL https://trcr.dev/install/install.sh | TRCR_SKIP_SETUP=1 sh
```

For each service it restarts, the installer prints
`Restarting trcrd-master so it runs the new version ...` (or `trcrd-agent`).
On an agent, it ends with a line like
`Upgrade complete: trcrd-agent is running v26.11.0.` If `trcrd` was already up
to date, it says `trcrd v26.11.0 is already installed and up to date.` and
restarts nothing.

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

On an agent, it runs `trcrd leave` first, while the agent's certificate still
works. Then it stops and removes the service and the binary, including the
`/usr/bin/trcrd` link if the installer made one.

By default, `/etc/trcr`, `/var/lib/trcr` and the `trcr` user stay. Running the
installer again brings the deployment back with the same identity and license.

On an all-in-one host, the uninstaller removes the TRCR dashboards and
datasource from Grafana. It leaves the PostgreSQL and Grafana packages, and
your results database, in place.

> **Warning:** Before you purge a master, copy `/etc/trcr/license.lic`
> somewhere safe. `--purge` deletes `/var/lib/trcr`, which holds your
> deployment's certificate authority. It can't be undone: every agent's
> certificate stops working, and you'll have to enroll each agent again
> against a rebuilt master.

Other options: `--yes` skips the questions, `--skip-leave` doesn't contact the
master, and `--keep-binary` leaves `trcrd` installed. If the master can't be
reached during the leave step, the uninstall still finishes and tells you to
run `sudo trcrd agents remove <name>` on the master.

## Stop the master

When you stop it, the master finishes what it's doing, writes any results
still waiting, and sends any alerts still waiting. That can take up to half a
minute. Let `systemctl stop` finish rather than killing the process.

Next, make sure your deployment is locked down: [Security](security.md).
