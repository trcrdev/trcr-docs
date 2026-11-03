# Installing with Docker or Podman

The same daemon the [installer](install.md) puts on a host is published as a
container image, `ghcr.io/trcrdev/trcrd`, built for Linux on amd64 and
arm64. Every release has its own tag (`v26.11.0` and so on); the files below
pin one, and you move to a new release by changing it.

Everything on this page works with Docker Compose v2 and with Podman. The
files it uses are in this repository:

| File | What |
|---|---|
| [`containers/compose.yml`](../containers/compose.yml) | master, local agent, PostgreSQL results store and Grafana on one host |
| [`containers/compose.agent.yml`](../containers/compose.agent.yml) | an agent on another host |
| [`containers/podman/`](../containers/podman/) | the same stack as quadlet units for Podman under systemd |

Choose between a container and a host install per machine, not per
deployment. A master in a container with agents installed directly on other
hosts is a normal setup, and so is the reverse.

## Start a master, an agent and dashboards on one host

You need Docker with Compose v2, your `license.lic` (or an email address to
request a free one), and the name or address other machines will use to
reach this host. Work in an empty directory on the **master**:

```bash
mkdir trcr && cd trcr
curl -fsSLO https://raw.githubusercontent.com/trcrdev/trcr-docs/main/containers/compose.yml
cp ~/Downloads/license.lic .
echo "TRCR_ADVERTISE_ADDR=mon.example.com:8444" >> .env
docker compose up -d
```

`TRCR_ADVERTISE_ADDR` is the address agents dial. It goes into the master's
certificate, so it has to be how other hosts reach this one, never the
container's own address. Without it, `docker compose up` stops at once and
tells you to set it.

Don't have a license file yet? Put `TRCR_LICENSE_EMAIL=you@example.com` in
`.env` instead of copying the file. The first start then requests a free
license and waits for you to click the link we email you (up to 30
minutes); `docker compose logs -f trcr-init` shows it waiting.

The first start takes about 20 seconds once the images are pulled. You'll
see something like this from `docker compose ps -a`:

```
NAME                   IMAGE                           SERVICE           STATUS
trcr-trcr-agent-1-1    ghcr.io/trcrdev/trcrd:v26.11.0  trcr-agent-1      Up 2 minutes
trcr-trcr-enroll-1     ghcr.io/trcrdev/trcrd:v26.11.0  trcr-enroll       Exited (0) 2 minutes ago
trcr-trcr-grafana-1    grafana/grafana:12.2.1-ubuntu   trcr-grafana      Up 2 minutes
trcr-trcr-init-1       ghcr.io/trcrdev/trcrd:v26.11.0  trcr-init         Exited (0) 2 minutes ago
trcr-trcr-master-1     ghcr.io/trcrdev/trcrd:v26.11.0  trcr-master       Up 2 minutes (healthy)
trcr-trcr-results-pg-1 postgres:18-trixie              trcr-results-pg   Up 2 minutes (healthy)
```

`trcr-init` and `trcr-enroll` are one-shot jobs; `Exited (0)` is what they
look like when they succeeded. To see that the agent reports in, run this on
the **master**:

```bash
docker compose exec trcr-master trcrd agents
```

```
NODE_ID       STATUS  LAST SEEN  PROBES  CERT EXPIRES
trcr-agent-1  up      11s ago    7       in 364d

1 agent(s); down-after 1m30s
```

When you see `up` next to `trcr-agent-1`, you're done. The seven starter
probes (ping, DNS, HTTP, certificate expiry, TCP, traceroute and an alive
sweep of two public resolvers) deliver their first results within a minute.
Open Grafana at `http://127.0.0.1:3000` (this host only), log in as `admin`
with the generated password:

```bash
docker compose exec trcr-master cat /run/trcr-secrets/grafana_admin_password
```

The home dashboard is the TRCR overview; the other sixteen are in the TRCR
folder. The datasource is already set up and points at the results store.
On a host with 512 MB of memory Grafana takes about four minutes to show
all its dashboards and pushes the host into swap; leave it out there (see
below) or give the host more memory.

### What the first start did

`trcr-init` generated the Postgres and Grafana passwords into a volume only
these containers mount, wrote `etc/master.yaml` and the starter probes in
`etc/conf.d/starter.yaml`, installed your license, and set up Grafana's
datasource and dashboards. `trcr-enroll` created a one-hour, single-use
token for the local agent and handed it over through a volume, never
`.env`; the agent enrolled with it on its first start and keeps its
identity in its own volumes, so restarts and `--force-recreate` don't
enroll again. Everything under `etc/` belongs to uid 65532, the user the
daemon runs as, and is yours to edit; reference copies of every
configuration file are in `etc/examples/`.

`trcr-init` runs again on every `up` and every start of the stack, and does
only what's missing. When nothing is, it prints a single line:

```
trcr-init: already set up; nothing to do.
```

## Add an agent on another host

On the **master**, create the agent's token and CA hash:

```bash
docker compose exec trcr-master trcrd enroll-agent --env
```

It prints two lines, `TRCR_ENROLL_TOKEN=...` and `TRCR_CA_HASH=...`. Then on
the **agent**, in an empty directory:

```bash
mkdir trcr-agent && cd trcr-agent
curl -fsSLO https://raw.githubusercontent.com/trcrdev/trcr-docs/main/containers/compose.agent.yml
cat > .env <<EOT
TRCR_JOIN=mon.example.com:8444
TRCR_NODE_ID=branch-office
TRCR_ENROLL_TOKEN=<the printed token>
TRCR_CA_HASH=<the printed hash>
EOT
docker compose -f compose.agent.yml up -d
```

The agent enrolls on its first start and shows up in `trcrd agents` on the
master within 30 seconds. The token is single-use and expires after an hour
(change that with `--expires` on `enroll-agent`); once the agent is listed,
delete the two lines from `.env`. Ports 8443 and 8444 on the master must be
reachable from the agent. An agent host that should run the daemon directly
uses the join command `trcrd enroll-agent` prints without `--env`; see
[Adding agents](agents.md).

## Podman

Podman runs the same files two ways. Both need rootful Podman: an agent that
runs traceroute needs a network stack that returns TTL-exceeded replies,
which rootless Podman's user-mode network does not.

### With podman-compose

Install `podman-compose` from your distribution first (`sudo dnf install
podman-compose` on Fedora, `sudo apt install podman-compose` on Debian).
Without it, `podman compose` fails with "looking up compose provider failed".
Then follow the Docker steps above with `sudo podman-compose` in place of
`docker compose`, including for every check (`sudo podman-compose exec
trcr-master trcrd agents`): podman-compose names the containers
`trcr_trcr-master_1` and so on, so a plain `podman exec trcr-master` does
not find them. The `:z` labels on the bind mounts are already in the file
for SELinux hosts.

Three commands differ. `ps` takes no `-a` and lists the finished jobs
anyway. `restart` prints "container state improper", exits 0 and restarts
nothing, so use `stop` and then `start` (`sudo podman-compose stop
trcr-master && sudo podman-compose start trcr-master`). There is no `rm`;
"An agent that never came up" below shows what to run instead.

One `sudo podman-compose up -d` runs `trcr-init` several times, once for each
service that depends on it; that's how podman-compose starts dependencies.
The first run does the setup, and each later one prints only
`trcr-init: already set up; nothing to do.` That makes the first start take
about 30 seconds once the images are pulled, rather than 20.

### With quadlets

Quadlet turns `.container`, `.network` and `.volume` files under
`/etc/containers/systemd/` into systemd services at `daemon-reload`, which
is the better fit for a server that should come back on its own after a
reboot. It needs Podman 5 or newer (Debian 13, Fedora 41 and later, RHEL
10).

Put your inputs where the units expect them, on the **master**:

```bash
sudo mkdir -p /etc/trcr /etc/trcr-container
sudo install -m 0600 ~/Downloads/license.lic /etc/trcr-container/license.lic
echo "TRCR_ADVERTISE_ADDR=mon.example.com:8444" | sudo tee /etc/trcr-container/setup.env
sudo chmod 0600 /etc/trcr-container/setup.env
```

`setup.env` takes the same variables as `.env` does for Compose
(`TRCR_LICENSE_EMAIL` instead of a license file, for example). Then install
the units and start the stack:

```bash
cd /etc/containers/systemd
for f in trcr.network trcr-init.container trcr-results-pg.container trcr-master.container \
         trcr-enroll.container trcr-agent.container trcr-grafana.container \
         trcr-master-state.volume trcr-agent-etc.volume trcr-agent-state.volume \
         trcr-results-pg-data.volume trcr-secrets.volume trcr-bootstrap.volume \
         trcr-grafana-data.volume trcr-grafana-provisioning.volume trcr-grafana-dashboards.volume; do
  sudo curl -fsSLo $f https://raw.githubusercontent.com/trcrdev/trcr-docs/main/containers/podman/$f
done
sudo systemctl daemon-reload
sudo systemctl start trcr-master trcr-agent trcr-grafana
```

`systemctl start` returns after about 25 seconds, once the master is
healthy and the agent is running; the setup and enrollment units run first
on their own. There is nothing to `enable`: the units start at boot through
their `[Install]` sections, and the one-shot units run again at every boot
and find nothing left to do (`trcr-init: already set up; nothing to do.` in
the journal). Check the same way as with Compose:

```bash
sudo podman exec trcr-master trcrd agents
sudo podman exec trcr-master cat /run/trcr-secrets/grafana_admin_password
```

Leave out `trcr-grafana.container` and its three `trcr-grafana-*.volume`
files on a small host, or if you run Grafana elsewhere; the rest of the
stack uses about 200 MB of memory. For an agent on another host, install
`trcr-agent-remote.container` with the two `trcr-agent-*.volume` files, and
put the output of `trcrd enroll-agent --env` plus `TRCR_JOIN=` into
`/etc/trcr-container/agent.env` (mode 0600). The comments at the top of each
unit say what it needs.

## What runs where

| Service | Runs as | Network | Ports on the host |
|---|---|---|---|
| `trcr-master` | uid 65532 | bridge | 8443 (agents), 8444 (enrollment), 127.0.0.1:9101 (metrics) |
| `trcr-agent-1` | uid 65532 | host | 5202 (throughput server, mTLS) |
| `trcr-results-pg` | Postgres' own user | bridge | none |
| `trcr-grafana` | uid 472 | bridge | 127.0.0.1:3000 |
| `trcr-init` | root, one-shot | bridge | none |
| `trcr-enroll` | uid 65532, one-shot | bridge | none |

Ping, batch ping and traceroute open raw sockets, which needs the `NET_RAW`
capability. Docker only grants capabilities to root, so the `trcrd`
containers start as root with everything but `NET_RAW`, `SETUID` and
`SETGID` dropped, and the entrypoint immediately switches to uid 65532,
keeping `NET_RAW` and nothing else; `no-new-privileges` is on. Podman hands
the capability to the image's user directly, so the quadlets run as uid
65532 from the start. An agent that only runs TCP, HTTP, DNS or SSL probes
can drop `NET_RAW` too.

The agent uses host networking so its measurements come from the host's
own interfaces and traceroute sees real hops rather than the container
bridge. Generated passwords live in a named volume (`trcr_secrets`) that only
the containers needing them mount; nothing secret is in `.env` or in
`docker compose config`. The master's hostname is pinned to `trcr-master`
because the license is bound to a fingerprint derived from it; don't change
it after the license is installed. The config directory `etc/` is the one
bind mount, so you can edit it and back it up with the tools you already
have.

## Day-to-day operations

**Changing probes.** Edit or add files under `etc/conf.d/`
(`/etc/trcr/conf.d/` with quadlets). Each file holds a list of probes, and
files whose names start with `_` are skipped. `_samples.yaml` there has a
sample of every probe type: the ones that work against public targets are
live, and the ones that need your own data (throughput between two agents,
batch ping, SNMP, BGP and DNS propagation) are commented out. It's rewritten
for every release, so don't edit it; copy it to an active name (see below)
and edit the copy. A minimal file:

```yaml
probes:
  - name: office-website
    type: http
    url: https://www.example.com
    interval: 1m
```

Then restart the master; it reads its configuration once at startup, so
there is no hot reload:

```bash
docker compose restart trcr-master
docker compose exec trcr-master trcrd probes
```

With quadlets: `sudo systemctl restart trcr-master`, which also re-runs
`trcr-enroll`; the first time it removes the agent's used token, and after
that it finds nothing to do. The agent keeps running and reconnects.
`trcrd probes` lists what the files say, not what the agents run; the
agent's log (`docker compose logs trcr-agent-1`, `sudo journalctl -u
trcr-agent`) shows the change arrive within a minute, with a new `revision`:

```
{"time":"2026-11-03T04:02:26.889285345Z","level":"INFO","msg":"probe config applied","revision":2,"probe_count":8,"probe_count_unfiltered":8}
```

The daemon runs as uid 65532 and must be able to read the file, so install
it rather than copy it (on a Mac, see below; with quadlets the target is
`/etc/trcr/conf.d/NAME.yaml`):

```bash
sudo install -o 65532 -g 65532 -m 0640 FILE etc/conf.d/NAME.yaml
```

A file it can't read is skipped with an error in the master's log, and
`trcrd validate` reports it; `restart` doesn't re-run the setup job that
fixes ownership on `up`.

**An agent that never came up.** If an agent's first enrollment failed (the
token expired, a typo in `TRCR_JOIN`), the agent container restarts and
tries again with the same token until the token is used or expires. Fix the
cause, then start clean:

```bash
docker compose exec trcr-master trcrd agents remove --yes trcr-agent-1
docker compose rm -sf trcr-agent-1 trcr-enroll
docker volume rm trcr_trcr_agent_1_etc trcr_trcr_agent_1_state trcr_trcr_bootstrap
docker compose up -d
```

`rm -sf` removes just those two containers (`down` would also remove the
network the rest of the stack uses). `agents remove` only matters when the
agent is already listed; a listed agent whose volumes are gone can't enroll
again under the same name otherwise. For a remote agent, run
`enroll-agent --env` again and replace the two lines in its `.env`.

podman-compose has no `rm`, so remove the two containers with Podman
itself, the agent first because it depends on the enrollment job:

```bash
sudo podman-compose exec trcr-master trcrd agents remove --yes trcr-agent-1
sudo podman-compose stop trcr-agent-1 trcr-enroll
sudo podman rm trcr_trcr-agent-1_1 && sudo podman rm trcr_trcr-enroll_1
sudo podman volume rm trcr_trcr_agent_1_etc trcr_trcr_agent_1_state trcr_trcr_bootstrap
sudo podman-compose up -d
```

**Upgrading.** Put `TRCR_IMAGE=ghcr.io/trcrdev/trcrd:<release>` in `.env`
and run `docker compose up -d`; with quadlets, change the `Image=` line in
the `trcr-*.container` files, then `sudo systemctl daemon-reload` and
`sudo systemctl restart trcr-init trcr-master trcr-enroll trcr-agent`.
Configuration, state and license live in `etc/` and the volumes, so a new
image picks them up as they are. The setup job refreshes the Grafana
dashboards to the ones shipped with that release, and the probe samples too:

```
trcr-init: refreshed /etc/trcr/conf.d/_samples.yaml (probe samples for this release)
trcr-init: done.
```

When the release brings new dashboards,
`trcr-init: Grafana: 17 dashboards and the datasource are set up` comes
before `done.`. The Grafana address and the command that shows its password
come only at the end of the first start, written for the stack it runs in
(`docker compose exec`, `sudo podman-compose exec` or `sudo podman exec`).

**Checking.** The master's CLI works through `exec` as it does on a host:

```bash
docker compose exec trcr-master trcrd agents      # which agents report in
docker compose exec trcr-master trcrd probes      # which probes run where
docker compose exec trcr-master trcrd run ping 1.1.1.1
docker compose logs --tail 50 trcr-agent-1       # an agent's log
curl -s http://127.0.0.1:9101/metrics | head     # Prometheus metrics
```

Where [Operations](operations.md) says `systemctl restart trcrd-master`,
use `docker compose restart trcr-master` or `sudo systemctl restart
trcr-master`; where it says `journalctl -u trcrd-agent`, use
`docker compose logs trcr-agent-1`.

**Removing everything.** `docker compose down -v` stops the containers and
deletes the volumes, including the master's CA and the results. `etc/` on
the host stays. To start from scratch, keep a copy of `etc/license.lic` (it
belongs to uid 65532, so copy it with `sudo`), remove `etc/` as well, and put
the copy back as `etc/license.lic` before `docker compose up -d`. Otherwise
the first start installs `license.lic` from next to `compose.yml` if it's
still there, or, with `TRCR_LICENSE_EMAIL` in `.env`, requests a new license
by email. On an agent host of its own, run it where `compose.agent.yml` is:
`docker compose -f compose.agent.yml down -v` (with podman-compose,
`sudo podman-compose -f compose.agent.yml down -v`).

With quadlets, stop every `trcr-` unit, including the volume and network
units Quadlet generated so that a later install creates the volumes again,
then remove the unit files and the volumes:

```bash
sudo systemctl stop 'trcr-*'
cd /etc/containers/systemd && sudo rm -f trcr.network trcr-*.container trcr-*.volume
sudo systemctl daemon-reload
sudo podman volume rm trcr-master-state trcr-agent-etc trcr-agent-state trcr-results-pg-data \
  trcr-secrets trcr-bootstrap trcr-grafana-data trcr-grafana-provisioning trcr-grafana-dashboards
sudo podman network rm trcr
```

`/etc/trcr` and `/etc/trcr-container` stay, with your license. To start from
scratch, also remove `/etc/trcr`; the setup job writes it again from what's
in `/etc/trcr-container`. If your license came by email, it's only in
`/etc/trcr`, so copy `/etc/trcr/license.lic` to
`/etc/trcr-container/license.lic` first. On a remote agent, remove just the two
`trcr-agent-*` volumes; there is no network.

After `trcrd agents remove` or `agents revoke`, a master in a container
prints these remote-agent commands, for Compose and for quadlets, so you can
clean up the agent's host too. For an agent installed directly on a host, it
gives `sudo trcrd leave --local-only --yes` to run there instead.

## macOS and Docker Desktop

The stack runs on Docker Desktop, with two differences. Host networking
puts the agent in Docker Desktop's Linux VM, not on your Mac, so its
latency and traceroute are measured from that VM (usually `192.168.65.x`);
fine for trying TRCR, not for measuring the Mac's own connection. And the
bind-mounted `etc/` shows up owned by your macOS user, not uid 65532; that
is Docker Desktop's file sharing, and nothing needs changing. To add a
probe file, `install -m 0640 FILE etc/conf.d/NAME.yaml` without `sudo` or
an owner is enough; the container reads it through that sharing.

> **Note:** On a laptop that sleeps, agents elsewhere will report the master
> as down while the lid is closed. Run a production master on a server.
