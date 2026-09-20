# Configuration

## Files

| Path | What it is |
|---|---|
| `/etc/trcr/master.yaml` | The master's configuration. |
| `/etc/trcr/agent.yaml` | An agent's configuration. Written for you when the agent enrols. |
| `/etc/trcr/conf.d/*.yaml` | Fragments: probes, inventory and alert rules. This is where most of your edits go. |
| `/etc/trcr/examples/` | Annotated reference copies of every example, matching the installed version. Refreshed on every install or upgrade. Read these; do not edit them. |
| `/etc/trcr/license.lic` | The licence. |
| `/var/lib/trcr/` | State: the deployment's certificate authority, agent certificates, saved state. Back this up on the master. |

## How the configuration is put together

1. The main file, `master.yaml` or `agent.yaml`. Use `--config` to point at
   another.
2. Every `conf.d/*.yaml` file next to it, in **alphabetical order**. Files
   whose names start with `_` are skipped, which is a handy way to switch a
   fragment off. Use `--conf-dir` for another folder.
3. Environment overrides, described below.

Reading is **strict**. An unknown or misspelt key anywhere stops the load and
names the file and the key. Nothing is silently ignored.

Alert outputs (where alerts are sent) can only be defined in the main file.
Alert rules, probes and inventory can live in fragments.

## Check before you restart

```bash
sudo trcrd validate --config /etc/trcr/master.yaml
```

It loads everything the way the service does and reports **every** problem at
once. It does not need the service to be stopped, and it skips checks that need
the real host, so you can run it on another machine or in a pipeline. Add
`--mode master` or `--mode agent` to insist on one.

**Changes to the master's configuration need a restart**:

```bash
sudo systemctl restart trcrd-master
```

There is no reload signal. Agents fetch probe changes from the master once a
minute and apply them without restarting.

## Overall shape

```yaml
mode: master                  # master or agent; required
node_id: trcr-master          # required; unique in your deployment
license:   { file_path: /etc/trcr/license.lic }
state:     { data_dir: /var/lib/trcr }
log:       { level: info, format: json, output: stdout }
master:    { ... }            # master only
agent:     { ... }            # agent only
heartbeat: { enabled: true }  # the master's check-in with api.trcr.dev
metrics:   { enabled: true, prometheus_listen_addr: 127.0.0.1:9101 }
acl:       { allowed_cidrs: [...], allowed_hostnames: [...], default_action: deny }   # deny or allow
backends:  [ ... ]            # where results are stored
inventory: [ ... ]            # reusable hosts and devices
probes:    [ ... ]            # usually in conf.d fragments
alerting:  { ... }            # rules and outputs
geoip:     { mmdb_path: ... } # optional location lookup for the map
```

`log.level` is `debug`, `info`, `warn` or `error`. `log.format` is `json` or
`text`. Logs go to standard output or standard error, which systemd collects
in the journal. Writing to a file is not supported; use the journal or a log
shipper.

## Master settings

```yaml
master:
  listen_addr: 0.0.0.0:8443          # agents connect here
  enroll_listen_addr: 0.0.0.0:8444   # enrolment
  health_listen_addr: 0.0.0.0:8080   # plain health check for load balancers
  advertise_addr: trcr-master.example.com:8444   # see below
  throughput_port: 5202              # port for bandwidth tests across the deployment
  agents:
    auto_mesh: true                  # ping between every pair of agents
    auto_mesh_interval: 60s
  assignment:                        # tuning for preferred_agents failover; all optional
    agent_down_after: 90s            # silence before an agent counts as down
    failback_hold_down: 5m           # how long an agent must be healthy before work moves back
    startup_grace: 2m                # no decisions straight after the master starts
```

### `advertise_addr` is required for remote agents

It looks like a label, but it matters. Agents check that the master's
certificate matches the address they connect to, and this setting is what puts
that address into the certificate. Without it, the certificate is valid only
for connections from the master's own host.

The failure this causes is misleading. Enrolment succeeds, so the agent
appears. Then every call after that fails. The agent's log reports a
certificate error saying the master's certificate is valid for `127.0.0.1` and
not for the address the agent used, the master's log reports a rejected
certificate, and `trcrd agents` shows the agent as `never-seen` for ever.

- Set it to a name or address your agents can reach, with the **enrolment**
  port (8444 by default).
- `trcrd init` fills it in from the host's outbound IP address. Check that
  value suits your network, especially behind NAT or a load balancer.
- **Restart the master after changing it**, because the certificate is made at
  startup.
- The master warns at startup when it is missing.

An all-in-one host whose only agent is local does not need it.

## Agent settings

Enrolment writes `agent.yaml` for you. The settings you may want to change:

```yaml
agent:
  master_addr: trcr-master.example.com:8443
  probe_concurrency: 16              # probes running at the same time; at most 256
  config_poll_interval: 1m           # how often to ask the master for changes
  result_batch_size: 100             # send results when this many are waiting
  result_batch_window: 5s            # or after this long
  throughput_server:
    enabled: true
    listen_addr: 0.0.0.0:5202        # other agents connect here for bandwidth tests
```

The bandwidth-test listener only accepts agents from your own deployment,
limits how many tests run at once, and refuses tests longer than 60 seconds.

Restart the agent after editing this file:

```bash
sudo systemctl restart trcrd-agent
```

## Environment overrides

Any setting can be overridden with an environment variable. Start with `TRCR_`,
and use a double underscore for each level:

```
TRCR_LOG__LEVEL=debug          →  log.level: debug
```

- Only variables whose first part is a real top-level key (`log`, `master`,
  `heartbeat` and so on) are treated as overrides. Other `TRCR_` variables,
  such as `TRCR_PG_PASSWORD`, are secrets read by name and are left alone.
- A misspelt setting under a real key (`TRCR_LOG__LEVL`) is an error.
- Each override is logged by **name only**. Values are never logged.
- A few security-sensitive settings cannot be overridden from the
  environment. Set those in the configuration file.

For a service, put these in a systemd drop-in:

```bash
sudo systemctl edit trcrd-master
```

```ini
[Service]
Environment=TRCR_LOG__LEVEL=debug
```

## Inventory

If many probes share the same hosts, define the hosts once under `inventory:`
and refer to them from probes with `inventory_ref` or `inventory_selector`.
This also keeps per-device SNMP credentials in one place.
`/etc/trcr/examples/` has annotated examples.

## Location data for the map

Add a `location:` to a probe to place its target on the Map dashboard. For
public addresses you can instead point `geoip.mmdb_path` at a MaxMind
GeoLite2 or GeoIP2 database file, and TRCR looks locations up. A probe's own
`location:` always wins.

Next: [Probes](probes.md).
