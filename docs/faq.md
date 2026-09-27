# Frequently asked questions

## Installing

**Do I need a database before I start?**
No. The all-in-one install sets up PostgreSQL and Grafana for you. If you
already run PostgreSQL, InfluxDB v2 or Elasticsearch, use the plain install and
point TRCR at it. See [Installation](install.md).

**Is it safe to run the installer again?**
Yes. It is how you upgrade. It replaces the binary and never overwrites your
configuration, licence or data.

**Why did the install finish with nothing running?**
You asked for a free licence by email. The master cannot start without a
licence, and the installer does not wait for you. Click the link in the email
and the host finishes setting itself up within 15 seconds.

**Can I install without piping a script into a shell?**
Yes. Download the script, read it, then run it:
`curl -fsSLO https://trcr.dev/install/install.sh && less install.sh && sh install.sh --all-in-one`.
Or download only the binary. See
[Installation](install.md#installing-only-the-binary).

**Does it work on a Raspberry Pi?**
Yes, as a master or an agent, on both 32-bit and 64-bit Raspberry Pi OS,
including the Pi Zero.

**Does it run on macOS or Windows?**
macOS is fully supported for agents and suitable for trying out a master.
Windows has a binary but no installer or service setup. See
[Getting started](getting-started.md#supported-platforms).

**Can I run it in a container?**
The supported install is the service on a host. If you run the binary in a
container yourself, the agent needs permission to send ICMP (`NET_RAW`), and
`/etc/trcr` and `/var/lib/trcr` must be kept on persistent volumes.

**Does the master need a lot of resources?**
No. It coordinates and forwards results. Size the host by your database, which
does the heavy work. A small virtual machine runs an all-in-one install for a
small deployment.

### Can I run TRCR in Docker or Podman?

Yes. The image is `ghcr.io/trcrdev/trcrd`, for amd64 and arm64 Linux. A Compose
file and Podman quadlet units are in this repository; see
[Containers](containers.md). Agents run with the `NET_RAW` capability on the
host network so ping and traceroute measure the host's real path, and the
master's container hostname is pinned because the licence is bound to a
fingerprint derived from it.

## Agents

**How many agents can I have?**
The free tier allows 5. Agents are not charged for in any tier: licences limit
monitored targets, not agents.

**How many agents should I have?**
Three or more, in different places, if you want to tell where a problem is. See
[Getting started](getting-started.md#how-many-agents).

**Does an agent need its own licence, or an email address?**
No. Only the master holds a licence.

**My agent is behind NAT. Will it work?**
Yes. Use the token one-liner, where the agent connects out to the master. See
[Agents](agents.md#token-one-liner-the-agent-reaches-the-master).

**Do I need an agent on the master's host?**
Only if you want to measure from there. The master never runs probes. An
all-in-one install adds a local agent for that reason.

**Do agents need certificates from me?**
No. The master issues them at enrolment, and agents renew them by themselves.

**What happens to results while the master is down?**
Results from that period are not kept. Agents carry on and start sending again
when the master returns.

**How do I rename an agent?**
Run `sudo trcrd leave` on it, then enrol it again with `--node-id NEWNAME` on
`enroll-agent`. Old results keep the old name.

## Configuration

**Where do I put my probes?**
In files under `/etc/trcr/conf.d/`. One file per team, site or purpose works
well. Files starting with `_` are ignored.

**Why does my edit have no effect?**
Restart the master: `sudo systemctl restart trcrd-master`. There is no reload.
If the file name starts with `_`, it is being skipped.

**Why is TRCR so strict about configuration?**
A misspelt setting that is silently ignored leaves you thinking something is
monitored when it is not. TRCR refuses to start instead, and names the file and
the key.

**Can I monitor hosts on my private network?**
Yes. Add `allow_private_targets: true` to those probes. See
[Probes](probes.md#private-and-internal-targets).

**Can I send results to two places?**
Yes. List several stores under `backends:`. Every result goes to all of them.

**How long is data kept?**
In PostgreSQL, 12 months by default; change `retention_months`. In InfluxDB and
Elasticsearch, use their own retention settings. See
[Storing results](backends.md).

**Do I need another tool for bandwidth tests?**
No. The `throughput` probe is built in and runs between two of your agents.

## Licence and privacy

**What does the free licence include?**
5 agents, every probe type, and up to 15 web, 20 reachability, 10 performance
and 5 routing targets, for a year at a time with automatic renewal. See
[Licensing](licensing.md).

**What does TRCR send to trcr.dev?**
An hourly check-in from the master with the licence and an identifier for the
host. Never your results, targets or configuration. See
[Security](security.md#what-trcr-sends-to-trcrdev).

**Does TRCR stop working if trcr.dev is unreachable?**
No. A failed check-in is logged and retried. Only an expired or revoked licence
stops the master.

**Can I run it with no internet access at all?**
Yes. See [Security](security.md#running-without-internet-access).

**I lost my verification email.**
`sudo trcrd license resend`. Do not request again; that cancels the first
request.

## Dashboards

**Where are the dashboards?**
At [github.com/trcrdev/trcr-dashboards](https://github.com/trcrdev/trcr-dashboards),
and already loaded on an all-in-one install.

**Can I change them?**
Yes, for your own TRCR deployment. Save your version under a new name so an
upgrade does not replace it.

**Can I use my existing Grafana?**
Yes. Add a datasource with the right uid and import the files. See
[Dashboards](dashboards.md).

## Help

**Where do I report a problem?**
Installation problems and mistakes in these pages:
[open an issue](https://github.com/trcrdev/trcr-docs/issues/new/choose).
Account, licence or security matters: support@trcr.dev.
