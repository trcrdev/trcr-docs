# Frequently asked questions

## Installing

### Do I need a database before I start?

No. The all-in-one install sets up PostgreSQL and Grafana for you. If you
already run PostgreSQL, the installer can point TRCR at it with
`--postgres-dsn`. For InfluxDB v2 or Elasticsearch, install with no options and
add the store yourself. See [Install TRCR](install.md).

### Is it safe to run the installer again?

Yes. That's how you upgrade, on the master and on agents alike. It replaces
`trcrd`, restarts the TRCR services that were running if the version changed,
and leaves your configuration, license and data alone. When it's done, it says
`Upgrade complete`. If there was nothing to upgrade and everything is running,
it says `Nothing to do: trcrd v26.11.0 is installed and everything is running.`
within seconds. See [Operations](operations.md#upgrade-trcr).

### Why did the install finish with nothing running?

You asked for a free license by email, and the master can't start until you
click the link we sent. Click it, and the host finishes setting itself up
within about 15 seconds. See
[Click the link in your email](install.md#click-the-link-in-your-email).

### Can I see what the installer would do first?

Yes. Add `--dry-run` to any install command. It shows what would change on the
host, without changing anything.

### Can I install without piping a script into a shell?

Yes. Download the script, read it, then run it:

```bash
curl -fsSLO https://trcr.dev/install/install.sh
less install.sh
sh install.sh --all-in-one
```

Or download only the binary. See
[Install only the binary](install.md#install-only-the-binary).

### Does it work on a Raspberry Pi?

Yes, as a master or an agent, on both 32-bit and 64-bit Raspberry Pi OS,
including the Pi Zero.

### Does it run on macOS or Windows?

Partly. macOS is fully supported for agents, and a master runs there in the
foreground, which is fine for trying TRCR out. Windows has a binary to
download, but no installer or service setup. See
[Getting started](getting-started.md#supported-platforms).

### Can I run TRCR in Docker or Podman?

Yes. The image is `ghcr.io/trcrdev/trcrd`, for Linux on amd64 and arm64.
[Containers](containers.md) walks you through it with Docker Compose or Podman,
for a master, for agents, or both. You can mix the two: a master in a container
works with agents installed directly on other hosts, and the other way round.

### Does the master need a lot of resources?

No. It coordinates and forwards results, so size the host by your database,
which does the heavy work. For an all-in-one install, where PostgreSQL and
Grafana run on the same host, give it at least 2 GB of memory.

## Agents

### How many agents can I have?

That depends on your license. The free license allows five, and on an
all-in-one host the local agent is one of them. Agents you've revoked don't
count. See [Licensing](licensing.md).

### How many agents should I have?

Three or more, in different places, if you want to tell where a problem is. See
[Getting started](getting-started.md#how-many-agents).

### Does an agent need its own license, or an email address?

No. Only the master holds a license.

### My agent is behind NAT. Will it work?

Yes. Use a join command, where the agent connects out to the master. See
[Agents](agents.md#add-an-agent-with-a-join-command).

### Do I need an agent on the master's host?

Only if you want to measure from there. The master never runs probes itself.
The all-in-one install adds a local agent for that reason, and so does
`finish-setup.sh` on any master.

### Do agents need certificates from me?

No. The master issues them when an agent enrolls, and agents renew them by
themselves.

### What happens to results while the master is down?

Results from that period are lost. Agents carry on and start sending again
when the master returns.

### How do I rename an agent?

Run `sudo trcrd leave` on it. Then enroll it again with a join command made by
`sudo trcrd enroll-agent --node-id <new-name>` on the master. Old results keep
the old name.

## Configuration

### Where do I put my probes?

In files under `/etc/trcr/conf.d/`. One file per team, site or purpose works
well. Files whose names start with `_` are ignored. Copy files in with
`sudo install -o root -g trcr -m 0640` so the master can read them.

### Why does my edit have no effect?

The master reads its configuration only when it starts. Restart it with
`sudo systemctl restart trcrd-master`. If the file name starts with `_`, it's
being skipped.

### Why is TRCR so strict about configuration?

A misspelled setting that's silently ignored would leave you thinking
something is monitored when it isn't. TRCR refuses to start instead, and names
the file and the key.

### Can I monitor hosts on my private network?

Yes. Add `allow_private_targets: true` to those probes. See
[Probes](probes.md#private-and-internal-targets).

### Can I send results to two places?

Yes. List several stores under `backends:`, and every result goes to all of
them.

### How long is data kept?

In PostgreSQL, 12 months by default; change it with `retention_months`. In
InfluxDB and Elasticsearch, use their own retention settings. See
[Storing results](backends.md).

### Do I need another tool for bandwidth tests?

No. The `throughput` probe is built in and runs between two of your agents.

## License and privacy

### What does the free license include?

Five agents, every probe type, and up to 15 web, 20 reachability, 10
performance and 5 routing targets, for a year at a time with automatic
renewal. See [Licensing](licensing.md).

### What does TRCR send to trcr.dev?

An hourly check-in from the master, with the license and an identifier for the
host. Never your results, targets or configuration. See
[Security](security.md#what-trcr-sends-to-trcrdev).

### Does TRCR stop working if trcr.dev is unreachable?

No. A failed check-in is logged and retried, and monitoring carries on. Only
an expired or revoked license stops the master.

### Can I run it with no internet access at all?

Yes. See [Security](security.md#run-trcr-without-internet-access).

### I lost my verification email.

Run `sudo trcrd license resend`. Don't request a license again: a new request
cancels the first one.

## Dashboards

### Where are the dashboards?

At [github.com/trcrdev/trcr-dashboards](https://github.com/trcrdev/trcr-dashboards).
They're already loaded on an all-in-one install.

### Can I change them?

Yes, for your own TRCR deployment. Save your version under a new name so an
upgrade doesn't replace it.

### Can I use my existing Grafana?

Yes. Add a datasource with the right uid and import the files. See
[Dashboards](dashboards.md).

## Help

### Where do I report a problem?

For installation problems and mistakes in these pages,
[open an issue](https://github.com/trcrdev/trcr-docs/issues/new/choose). For
your account, your license or a security matter, email support@trcr.dev.
