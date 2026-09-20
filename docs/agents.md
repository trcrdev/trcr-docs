# Agents

An agent needs no email address, no licence and no registration. There are two
ways to enrol one. Choose by which side can reach the other.

| Situation | Use |
|---|---|
| The master can connect to the agent | [Pairing code](#pairing-code-the-master-reaches-the-agent) |
| The agent is behind NAT or a firewall, and can only connect out | [Token one-liner](#token-one-liner-the-agent-reaches-the-master) |

Before adding a remote agent, make sure the master has
[`advertise_addr`](configuration.md#advertise_addr-is-required-for-remote-agents)
set and [ports 8443 and 8444 open](install.md#firewall).

## Pairing code (the master reaches the agent)

On the **agent** host:

```bash
curl -fsSL https://trcr.dev/install/install.sh | sh -s -- --agent
```

This installs `trcrd`, creates the `trcr` service account, and starts the agent
in a waiting state, listening on port 8445. The install ends by printing a
pairing code and a fingerprint:

```
Pairing code: K7QM-3XWD
Fingerprint:  sha256:9f2c…e1
```

On the **master**, using the agent's address and those two values:

```bash
sudo trcrd enroll-agent 203.0.113.7 --code K7QM-3XWD --fingerprint sha256:9f2c…e1
```

The master first confirms that the host answering at that address holds the key
behind the fingerprint. A wrong host gets nothing, not even the code. The
command waits until the agent has reported in (60 seconds by default; change it
with `--timeout`) and prints `enrolled <name>`.

As soon as enrolment succeeds, the agent deletes the pairing code and closes
port 8445 for good.

Useful options and facts:

- `--accept-from IP[,IP]` on the install accepts enrolment only from those
  master addresses. For automated rollouts it can also replace the code. Only
  rely on that inside a network where those addresses cannot be used by anyone
  else, and keep `--fingerprint` in every case.
- `--bootstrap-port N` changes the port. Then use `enroll-agent IP:N` on the
  master.
- `--open-firewall` opens the port in firewalld or ufw. Without it the
  installer prints the command. The firewall rule does not close by itself, so
  the installer also prints the command to remove it afterwards.
- Lost the code? On the agent, `sudo trcrd join --pending --show-code` prints
  the code and fingerprint again. Re-running the installer on a waiting agent
  prints the same ones.
- Repeated wrong codes are blocked for a short time.

## Token one-liner (the agent reaches the master)

On the **master**:

```bash
sudo trcrd enroll-agent
```

It prints one command with a token included. Run that command on the **agent**
host:

```bash
curl -fsSL https://trcr.dev/install/install.sh | sh -s -- \
  --join trcr-master.example.com:8444 \
  --token TRCR-ENROLL-1.… \
  --ca-hash sha256:…
```

On a host that had nothing installed, this installs `trcrd`, enrols, writes
`/etc/trcr/agent.yaml`, creates the service account, installs the service and
starts it.

- **The agent's name defaults to its hostname**, in lower case. Pass
  `--node-id` to `enroll-agent` to choose a name.
- **Tokens work once and expire** after one hour by default. Change that with
  `--expires`.
- **`--ca-hash` is what makes enrolment safe.** It tells the agent which master
  to trust. `enroll-agent` always includes it; do not remove it.
- If `trcrd` is already on the host, `enroll-agent` also prints the plain
  `trcrd join …` form.
- Pasting the same line twice is harmless. On an agent that is already enrolled
  it only makes sure the service is installed and running.

## Checking

On the master:

```bash
sudo trcrd agents
```

A new agent should show `up` within a minute. The states are:

| State | Meaning |
|---|---|
| `up` | Reporting normally. |
| `down` | Was reporting, and has been silent for longer than the limit (90 seconds by default). |
| `never-seen` | Enrolled, but has never made a successful call. See [Troubleshooting](troubleshooting.md#an-agent-is-stuck-at-never-seen). |
| `revoked` | Trust withdrawn. Listed with `--all`. |

`trcrd agents` reads saved state, so it works even when the master is stopped.
`--json` gives output for scripts. `--stale` lists only agents that are not
reporting and exits with status 1 if there are any:

```bash
trcrd agents --stale || echo "an agent is not reporting"
```

## Agent-to-agent probes

As soon as two agents are enrolled, the master creates a ping between every
pair, in both directions, named `mesh-<a>-to-<b>`. These feed the Agent Mesh
and Agent-to-Agent dashboards. They appear in `trcrd probes` marked
`auto-mesh`, which shows where they came from and is not a licence bundle. They
are not written to your configuration files.

```yaml
master:
  agents:
    auto_mesh: true            # set false to turn these off
    auto_mesh_interval: 60s
```

## Choosing where a probe runs

Each probe can say which agents run it. See
[Probes](probes.md#where-a-probe-runs).

## Moving an agent to another master

On the agent:

```bash
sudo trcrd leave
```

Then enrol it with the new master in either of the two ways above.

`trcrd leave` tells the old master first, while the agent's certificate still
works, then stops the service and deletes the agent's certificate and
`agent.yaml`. If the master cannot be reached, **nothing is deleted**. For a
master that is gone for good, use `--local-only`. `--keep-config` keeps
`agent.yaml`.

`trcrd join` refuses to run on a host that is already enrolled:

```
trcrd join: config /etc/trcr/agent.yaml already exists; pass --force to overwrite
agent already enrolled at /var/lib/trcr/agent; pass --force to re-enroll (destructive)
```

This is a local check, not a network problem. Prefer `trcrd leave`. Use
`--force` only for an enrolment that is stale or never completed. To see which
master a host belongs to:

```bash
grep master_addr /etc/trcr/agent.yaml
```

If you rebuilt the master and paste a new one-liner on an old agent, the agent
notices the different `--ca-hash` and enrols again.

## Retiring an agent

```bash
sudo trcrd agents revoke <name>    # on the master: stop trusting it, keep the record
sudo trcrd agents remove <name>    # on the master: delete the record
sudo trcrd leave                   # on the agent: undo the enrolment
```

Revoking takes effect on a running master within seconds, with no restart.
A revoked agent is refused on its next call, even though its certificate has
not expired.

- **`revoke`** keeps the record, so you can see later that the agent was
  retired. The name can be used again: enrolling under it issues a new
  certificate. The old certificate does not start working again.
- **`remove`** deletes the record and frees the name.
- Neither command touches the agent host.
