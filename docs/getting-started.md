# Getting started

## What TRCR is

TRCR is one program, `trcrd`, that you install on your own hosts. The same
program runs in one of two roles.

| Role | What it does |
|---|---|
| **Master** | Holds the configuration and the licence, tells agents which probes to run, receives their results, writes the results to your database, and evaluates alert rules. It does not run probes itself. |
| **Agent** | Enrols with a master, runs the probes it is given, and sends the results back. |

A deployment is one master and one or more agents. Agents and the master talk
over mutually authenticated TLS, using certificates the master issues when an
agent enrols. You do not need to set up a certificate authority.

Results go to a store you choose: PostgreSQL, InfluxDB v2, Elasticsearch, a
Prometheus scrape endpoint, a file, or standard output. See
[Storing results](backends.md).

## The smallest useful setup

One Linux host running everything: the master, a local agent, PostgreSQL and
Grafana with the ready-made dashboards. The installer sets this up with one
command. See [Installation](install.md).

This is enough to monitor websites, DNS, certificates and hosts from one place.
Add agents on other hosts when you want to see the network from more than one
place.

## How many agents

Agents are free in every tier. The licence limits how many targets you
monitor, not how many agents you run. Deploy as many as your network needs.

| Agents | What you get |
|---|---|
| 1 | Probes from one place. No agent-to-agent data. |
| 2 | The minimum for agent-to-agent measurements. If one agent fails you lose half the picture. |
| 3 or more (recommended) | You can tell where a problem is. When one agent reports a target down and the other two reach it, the problem is near the first agent and not at the target. You also keep working when one agent fails. |
| 5 or more | Several sites, internet providers or regions. Above about 10 agents, consider filtering the mesh dashboards by region. |

As soon as two agents are enrolled, the master sets up a ping between every
pair of agents automatically. See [Agents](agents.md#agent-to-agent-probes).

## Where to put the master

Put the master close to the database it writes to, on a host that every agent
can reach. It coordinates and stores; it is not a vantage point. Put agents in
the places you want to measure from.

If an agent cannot be reached from the master (for example, it is behind NAT),
that is fine: that agent connects out to the master instead. See
[Agents](agents.md).

## Supported platforms

| Platform | Master | Agent |
|---|---|---|
| RHEL, CentOS Stream, Oracle Linux, Rocky, Alma 8 to 10 (amd64, arm64) | Yes | Yes |
| Fedora (amd64, arm64) | Yes | Yes |
| Debian 11, 12 and 13, Ubuntu (amd64, arm64) | Yes | Yes |
| Raspberry Pi OS 64-bit | Yes | Yes |
| Raspberry Pi OS 32-bit, including the Pi Zero and Pi 1 | Yes | Yes |
| macOS 12 or later (Intel and Apple silicon) | Foreground only, for evaluation | Yes, installed as a service |
| Windows (amd64) | Manual | Manual |

The all-in-one install, which adds PostgreSQL and Grafana, works on Linux only
and needs `apt`, `dnf` or `yum`.

On macOS there is no ready-made service for the master. Run it in the
foreground or under a launchd job of your own. Agents on macOS install as a
launchd service automatically.

On Windows a binary is available to download, but there is no installer and no
service setup.

## What you need before you install

- A Linux host for the master, with root access through `sudo`.
- `curl` and OpenSSL 1.1.1 or later. The installer uses OpenSSL to verify the
  download's signature and tells you which package to install if it is missing.
  On macOS the built-in LibreSSL is not enough; install OpenSSL with Homebrew.
- An email address for the free licence, or a licence file you already hold.
- Network access between the agents and the master on TCP ports 8443 and 8444.
  See [Security](security.md#ports).
- Outbound HTTPS from the master to `trcr.dev` and `api.trcr.dev`, unless you
  run without internet access. See [Security](security.md#running-without-internet-access).

Next: read the [checklist](checklist.md), then [install](install.md).
