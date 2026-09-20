# TRCR documentation

[TRCR](https://trcr.dev) is network monitoring software you install on your own
hosts. It measures reachability, latency, DNS, TLS certificates, routing,
throughput and device health from several places at once, and stores the
results in a database you control.

These pages cover installing, configuring and running TRCR. They apply to
**TRCR v26.09.03**.

## Start here

| If you want to | Read |
|---|---|
| Understand the parts and plan a deployment | [Getting started](docs/getting-started.md) |
| Avoid the usual mistakes | [Checklist for a successful installation](docs/checklist.md) |
| Install TRCR | [Installation](docs/install.md) |
| Get or renew a licence | [Licensing](docs/licensing.md) |
| Add, move or retire agents | [Agents](docs/agents.md) |

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
| Day-to-day commands, upgrades, backups, uninstalling | [Operations](docs/operations.md) |
| Ports, certificates, secrets and running without internet access | [Security](docs/security.md) |
| Something is not working | [Troubleshooting](docs/troubleshooting.md) |
| Short answers to common questions | [FAQ](docs/faq.md) |

## Getting help

- Check [Troubleshooting](docs/troubleshooting.md) and the [FAQ](docs/faq.md)
  first. Most installation problems are one of a handful of causes.
- For an installation problem or a mistake in these pages,
  [open an issue](https://github.com/trcrdev/trcr-docs/issues/new/choose). Remove licence files, tokens,
  passwords and real IP addresses before you post: issues are public.
- For anything about your account, your licence or a security concern, email
  support@trcr.dev instead.

The ready-made Grafana dashboards are in
[trcr-dashboards](https://github.com/trcrdev/trcr-dashboards).

## Licence

Copyright © 2026 TRCR Networks. You may read and copy this documentation to
install and operate TRCR. See [LICENSE](LICENSE).
