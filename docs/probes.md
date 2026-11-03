# Probes

A probe is one check that runs on a schedule: ping this host, fetch this URL,
look up this name. You define probes on the master, usually in
`/etc/trcr/conf.d/*.yaml`, and the master hands them to agents.

Annotated examples for every probe type are installed on your master under
`/etc/trcr/examples/conf.d/`. They match your installed version exactly, so use
them as the reference for each type's options.

## Write your first probes

The quickest start is the sample file the installer wrote. Copy it to an
active name, so the master reads it, and edit the targets:

```bash
sudo install -o root -g trcr -m 0640 /etc/trcr/conf.d/_samples.yaml /etc/trcr/conf.d/probes.yaml
sudoedit /etc/trcr/conf.d/probes.yaml
```

Or write your own file. Here's a small one with the most common types:

```yaml
# /etc/trcr/conf.d/probes.yaml
description: Our first probes

# Defaults apply to every probe in this file. A probe's own value wins.
defaults:
  interval: 1m

probes:
  - name: gateway-ping
    type: ping
    target: 192.0.2.1
    interval: 30s

  - name: website
    type: http
    url: https://example.com
    timeout: 10s
    expected_status: [200]

  - name: website-dns
    type: dns
    target: example.com
    record_type: A

  - name: website-cert
    type: ssl_expiry
    target: example.com:443
    interval: 24h

  - name: ssh-port
    type: tcp
    target: 192.0.2.1:22

  - name: path-to-gateway
    type: traceroute
    target: 192.0.2.1
    interval: 5m
```

To check the file and load it, run these on the master:

```bash
sudo trcrd validate --config /etc/trcr/master.yaml
sudo systemctl restart trcrd-master
sudo trcrd probes
```

The master reads probes only when it starts, which is why the restart is
needed. `trcrd probes` then lists every probe and where it runs:

```
NAME             TYPE        TARGET               INTERVAL  BUNDLE        RUNS ON     BACKENDS
gateway-ping     ping        192.0.2.1            30s       reachability  all agents  -
path-to-gateway  traceroute  192.0.2.1            5m        reachability  all agents  -
ssh-port         tcp         192.0.2.1:22         1m        reachability  all agents  -
website          http        https://example.com  1m        web           all agents  -
website-cert     ssl_expiry  example.com:443      24h       web           all agents  -
website-dns      dns         example.com          1m        web           all agents  -

6 probe(s) — reachability 3, web 3
```

`trcrd probes` reads the files on disk, so it shows a new probe even before
you've restarted the master. Agents pick up the change within a minute of the
restart, and the first results arrive a few seconds after that.

The targets above are documentation addresses. Replace them with your own
gateway, site and hosts. If they're on a private network, see
[Private and internal targets](#private-and-internal-targets).

## Settings every probe has

```yaml
- name: example-com            # unique
  type: http                   # one of the 14 types below
  interval: 1m                 # how often
  timeout: 10s
  enabled: true
  backends: [postgres-main]    # optional; see below
  agents: [agent-1, agent-2]   # see "Where a probe runs"
  labels: { site: london }     # appear on every result; use them to filter dashboards
  location: { lat: 51.5, lon: -0.12, city: London }   # for the Map dashboard
  if_overrunning: drop         # drop or queue, when the previous run has not finished
  allow_private_targets: false # see "Private and internal targets"
```

Label names use lowercase letters, digits, `_`, `.` and `-`, up to 64
characters. A probe can have up to 32 labels, with values up to 256 bytes.

Results always go to every results store in `master.yaml`, so you can leave
`backends:` out. If you do list stores, the master checks that each one
exists, and an unknown name stops it from starting.

## Where a probe runs

By default every agent runs every probe. To choose, give the probe one of
these settings:

| Setting | What happens |
|---|---|
| Neither | Every agent runs it. |
| `agents: [a, b]` | Every agent listed runs it. |
| `preferred_agents: [a, b, c]` | Exactly one agent runs it at a time. If that agent goes down or stalls, the master moves the probe to the next in the list, and back again once the first has been healthy for a while. |

You can't use `agents` and `preferred_agents` together. Use
`preferred_agents` for checks where duplicates would be wasteful, such as
bandwidth tests or checks against a rate-limited service.

`sudo trcrd probes` shows where each probe runs right now, including the live
placement of `preferred_agents` probes. `sudo trcrd probes --agent NAME`
answers "what does this agent actually run?"

Agents spread their runs out, so several agents with the same probe don't all
hit a target at the same moment.

## The probe types

### Web bundle

| Type | What it measures |
|---|---|
| `http` | An HTTP or HTTPS request with a timing breakdown: DNS, connect, TLS, time to first byte, transfer and total. Records the status code, size, redirects and final URL. Supports method, headers, body, basic authentication, an API key, a list of acceptable status codes and response checks. Reads at most 8 MiB of a response. |
| `ssl_expiry` | Days until a TLS certificate expires, plus details of the chain. It reports on broken and expired certificates too, rather than only failing. Use `ca_bundle` for a private certificate authority and `sni` to ask for a particular name. |
| `dns` | A lookup through the system resolver (A, AAAA, CNAME, MX, TXT, NS) or through the `resolvers:` you list (which adds SOA, PTR and SRV). `expected_value` checks the answer. |

### Reachability bundle

| Type | What it measures |
|---|---|
| `ping` | ICMP echo: minimum, average and maximum round-trip time, variation, and packet loss. `count` and `packet_size` are optional (4 packets of 56 bytes by default). |
| `batch_ping` | Pings many `targets:` from one probe entry, with per-target results and totals. |
| `tcp` | Time to open a TCP connection to `host:port`. |
| `traceroute` | The path to a target, hop by hop, with the networks (AS numbers) it crosses. Feeds the path-change alert. |
| `alive` | A fast up-or-down sweep across many `devices:`, by ICMP or, where ICMP is blocked, TCP. It answers "is it up" only, with no timing. Suited to hundreds or thousands of devices. |
| `ntp` | Clock offset, delay, jitter and stratum of NTP servers. Catches clock drift, which breaks TLS and makes logs hard to line up. |
| `mtu` | The largest packet that gets through to a target without fragmenting, between `min_mtu` and `max_mtu` (576 to 1500 by default). Catches MTU problems on VPNs and tunnels that ordinary ping misses. |

### Performance bundle

| Type | What it measures |
|---|---|
| `throughput` | Bandwidth between two agents. It's built in, so you don't need a separate bandwidth tool. `duration` and `max_bytes` limit a test; whichever is reached first ends it. See below. |
| `dns_propagation` | Asks many resolvers for the same record at once and reports whether they agree. Uses a built-in list of public resolvers, or your own `resolvers:` (up to 32). |
| `snmp` | SNMPv3 interface data from network devices: utilization, error and discard rates, and interfaces going up and down. One result per interface. |

### Routing bundle

| Type | What it measures |
|---|---|
| `bgp` | Whether a prefix is announced on the internet by the network you expect, checked against public routing data. |

Your [license](licensing.md) decides which bundles you can use.

## Bandwidth tests between agents

Bandwidth tests run between two of your agents, so you don't need a separate
bandwidth tool. The agent being tested to must accept tests:

```yaml
# on the target agent, in /etc/trcr/agent.yaml
agent:
  throughput_server:
    enabled: true
    listen_addr: 0.0.0.0:5202
```

Then, on the master:

```yaml
- name: london-to-paris
  type: throughput
  target: agent-paris          # port 5202 is added when you give none
  duration: 10s
  max_bytes: 100MB
  interval: 15m
  preferred_agents: [agent-london]
```

Both ends authenticate with their agent certificates, so only agents in your
deployment can run tests against each other. Open port 5202 between them, and
restart the target agent after you turn the listener on. Keep tests short and
infrequent: they use real bandwidth.

## SNMP

SNMP passphrases are read from environment variables, so they never sit in a
YAML file:

```yaml
- name: core-switch
  type: snmp
  target: 192.0.2.10
  interval: 1m
  allow_private_targets: true
  snmp:
    username: trcr-poller
    auth_protocol: SHA-256
    auth_passphrase_env: TRCR_SNMP_AUTH_CORE
    priv_protocol: AES-256
    priv_passphrase_env: TRCR_SNMP_PRIV_CORE
```

Variable names for SNMP secrets must start with `TRCR_SNMP_`. Set them in a
systemd drop-in on the agents that run the probe. See
[Security](security.md#secrets-in-configuration).

## Private and internal targets

By default, probes that open a connection to a target, such as `http`, `tcp`
and `ssl_expiry`, refuse private and special addresses: loopback, link-local,
the private ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`),
carrier-grade NAT, multicast and reserved ranges. A public name that points at
a private address is refused too.

This stops your agents being used to reach internal services, whether by
mistake or by someone who shouldn't be able to.

To monitor your own internal systems, say so on each probe:

```yaml
- name: intranet
  type: http
  url: https://intranet.example.internal
  allow_private_targets: true
```

A refused run is recorded with the error `private_target_refused`.

## Limits

Probes have fixed limits, so a typo in an interval or a packet count can't
turn your agents into a source of floods. `trcrd validate` rejects values
outside these limits, and agents check them again when they receive a probe.

| Setting | Limit |
|---|---|
| `interval` | At least 5 seconds (`ping`: at least 1 second) |
| `timeout` | At most 5 minutes for `http`, 10 minutes for others |
| `count` | At most 100 |
| `packet_size` | At most 1472 |
| `dns_propagation` resolvers | At most 32 |
| HTTP headers | Valid header names, no line breaks, at most 4 KiB |
| `ssl_expiry.ca_bundle` | A file under `/etc/trcr`, `/etc/ssl`, `/etc/pki`, `/usr/share/ca-certificates` or `/usr/local/share/ca-certificates` |

## Trying a probe by hand

```bash
trcrd run ping 1.1.1.1
trcrd run http https://example.com
```

This runs one probe straight away on the host you're on and prints the full
result. The exit status is 1 when the probe fails. It's the quickest way to
tell a network problem from a configuration problem: if `trcrd run` works on
the agent host but the probe fails, look at the probe's configuration.

## What a result contains

Every result carries the time, the probe's name and type, the target, the agent
that ran it, whether it succeeded, the measurements for that probe type, your
labels, how long it took, and, on failure, a short error class such as
`unexpected_status`, `cert_expired`, `lookup_failure` or
`private_target_refused`. Alert rules and dashboards work from
these fields.

Next, decide where your results are kept: [Storing results](backends.md).
