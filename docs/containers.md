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
trcr-agent-1  up      24s ago    7       in 364d
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

### What the first start did

`trcr-init` generated the Postgres and Grafana passwords into a volume only
these containers mount, wrote `etc/master.yaml` and the starter probes in
`etc/conf.d/starter.yaml`, installed your license, and copied the datasource
and dashboards into Grafana's volumes. `trcr-enroll` created a one-hour,
single-use token for the local agent and handed it over through a volume,
so the token is never in `.env`. The agent enrolled with it on its first
start and keeps its identity in its own volumes, so restarts and
`docker compose up -d --force-recreate` don't enroll again.

Everything under `etc/` belongs to uid 65532, the user the daemon runs as,
and is yours to edit. Reference copies of every configuration file are in
`etc/examples/`.

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
reachable from the agent.

An agent host that should run the daemon directly instead of a container
uses the join command that `trcrd enroll-agent` prints without `--env`; see
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
`docker compose`. The `:z` labels on the bind mounts are already in the file
for SELinux hosts.

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
on their own because every unit requires them. There is nothing to
`enable`: the units start at boot through their `[Install]` sections, and
the one-shot units run again at every boot and find nothing left to do.
Check the same way as with Compose:

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
keeping `NET_RAW` and nothing else. The daemon itself never runs as root,
and `no-new-privileges` is on. Podman hands the capability to the image's
user directly, so the quadlets run as uid 65532 from the start. An agent
that only runs TCP, HTTP, DNS or SSL probes can drop `NET_RAW` too.

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

**Changing probes.** Edit or add files under `etc/conf.d/`, then restart the
master; it reads its configuration once at startup, so there is no hot
reload:

```bash
docker compose restart trcr-master
docker compose exec trcr-master trcrd probes
```

With quadlets: `sudo systemctl restart trcr-master`. A file copied in as
root is fine; the setup job hands everything under `etc/` to uid 65532 on
the next `up`, and `trcrd validate` inside the container tells you about a
file it can't read.

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

**Upgrading.** Put `TRCR_IMAGE=ghcr.io/trcrdev/trcrd:<release>` in `.env`
and run `docker compose up -d`; with quadlets, change the `Image=` line in
the `trcr-*.container` files, then `sudo systemctl daemon-reload` and
`sudo systemctl restart trcr-init trcr-master trcr-enroll trcr-agent`.
Configuration, state and license live in `etc/` and the volumes, so a new
image picks them up as they are, and the setup job refreshes the Grafana
dashboards to the ones shipped with that release.

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
the host stays; keep `etc/license.lic` if you plan to start again.

## macOS and Docker Desktop

The stack runs on Docker Desktop, with two differences. Host networking
puts the agent in Docker Desktop's Linux VM, not on your Mac, so its
latency and traceroute are measured from that VM (it has its own address,
usually `192.168.65.x`); fine for trying TRCR, not for measuring the Mac's
own connection. And the bind-mounted `etc/` shows up owned by your macOS
user, not uid 65532; that is Docker Desktop's file sharing, and nothing
needs changing. There is no `sudo chown` step on macOS.

> **Note:** On a laptop that sleeps, agents elsewhere will report the master
> as down while the lid is closed. Run a production master on a server.
