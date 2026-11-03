# Configuration

TRCR is configured with YAML files on the master. Most of what you'll change
is probes, which live in small files of their own; the main file holds the
settings you set once.

## Where the files are

| Path | What it is |
|---|---|
| `/etc/trcr/master.yaml` | The master's configuration. |
| `/etc/trcr/agent.yaml` | An agent's configuration. Written for you when the agent enrolls. |
| `/etc/trcr/conf.d/*.yaml` | Fragments: probes, inventory and alert rules. Most of your edits go here. |
| `/etc/trcr/examples/` | Annotated reference copies of every example, matching the installed version. Refreshed on every install or upgrade, so read them but don't edit them. |
| `/etc/trcr/license.lic` | The license. |
| `/etc/trcr/master.env` | Secrets for the master, as `NAME=value` lines: the variables your `*_env` settings name. The master's service reads it. Root and the `trcr` group only. |
| `/etc/trcr/postgres.env` | The database password, on an all-in-one or `--postgres-dsn` install. Written by the installer. |
| `/var/lib/trcr/` | State: your deployment's certificate authority, agent certificates and saved state. Back this up on the master. |

## How the configuration is put together

The master reads its configuration in this order:

1. The main file, `master.yaml` or `agent.yaml`. Use `--config` to point at
   another.
2. Every `conf.d/*.yaml` file next to it, in alphabetical order. Files whose
   names start with `_` are skipped, so renaming a fragment to start with `_`
   switches it off. Use `--conf-dir` for another folder.
3. Environment overrides, described below.

Reading is strict. An unknown or misspelled key anywhere stops the load, and
the error names the file and the key. That's on purpose: a setting that's
silently ignored would leave you thinking something is monitored when it
isn't.

Alert outputs (where alerts are sent) can only be defined in the main file.
Alert rules, probes and inventory can live in fragments.

The master runs as the `trcr` user, so every file it reads must be readable by
the `trcr` group. To copy a file into `/etc/trcr` with the right owner and
mode, use `install` rather than `cp`:

```bash
sudo install -o root -g trcr -m 0640 my-probes.yaml /etc/trcr/conf.d/my-probes.yaml
```

## Check before you restart

To check your changes without touching the running master, run:

```bash
sudo trcrd validate --config /etc/trcr/master.yaml
```

It loads everything the way the service does, then checks the things that
would stop the master on this host. It doesn't need the service to be stopped.
Add `--mode master` or `--mode agent` to insist on one.

When everything is fine, you'll see something like this:

```
config OK: mode=master node_id=web-01 probes=7 backends=1 inventory=0 alerting_rules=0 fragments=2
license OK: id=… tier=free expires=…
  bundle performance   0/10 monitors configured
  bundle reachability  4/20 monitors configured
  bundle routing       0/5 monitors configured
  bundle web           3/15 monitors configured
  agent_limit: 5
Restart the master to apply changes: sudo systemctl restart trcrd-master
```

- `license OK` means the installed license is valid and your probes fit its
  bundles and target limits. Without a license file yet, you'll see
  `note: license entitlements not checked` instead. To check against a license
  file you haven't installed, add `--license <file>`.
- The `Restart the master` line appears only when a configuration file or the
  license changed after the running master started. If it's missing, the
  running master already has what you checked, or the master isn't running.

When something is wrong, `validate` lists every problem together, ends with a
count, and exits with status 1. It doesn't print `config OK`. Configuration
errors start with `error:` and name the file. Problems with the host start with
`warning:` and say how to fix them. For example:

```
warning: /etc/trcr/conf.d/probes.yaml is owned by root:root with mode 0640, which the trcr service user cannot read
  fix: sudo chgrp trcr /etc/trcr/conf.d/probes.yaml && sudo chmod 0640 /etc/trcr/conf.d/probes.yaml
warning: backend "postgres-main" reads its password from $TRCR_PG_PASSWORD, but no EnvironmentFile of trcrd-master sets it; put TRCR_PG_PASSWORD=... in /etc/trcr/master.env (mode 0640, group trcr)
trcrd validate: 2 problem(s); the master would not run correctly
```

The host checks are:

- Run as root, that the `trcr` user can read `master.yaml`, every file in
  `conf.d` and the license file.
- That every variable a `*_env` setting names is set by one of the master
  service's `EnvironmentFile`s, and that the files it requires exist. See
  [Storing results](backends.md#passwords-and-tokens).

On another machine or in a pipeline, there's no master service to look at, so
`validate` checks the variables in its own environment instead. Export them
there, or expect a warning for each one.

## Apply a change

The master reads its configuration only when it starts. There's no reload
signal, so restart it after every change:

```bash
sudo systemctl restart trcrd-master
```

Agents fetch probe changes from the master once a minute and apply them
without restarting. A new probe runs within a few seconds of an agent
receiving it.

## Overall shape

Here's every top-level section of `master.yaml` at a glance, so you know where
a setting belongs:

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
`text`. Logs go to standard output or standard error, and systemd collects them
in the journal. TRCR can't write its log to a file; use the journal or a log
shipper.

## Master settings

```yaml
master:
  listen_addr: 0.0.0.0:8443          # agents connect here
  enroll_listen_addr: 0.0.0.0:8444   # enrollment
  health_listen_addr: 0.0.0.0:8080   # optional plain /healthz for load balancers; off unless set
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

The failure this causes is misleading. Enrollment succeeds, so the agent
appears. Then every call after that fails. The agent's log reports a
certificate error saying the master's certificate is valid for `127.0.0.1` and
not for the address the agent used. The master's log reports a rejected
certificate, and `trcrd agents` shows the agent as `never-seen` for ever.

- Set it to a name or address your agents can reach, with the enrollment port
  (8444 by default).
- The installer fills it in from the host's outbound IP address. Check that
  value suits your network. On a cloud host behind NAT or a load balancer,
  it's usually the private address, which agents elsewhere can't reach.
- Restart the master after changing it, because the certificate is made when
  the master starts.
- The master logs a warning at startup when it's missing.

An all-in-one host whose only agent is the local one doesn't need it.

## Agent settings

Enrollment writes `agent.yaml` for you. These are the settings you may want to
change:

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

Environment variables let you change a setting for one service without
editing its file, for example to turn on debug logging for a while. Start the
name with `TRCR_`, and use a double underscore for each level:

```
TRCR_LOG__LEVEL=debug          →  log.level: debug
```

- Only variables whose first part is a real top-level key (`log`, `master`,
  `heartbeat` and so on) count as overrides. Other `TRCR_` variables, such as
  `TRCR_PG_PASSWORD`, are secrets read by name and are left alone.
- A misspelled setting under a real key, such as `TRCR_LOG__LEVL`, is an error.
- Each override is logged by name only. Values are never logged.
- A few security-sensitive settings can't be overridden from the environment.
  Set those in the configuration file.

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
This also keeps per-device SNMP credentials in one place. You'll find
annotated examples in `/etc/trcr/examples/`.

## Location data for the map

To place a probe's target on the Map dashboard, add a `location:` to the
probe. For public addresses, you can instead point `geoip.mmdb_path` at a
MaxMind GeoLite2 or GeoIP2 database file, and TRCR looks locations up. A
probe's own `location:` always wins.

Next, tell TRCR what to measure: [Probes](probes.md).
