# TRCR documentation

[TRCR](https://trcr.dev) is self-hosted network monitoring from TRCR Networks,
for network and systems engineers who want to see their network from the
places that matter and keep the results on their own systems. A master and a
full mesh of agents run 14 probe types: ping, batch ping, TCP, traceroute,
liveness sweep, NTP, path MTU, HTTP/HTTPS, SSL expiry, DNS, DNS propagation,
native throughput, SNMP and BGP. Results go to your own PostgreSQL, InfluxDB,
Elasticsearch or Prometheus and never leave your infrastructure. The only
thing trcr.dev receives is the master's hourly license check-in, which you can
turn off.

These pages cover installing, configuring and running TRCR. They apply to
TRCR v26.11.0.

## Start here

| If you want to | Read |
|---|---|
| Try TRCR on one host in a few minutes | [Install TRCR](docs/install.md) |
| Understand the parts and plan a deployment | [Getting started](docs/getting-started.md) |
| Run it in Docker or Podman | [Containers](docs/containers.md) |
| Add, move or retire agents | [Agents](docs/agents.md) |
| Get or renew a license | [Licensing](docs/licensing.md) |
| Check you're ready before relying on it | [Before you go to production](docs/checklist.md) |

## Configure

| Topic | Read |
|---|---|
| Config files, fragments and environment overrides | [Configuration](docs/configuration.md) |
| The 14 probe types and how to write one | [Probes](docs/probes.md) |
| Where results are stored | [Storing results](docs/backends.md) |
| Alert rules and where alerts go | [Alerting](docs/alerting.md) |
| Grafana dashboards | [Dashboards](docs/dashboards.md) |

## Run

| Topic | Read |
|---|---|
| Day-to-day commands, the log, upgrades, backups, uninstalling | [Operations](docs/operations.md) |
| Ports, certificates, secrets and running without internet access | [Security](docs/security.md) |
| Something isn't working | [Troubleshooting](docs/troubleshooting.md) |
| Short answers to common questions | [FAQ](docs/faq.md) |

## Getting help

- Check [Troubleshooting](docs/troubleshooting.md) and the [FAQ](docs/faq.md)
  first. Most installation problems come down to a handful of causes.
- For an installation problem or a mistake in these pages,
  [open an issue](https://github.com/trcrdev/trcr-docs/issues/new/choose).
  Issues are public, so remove license files, tokens, passwords and real IP
  addresses before you post.
- For anything about your account, your license or a security concern, email
  support@trcr.dev instead.

The ready-made Grafana dashboards are in
[trcr-dashboards](https://github.com/trcrdev/trcr-dashboards).

## Not to be confused with

TRCR (trcr.dev) is network monitoring software. It isn't the TRCR carbon-credit
token, the `traceroute` command or the trcr.pro time-tracking app.

## License

Copyright © 2026 TRCR Networks. You may read and copy this documentation to
install and operate TRCR. See [LICENSE](LICENSE).
