# Getting started

TRCR measures your network from the places you choose: it pings hosts, fetches
web pages, looks up names, checks certificates and traces paths, on a schedule.
It runs on your own machines and keeps every result in your own database, so
your data never leaves your network. Grafana dashboards show what it finds.

## See it working first

Most people start by putting everything on one Linux host. It takes a few
minutes, and nothing you do there gets in the way of a larger setup later.

[Install it on one host now](install.md#install-everything-on-one-host), then
come back here when you're ready to plan a real deployment.

## How TRCR works

TRCR is a single program, `trcrd`, that runs on your own machines. Each copy
has one of two jobs:

- The **master** coordinates. It holds your configuration and your license,
  tells agents what to measure, saves what they send back to your results
  store and checks your alert rules. It doesn't run probes itself.
- **Agents** do the measuring. Put them wherever you want to see your network
  from: offices, data centers, cloud regions.

```
 agent ──┐
 agent ──┼── 8443, 8444 ──> master ──> results store ──> Grafana
 agent ──┘                     │       (PostgreSQL,
                               │        InfluxDB, ...)
                       license, config
```

Agents and the master talk over TLS, and each side proves who it is with a
certificate. The master issues those certificates when an agent enrolls, and
agents renew them by themselves, so you don't need to run a certificate
authority.

The license lives on the master. Agents don't need a license or an email
address of their own, but the master's license sets how many agents you can
enroll. The free license allows five.

Results go to a store you choose: PostgreSQL, InfluxDB v2, Elasticsearch, a
Prometheus scrape endpoint, a file, or standard output. See
[Storing results](backends.md).

## Plan a real deployment

### Where to put the master

Put the master close to the database it writes to, on a host every agent can
reach. It coordinates and stores, so it doesn't need to be a good place to
measure from.

If the master can't reach an agent, for example because the agent is behind
NAT, that's fine: the agent connects out to the master instead. See
[Agents](agents.md).

### How many agents

Each agent is one point of view. More points of view let you tell where a
problem is, not only that there is one.

| Agents | What you get |
|---|---|
| 1 | Measurements from one place. No agent-to-agent data. |
| 2 | The minimum for agent-to-agent measurements. If one agent fails, you lose half the picture. |
| 3 or more (recommended) | You can tell where a problem is. When one agent reports a target down and the other two reach it, the problem is near the first agent, not at the target. You also keep working when one agent fails. |
| 5 or more | Several sites, internet providers or regions. Above about 10 agents, consider filtering the mesh dashboards by region. |

The free license allows five agents. On an all-in-one host, the local agent is
one of them. Agents you've revoked don't count. If you need more, see
[Licensing](licensing.md#paid-tiers).

As soon as two agents are enrolled, the master sets up a ping between every
pair of agents by itself. See [Agents](agents.md#agent-to-agent-probes).

## Supported platforms

| Platform | Master | Agent |
|---|---|---|
| RHEL, CentOS Stream, Oracle Linux, Rocky, Alma 8 to 10 (amd64, arm64) | Yes | Yes |
| Fedora (amd64, arm64) | Yes | Yes |
| Debian 11, 12 and 13, Ubuntu (amd64, arm64) | Yes | Yes |
| Raspberry Pi OS 64-bit | Yes | Yes |
| Raspberry Pi OS 32-bit, including the Pi Zero and Pi 1 | Yes | Yes |
| macOS 12 or later (Intel and Apple silicon) | Foreground only, for trying it out | Yes, installed as a service |
| Windows (amd64) | Manual | Manual |

The all-in-one install, which adds PostgreSQL and Grafana, works on Linux only
and needs `apt`, `dnf` or `yum`.

On macOS, the master runs in the foreground only, which is fine for trying
TRCR out. For a permanent master, use Linux. Agents on macOS install as a
launchd service automatically.

On Windows, you can download the binary, but there's no installer and no
service setup.

To run TRCR in Docker or Podman instead, see [Containers](containers.md).

## What you need for a production install

- A Linux host for the master, with root access through `sudo`. If you're
  logged in as root on a host without `sudo`, leave `sudo` off the commands in
  these pages.
- `curl`, and OpenSSL 1.1.1 or later. The installer uses OpenSSL to check the
  download's signature, and tells you which package to install if it's
  missing. On macOS, the built-in LibreSSL isn't enough; install OpenSSL with
  Homebrew.
- An email address for the free license, or a license file you already have.
- TCP ports 8443 and 8444 open from every agent to the master. See
  [Security](security.md#ports).
- Outbound HTTPS from the master to `trcr.dev` and `api.trcr.dev`. The master
  checks in about once an hour, which is how a free license renews. If a
  check-in fails, the master logs a warning and keeps monitoring. To run with
  no internet access at all, see
  [Security](security.md#run-trcr-without-internet-access).

Before you rely on TRCR in production, go through the
[checklist](checklist.md). It covers the handful of mistakes that cause most
problems.

## Where to go next

- To measure from more places, add agents: [Agents](agents.md).
- To choose what to measure: [Probes](probes.md).
- To be told when something breaks: [Alerting](alerting.md).
- To keep results in a database you already run: [Storing results](backends.md).
