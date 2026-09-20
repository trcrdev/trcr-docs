# Operations

## Services

| Service | Host | What it is |
|---|---|---|
| `trcrd-master` | Master | The master. |
| `trcrd-agent` | Every agent, including the local one on an all-in-one host | The agent. |
| `trcr-firstboot` | Master, first install only | Waits for the licence, finishes the setup, then removes itself. |

```bash
sudo systemctl status trcrd-master
sudo systemctl restart trcrd-master
sudo journalctl -u trcrd-master -f        # follow the log
sudo journalctl -u trcrd-agent --since "1 hour ago"
```

On macOS, agents run under launchd.

## Everyday commands

These two run on the master. They read saved state, so they work even when the
master is stopped, which is often exactly when you need them.

```bash
sudo trcrd agents                 # what is enrolled, and is it reporting?
sudo trcrd agents --stale         # only agents that are NOT reporting; exit status 1 if any
sudo trcrd probes                 # what is configured, and where does it run?
sudo trcrd probes --agent web-01  # what does THIS agent actually run?
```

`probes` shows the configuration as the master really uses it: fragments
merged, defaults applied, inventory expanded. Filter with `--type`, `--bundle`,
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
| `trcrd join`, `trcrd leave` | On an agent: enrol with a master, or undo that. |
| `trcrd agents`, `agents revoke`, `agents remove` | On the master: list and retire agents. |
| `trcrd probes` | On the master: list configured probes. |
| `trcrd encrypt-password` | Encrypt a password for use in a probe. See [Security](security.md#secrets-in-configuration). |
| `trcrd metrics` | Print TRCR's own metrics, for debugging. |
| `trcrd master`, `trcrd agent` | Run in the foreground. The services do this for you. |

A wrong command or missing argument prints usage and exits with status 2. A
command that fails exits with status 1.

## Changing the configuration

1. Edit `/etc/trcr/master.yaml` or a file in `/etc/trcr/conf.d/`.
2. `sudo trcrd validate --config /etc/trcr/master.yaml`
3. `sudo systemctl restart trcrd-master`

There is no reload signal. Agents fetch the new probes within a minute and
apply them without restarting.

Keep `/etc/trcr` in version control if you can. Do not commit the licence file
or any `.env` file.

## Health checks

The master answers plain HTTP health checks on port 8080
(`master.health_listen_addr`). Point a load balancer or uptime monitor at it.

## Metrics

With `metrics.enabled: true`, TRCR publishes metrics about **itself** in
Prometheus format, on `127.0.0.1:9101` by default.

| Metric | Meaning |
|---|---|
| `trcr_probe_runs_total` | Probe runs, by type, name and status. |
| `trcr_probe_duration_seconds` | How long probes take. |
| `trcr_probe_errors_total` | Failed runs, by error class. |
| `trcr_results_received_total` | Results the master received, by agent. |
| `trcr_backend_writes_total` | Writes to each results store, by status. |
| `trcr_backend_drops_total` | Results dropped because a store could not keep up. |
| `trcr_alert_fires_total` | Alerts fired, by rule and severity. |
| `trcr_alert_sink_sends_total` | Alert deliveries, by output and status. |
| `trcr_heartbeat_consecutive_failures` | Failed check-ins with `api.trcr.dev` in a row. |
| `trcr_heartbeat_failures_total` | Failed check-ins, by cause. |
| `trcr_revocation_list_stale` | 1 when licence status could not be refreshed for too long. |
| `trcr_enrolled_agents` | Number of enrolled agents. |

Worth alerting on: failed writes or drops in `trcr_backend_*`, a growing
`trcr_heartbeat_consecutive_failures`, and a fall in `trcr_enrolled_agents`.

`trcrd metrics` prints the same numbers on the command line.

To publish your **probe results** to Prometheus instead, see
[Storing results](backends.md#prometheus).

## Backups

On the master, back up:

| What | Why |
|---|---|
| `/etc/trcr/` | Your configuration and the licence. |
| `/var/lib/trcr/` | The certificate authority for your deployment, and saved state. **Without it every agent must enrol again.** |
| Your results store | The data. Use the database's own tools: `pg_dump` or continuous archiving for PostgreSQL, snapshots for Elasticsearch, backups for InfluxDB. |

Treat the backup of `/var/lib/trcr` as a secret. It holds private keys.

After restoring a PostgreSQL backup, start the master as normal. It recreates
anything that is missing for the current period.

Agents hold nothing that cannot be recreated: a lost agent can simply be
enrolled again.

## Upgrading

Run the installer again, on the master and on each agent:

```bash
curl -fsSL https://trcr.dev/install/install.sh | sh
```

It replaces the binary, refreshes `/etc/trcr/examples/`, and **never touches
your configuration**. Then restart the service:

```bash
sudo systemctl restart trcrd-master     # or trcrd-agent
```

- Bring every host to the same release. Do not leave agents on an older one.
- After upgrading, run `sudo trcrd validate`. A new version may be stricter
  about a setting.
- Compare your configuration with the refreshed examples in
  `/etc/trcr/examples/` to see new options.
- Read the release notes in your trcr.dev portal before upgrading.

## Uninstalling

```bash
curl -fsSL https://trcr.dev/install/uninstall.sh | sh                  # keep data
curl -fsSL https://trcr.dev/install/uninstall.sh | sh -s -- --dry-run  # show what would happen
curl -fsSL https://trcr.dev/install/uninstall.sh | sh -s -- --purge    # delete everything
```

On an agent, it runs `trcrd leave` first, while the agent's certificate still
works, then stops and removes the service and the binary.

**Data is kept by default.** `/etc/trcr`, `/var/lib/trcr` and the `trcr`
account remain, so running the installer again brings the deployment back with
the same identity and licence.

**`--purge` on a master cannot be undone.** `/var/lib/trcr` holds the
certificate authority. Deleting it makes every agent's certificate worthless,
and the whole fleet must enrol again with a rebuilt master. Copy
`license.lic` somewhere safe first.

Other options: `--yes` (do not ask), `--skip-leave` (do not contact the
master), `--keep-binary`. If the master cannot be reached during the leave
step, the uninstall still completes and tells you to run
`trcrd agents remove <name>` on the master.

## Stopping

On stop, the master finishes what it is doing, writes any results still
waiting, and sends any alerts still waiting. This can take up to half a minute. Let
`systemctl stop` finish; do not kill the process.

Next: [Security](security.md).
