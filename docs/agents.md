# Agents

Agents do the measuring, so you'll want them in the places you care about:
offices, data centers, cloud regions. Adding one takes a couple of minutes and
needs no email address or license of its own.

There are two ways to add an agent. Which one you use depends on which side
can open a connection to the other:

| Situation | Use |
|---|---|
| The agent can reach the master. This is the usual case, and the only one that works behind NAT. | [A join command](#add-an-agent-with-a-join-command) |
| The master can reach the agent, but not the other way round. | [A pairing code](#pair-an-agent-the-master-can-reach) |

Before you add a remote agent, check two things on the master. Ports 8443 and
8444 must be open (see [Ports and firewalls](install.md#ports-and-firewalls)),
and [`advertise_addr`](configuration.md#advertise_addr-is-required-for-remote-agents)
must be an address the agent can reach.

The master's license sets how many agents you can enroll. The free license
allows five, and on an all-in-one host the local agent is one of them. Agents
you've revoked don't count. When the limit is reached, the master refuses the
next enrollment and its log says `enroll: license agent limit reached`.

## Add an agent with a join command

To get the command, run this on the **master**:

```bash
sudo trcrd enroll-agent
```

It prints one command with a token in it, like this:

```bash
curl -fsSL https://trcr.dev/install/install.sh | sh -s -- \
  --join 192.0.2.10:8444 \
  --token TRCR-ENROLL-1.… \
  --ca-hash sha256:…
```

Run that whole command on the **agent** host. It installs `trcrd`, creates the
`trcr` user, enrolls with the master, writes `/etc/trcr/agent.yaml`, and
installs and starts the agent's service. You'll see:

```
==> Enrolling with the master at 192.0.2.10:8444 ...
...
enrolled as web-02
...
==> This host is enrolled and the agent is running. Nothing else to do here.
```

To check it worked, run `sudo trcrd agents` on the master. The new agent
should show `up` within a minute.

Things worth knowing about the join command:

- The address after `--join` is the master's `advertise_addr`. If the agent
  reaches the master by another name or address, replace it with that one,
  keeping port 8444. Or have the master print it for you:
  `sudo trcrd enroll-agent --advertise-addr trcr-master.example.com:8444`.
- The token works once and expires after an hour. To change how long it lasts,
  run `enroll-agent` with `--expires`. For a fresh token, run
  `sudo trcrd enroll-agent` again.
- `--ca-hash` tells the agent which master to trust, so a different host
  pretending to be your master can't enroll it. `enroll-agent` always includes
  it. Keep it in the command.
- The agent's name defaults to its hostname, in lower case. To choose another
  name, run `enroll-agent` with `--node-id <name>`.
- If `trcrd` is already installed on the agent host, `enroll-agent` also prints
  the shorter `sudo trcrd join …` form.
- Pasting the same command twice is harmless. On a host that's already
  enrolled, the installer says `This host is already enrolled as <name>.` and
  only makes sure the service is installed and running.
- If the master is still starting when the agent tries to enroll, the agent
  prints `waiting for the master at 192.0.2.10:8444 ...` and keeps trying for
  20 seconds.
- An agent that runs in a container takes the token and the CA hash as two
  environment lines instead. Print them on the master with
  `sudo trcrd enroll-agent --env`. See [Containers](containers.md).

If the master already has an agent with the same name, it refuses the
enrollment and the installer says:

```
error: The master already has an agent with this name. On the master run:
         sudo trcrd agents remove web-02
```

That usually means the host was enrolled before, then uninstalled or rebuilt,
and the master still has its record. On the **master**, remove the old record:

```bash
sudo trcrd agents remove web-02 --yes
```

Then run the same join command on the agent again. A refused attempt doesn't
use up the token, so the command works for the rest of its hour. To keep the
old record and enroll under a new name instead, add `--node-id <other-name>`
to the join command.

If enrollment fails for any other reason, the installer says so and tells you
what to try:

```
error: This host could not enroll with the master.
       Each token works once and expires after an hour, so start with a new one: run
       'sudo trcrd enroll-agent' on the master and paste the line it prints here.
       If a new token fails too, check that this host can reach the master on
       port 8444:  nc -vz 192.0.2.10 8444
```

Do what it says. The agent host keeps nothing from a failed attempt, so you can
paste a new command straight away. If `nc` can't connect, the master's port
8444 is closed or the address is one the agent can't reach. If you've hit the
license's agent limit, the master's log says so (see above).

## Pair an agent the master can reach

Use this when the master can open a connection to the agent but the agent
can't reach the master. On the **agent** host, run:

```bash
curl -fsSL https://trcr.dev/install/install.sh | sh -s -- --agent
```

This installs `trcrd`, creates the `trcr` user, and starts the agent in a
waiting state on port 8445. It ends by printing a pairing code, a fingerprint
and the exact command to run on the master:

```
==> This agent is installed and waiting for your master.

    Pairing code:  K7QM-3XWD
    Fingerprint:   sha256:9f2c…e1

    To connect it, run this on the master:
      sudo trcrd enroll-agent 203.0.113.7 --code K7QM-3XWD --fingerprint sha256:9f2c…e1

    The code works once. As soon as the agent is enrolled, it stops listening
    on port 8445 for good.
```

Copy that command and run it on the **master**. The master first checks that
the host answering at that address holds the key that matches the
fingerprint, so a different host gets nothing, not even the code. Then it waits
for the agent to report in (60 seconds by default; change it with `--timeout`)
and prints:

```
enrolled web-03 (203.0.113.7:8445)
```

If the agent's address in the printed command isn't the one the master uses to
reach it, replace it.

### If the defaults don't fit

- `--accept-from IP[,IP]` on the agent's install command makes it accept the
  master only from those addresses.
- `--bootstrap-port N` changes the waiting port from 8445. The printed command
  then includes the port, as in `enroll-agent 203.0.113.7:N`.
- `--node-id NAME` gives the agent a name other than its hostname.
- `--open-firewall` opens the waiting port in firewalld or ufw. Without it, the
  installer prints the command. After enrollment nothing listens on that port,
  but the firewall rule stays, so the installer also prints the command to
  remove it.
- If you've lost the code, run `sudo trcrd join --pending --show-code` on the
  agent. Running the install command again on a waiting agent prints the same
  code and fingerprint.
- If a wrong code is entered several times, the agent stops accepting attempts
  for a short while. Wait a minute, then try again.

## Check the agent is reporting

On the master, run:

```bash
sudo trcrd agents
```

You'll see something like this:

```
NODE_ID       STATUS  LAST SEEN  PROBES  CERT EXPIRES
web-01-local  up      14s ago    8       in 364d
web-02        up      9s ago     8       in 364d

2 agent(s); down-after 1m30s
```

A new agent should show `up` within a minute. `PROBES` is how many probes the
master serves to that agent, including the automatic agent-to-agent pings.
`CERT EXPIRES` is when its certificate runs out; agents renew it by themselves
long before then. The last line says how long an agent can be silent before it
counts as down.

| Status | What it means |
|---|---|
| `up` | Reporting normally. |
| `down` | Was reporting, and has been silent for longer than the limit (90 seconds by default). |
| `never-seen` | Enrolled, but has never made a successful call. See [Troubleshooting](troubleshooting.md#an-agent-is-stuck-at-never-seen). |
| `revoked` | You've withdrawn trust in it. Shown only with `--all`. |

`trcrd agents` reads saved state, so it works even when the master is stopped.
`--json` gives output for scripts. `--stale` lists only the agents that aren't
reporting and exits with status 1 if there are any, which makes it easy to
check from cron:

```bash
trcrd agents --stale || echo "an agent is not reporting"
```

## Agent-to-agent probes

As soon as two agents are enrolled, the master adds a ping between every pair,
in both directions, named `mesh-<a>-to-<b>`. These feed the Agent Mesh and
Agent-to-Agent dashboards. They show up in `trcrd probes` marked `auto-mesh`.
They're not written to your configuration files, and they don't count as a
license bundle.

To turn them off or change how often they run, set this in `master.yaml` and
restart the master:

```yaml
master:
  agents:
    auto_mesh: true            # set false to turn these off
    auto_mesh_interval: 60s
```

## Choose where a probe runs

By default, every agent runs every probe. To pick agents for a probe, see
[Probes](probes.md#where-a-probe-runs).

## Move an agent to another master

First, run this on the **agent**:

```bash
sudo trcrd leave
```

Then enroll it with the new master in either of the two ways above.

`trcrd leave` shows the agent's name and its master, and asks you to confirm.
It tells the old master first, while the agent's certificate still works. Then
it stops the service and deletes the agent's certificate and `agent.yaml`. If
the master can't be reached, nothing is deleted. For a master that's gone for
good, add `--local-only`. To keep `agent.yaml`, add `--keep-config`.

This works the same for an agent enrolled with a pairing code. Its master's
address isn't in `agent.yaml`, so `leave` uses the one the agent recorded when
it was paired, and says so:
`master: 192.0.2.10:8443 (recorded at the pairing enrollment)`.

If you rebuilt the master and paste its new join command on an old agent, the
agent sees the different `--ca-hash`, says
`the master was rebuilt; enrolling again`, and enrolls with the new master.

To see which master a host belongs to, run this on the agent:

```bash
sudo grep master_addr /etc/trcr/agent.yaml
```

An agent enrolled with a pairing code has no `master_addr` line. For one of
those, `sudo trcrd leave` shows the master at the top of its question; answer
`n` to change nothing.

## Retire an agent

These commands stop trusting an agent and clean up after it:

```bash
sudo trcrd agents revoke <name>    # on the master: stop trusting it, keep the record
sudo trcrd agents remove <name>    # on the master: delete the record
sudo trcrd leave                   # on the agent: undo the enrollment
```

Both `revoke` and `remove` ask you to confirm; add `--yes` after the name to
skip the question. If you answer no, they print
`aborted (nothing changed; pass --yes to skip the prompt)` and exit with
status 1, so a script can tell. Revoking takes effect on a running master
within seconds, with no restart. The agent is refused on its next call, even
though its certificate hasn't expired.

- `revoke` keeps the record, so you can see later that the agent was retired.
  You can enroll a new agent under the same name; it gets a new certificate,
  and the old one stays refused.
- `remove` deletes the record and frees the name.
- Neither command touches the agent host. Run `sudo trcrd leave` there, or
  uninstall TRCR from it (see [Operations](operations.md#uninstall-trcr)).
  Both work for agents enrolled with a join command or a pairing code.

Revoked and removed agents no longer count toward your license's agent limit.
