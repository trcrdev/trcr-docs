# Security

This page covers what you need to know to run TRCR safely: which ports it uses,
how agents are trusted, where secrets go, and how to run without internet
access.

## Ports

Use this table to set up firewalls and security groups. Only the first two
rows matter for most deployments.

| Port | Where | Direction | Use |
|---|---|---|---|
| 8443/tcp | Master | From every agent | Agents fetch probes and send results. Both sides present certificates. |
| 8444/tcp | Master | From agents being enrolled | Enrollment. You can close it between rollouts. |
| 8445/tcp | A waiting agent | From the master | Pairing-code enrollment only. The agent stops listening once enrolled. |
| 5202/tcp | Agents that accept bandwidth tests | From other agents | Only if you run `throughput` probes. |
| 8080/tcp | Master, only if you set `master.health_listen_addr` | From your load balancer or monitor | Plain health check. No data. See [Operations](operations.md#health-checks). |
| 9101/tcp | Master and agents, loopback only by default | From Prometheus | TRCR's own metrics. |
| 9102/tcp | Master, loopback only by default | From Prometheus | Probe results, if you use the Prometheus store. |
| 3000/tcp | All-in-one host, loopback only by default | From you | Grafana. |
| 443/tcp outbound | Master | To `trcr.dev` and `api.trcr.dev` | License requests and the hourly check-in. |

Agents also need to reach whatever they probe.

To limit who can connect to the master at all, list the networks your agents
are on:

```yaml
acl:
  allowed_cidrs: [203.0.113.0/24, 198.51.100.7/32]
  default_action: deny
```

## How agents are trusted

You don't need to set up certificates, but it helps to know how trust works,
so you can tell which parts of an enrollment command matter.

- The master is its own certificate authority. It creates the authority on
  first start and keeps it under `/var/lib/trcr`. You don't supply
  certificates.
- Enrollment gives each agent its own certificate, valid for 365 days.
  Agents renew their certificates by themselves once three quarters of the
  lifetime has passed. The master renews its own certificate too, without a
  restart.
- All traffic between agents and the master uses TLS 1.3, with both sides
  proving who they are.
- The `--ca-hash` in a join command, and the `--fingerprint` in a
  pairing-code enrollment, are what stop an agent being enrolled by, or with,
  the wrong host. Keep them in the command.
- Enrollment tokens work once and expire after an hour by default.
- The master labels each result with the identity from the agent's
  certificate, not with whatever the agent claims. One agent can't submit
  results in another's name.
- An agent is sent only the probes it's responsible for.
- Revoking an agent takes effect within seconds, whatever its certificate's
  expiry date. See [Agents](agents.md#retire-an-agent).

An agent that can't reach the master for a long time, past the life of its
certificate, must be enrolled again.

## Secrets in configuration

Configuration files end up in backups, version control and support tickets, so
keep passwords, tokens and webhook URLs out of them. There are two ways to do
that.

### Environment variables

Settings ending in `_env` name an environment variable to read the secret
from: `password_env`, `token_env`, `api_key_env`, `url_env`,
`auth_passphrase_env` and so on. On the master, put the values in
`/etc/trcr/master.env`, which the master's service reads, and keep it readable
by root and the `trcr` group only:

```bash
sudo nano /etc/trcr/master.env         # NAME=value, one per line
sudo chgrp trcr /etc/trcr/master.env && sudo chmod 0640 /etc/trcr/master.env
sudo trcrd validate
```

`validate` warns about any variable the master needs that no file of its
service sets.
If your master's service doesn't read `master.env` yet, see
[Storing results](backends.md#passwords-and-tokens).

### Encrypted values

For a password that has to sit inside a probe, such as HTTP basic
authentication, encrypt it on the master:

```bash
sudo trcrd encrypt-password --probe intranet --field basic_auth.password
```

It asks for the password without showing it and prints a value starting with
`secret:v1:`. Paste that into the probe:

```yaml
- name: intranet
  type: http
  url: https://intranet.example.internal
  allow_private_targets: true
  basic_auth:
    username: monitor
    password: "secret:v1:…"
```

`--probe` and `--field` tie the encrypted value to that one place, so it can't
be copied into another probe.

What this protects, and what it doesn't:

- It protects configuration that ends up in backups, screenshots, tickets and
  version control.
- The key is on the master, in `/var/lib/trcr`, readable only by the service.
  Someone who controls the master can read both the key and the value.
- The master decrypts the value at startup and sends it to the agents that run
  that probe, over the encrypted connection. Those agents hold it in memory.
  Use `agents:` or `preferred_agents:` to limit which agents receive a
  sensitive probe.

## What the services are allowed to do

If someone did break into a TRCR service, these limits keep the damage small.
Both services run as the unprivileged `trcr` user with systemd's protections
turned on: no new privileges, a read-only view of the system apart from TRCR's
own folders, a private `/tmp`, no access to home directories, and a restricted
set of system calls.

- The agent has one extra permission, to send ICMP packets for `ping`,
  `traceroute` and `mtu`. It can't capture network traffic.
- The master has no network privileges beyond listening on its ports.
- `/etc/trcr` is read-only to the services. This is why a renewed license is
  saved under `/var/lib/trcr`.
- Key files must be readable only by their owner. The service refuses to start
  if a key file is readable by others.

## Protection against misuse of probes

Agents send traffic on your behalf, so TRCR limits what they'll send. Probes
that connect to a host refuse private and special addresses unless you
allow them per probe. See [Probes](probes.md#private-and-internal-targets).
Probe intervals, timeouts and packet counts have fixed limits, checked on the
master and again on each agent, so a configuration mistake can't turn your
agents into a source of floods.

## What TRCR sends to trcr.dev

Your results stay on your systems. The master checks in with `api.trcr.dev`
about once an hour. It sends the license and a fixed identifier for the host,
and optionally usage counts (`heartbeat.usage_stats`). The check-in is how a
free license renews and how a revoked license is detected. Your probe results,
targets and configuration are never sent. Agents don't contact trcr.dev at all,
apart from downloading the installer.

If the check-in fails, TRCR logs a warning, keeps trying, and keeps running.

## Run TRCR without internet access

TRCR works on a network with no route to the internet. You lose two
conveniences: the one-command installer and automatic license renewal. Each
has a manual alternative, described below. Start by turning off the check-in
in `master.yaml`:

```yaml
heartbeat:
  enabled: false
```

- Install from a copy of the binary and its checksum file that you download on
  another machine. Verify the checksum before installing.
- Use a license file you were issued: copy it to `/etc/trcr/license.lic` with
  `sudo install -o root -g trcr -m 0640`.
- The license still expires on its expiry date. Without the check-in there is
  no automatic renewal, so put the date in your calendar and install the new
  file before then.
- Enroll agents with join commands or pairing codes as usual. They only need
  to reach the master. Copy the binary to the agent yourself, and use the
  shorter `sudo trcrd join …` form that `enroll-agent` prints instead of the
  `curl` command.

## Verifying downloads

The installer checks a signature over the list of checksums before it trusts
any file, using a public key built into the script, and then checks each file
against that list. A tampered binary doesn't install. Use the installer where
you can, because it makes both checks. If you download by hand, at least
compare the file with `SHA256SUMS`:

```bash
curl -fsSL https://trcr.dev/download/latest/linux-amd64 -o trcrd
curl -fsSL https://trcr.dev/download/latest/SHA256SUMS | grep linux_amd64
sha256sum trcrd
```

The two checksums must be identical. The list names each file by release and
platform, for example `trcrd_v26.11.0_linux_amd64`.

## Reporting a security problem

Email support@trcr.dev. Please don't open a public issue for a security
problem, because issues are visible to everyone.
