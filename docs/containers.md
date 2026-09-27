# Installing with Docker or Podman

The same daemon that the [installer](install.md) puts on a host is published
as a container image:

```
ghcr.io/trcrdev/trcrd
```

It is built for Linux on amd64 and arm64. The `latest` tag is the current
release; every release also has its own tag (`v26.9.0` and so on), and
production installs should pin one.

Everything on this page runs with Docker Compose v2 or Podman. Where the two
differ, the Podman section says so. The files it uses are in this repository:

| File | What |
|---|---|
| [`containers/compose.yml`](../containers/compose.yml) | master, agent and PostgreSQL on one host |
| [`containers/podman/`](../containers/podman/) | quadlet units for Podman under systemd |

## Before you start

**Choose between a container and a host install per machine, not per
deployment.** A master in a container and agents installed directly on other
hosts is a normal setup, and so is the reverse.

Three things differ from a host install:

- **The master's hostname is pinned.** The licence is bound to a machine
  fingerprint, and inside a container that fingerprint is derived from the
  container's hostname. The Compose file and the quadlet set it to
  `trcr-master`. Do not remove that line, and do not change it after the
  licence is issued.
- **Agents use the host network and the `NET_RAW` capability.** Ping, batch
  ping and traceroute open raw sockets, and measurements should come from the
  host's own interfaces so latency and traceroute reflect the host rather than
  a container bridge. The master keeps `NET_RAW` too, because it runs probes
  as well. An agent that only runs TCP, HTTP, DNS or SSL probes can drop it.
- **The configuration directory belongs to the image's user.** The daemon runs
  as an unprivileged user, uid 65532. The master writes its licence into
  `/etc/trcr`, so that directory is bind-mounted read-write and must be owned
  by that uid.

The image contains only the daemon, `curl` for the health check, and `ping`
for diagnosis. There is no shell script to configure; everything is the same
`trcrd` command the host install uses.

## Docker Compose

Work in an empty directory. The steps below create a master with a PostgreSQL
results store and one agent on the same host. Replace
`trcr-master.example.com` with the name or address other hosts will use to
reach this one.

### 1. Directory and secrets

```bash
mkdir trcr && cd trcr
curl -fsSLO https://raw.githubusercontent.com/trcrdev/trcr-docs/main/containers/compose.yml
mkdir etc && sudo chown 65532:65532 etc
echo "TRCR_PG_PASSWORD=$(openssl rand -hex 16)" > .env
```

The password is read by both the database and the master through the
environment; it is never written into a configuration file.

### 2. Starter configuration

```bash
docker compose run --rm trcr-master init \
    --advertise-addr trcr-master.example.com:8444 \
    --health-listen-addr 127.0.0.1:8081 \
    --postgres-dsn 'postgres://trcr@trcr-results-pg:5432/trcr_results?sslmode=disable' \
    --postgres-password-env TRCR_PG_PASSWORD
```

This writes `etc/master.yaml`, a `conf.d/` folder with sample probes and
reference copies of every example under `etc/examples/`.

`--advertise-addr` is the address **agents** dial. It goes into the master's
certificate, so it must be how agents will reach this host, never the
container's own address. `--health-listen-addr` adds a plain `/healthz` on the
container's loopback for the health check in the Compose file.

### 3. Licence

The master does not start without a licence. The free tier is self-serve:

```bash
docker compose run --rm trcr-master license request \
    --email you@example.com --company "Your Company" --yes --wait
```

A verification link is emailed to that address. `--wait` keeps the command
running until the link is clicked, then installs `etc/license.lic` and exits.
If you already hold a licence file, skip this step and copy it to
`etc/license.lic` instead.

### 4. Start the master

```bash
docker compose up -d trcr-results-pg trcr-master
docker compose logs -f trcr-master
```

The master is healthy when the log shows `health listener ready` and
`docker compose ps` reports it `healthy`. Activate the starter probes by
copying the sample file to an active name, then edit the targets:

```bash
sudo -u '#65532' cp etc/conf.d/_samples.yaml etc/conf.d/probes.yaml
```

Changes under `etc/conf.d/` are picked up within a minute; no restart needed.

### 5. Enrol the agent

Ask the master for a single-use token. It prints a line with `--token` and
`--ca-hash` values:

```bash
docker compose exec trcr-master trcrd enroll-agent
```

Copy those two values into `.env`:

```
TRCR_ENROLL_TOKEN=TRCR-ENROLL-1....
TRCR_CA_HASH=sha256:...
```

Then start the agent:

```bash
docker compose up -d trcr-agent-1
docker compose exec trcr-master trcrd agents
```

On its first start the agent enrols against the master, writes its own
configuration into its volume and comes up. The token is single use and
expires after an hour; once the agent is listed, delete it from `.env`.
Restarts do not enrol again.

The agent in the Compose file reaches the master at `127.0.0.1:8444` because
both share the host. For an agent on **another** host, copy only the
`trcr-agent-1` service, set `TRCR_JOIN=trcr-master.example.com:8444`, and
give it its own `TRCR_NODE_ID`.

### 6. Dashboards

The master writes to PostgreSQL. Point Grafana at that database and import the
dashboards from [trcr-dashboards](https://github.com/trcrdev/trcr-dashboards),
or use any of the other [results stores](backends.md) by editing
`etc/master.yaml`.

## Podman

Podman runs the same image two ways.

**`podman compose`** with the Compose file above. Podman 4.7 and newer runs
Compose files natively through `podman compose`; older versions need
`podman-compose` from your distribution. The `:Z` labels on the bind mounts
are already in the file for SELinux hosts. Replace `docker compose` with
`podman compose` in every command above.

**Quadlet units** for a host managed with systemd. Quadlet turns `.container`,
`.network` and `.volume` files under `/etc/containers/systemd/` into systemd
services. This is the better fit for a server that should come back on its
own after a reboot.

### Master with quadlets

```bash
sudo mkdir -p /etc/containers/systemd /etc/trcr
cd /etc/containers/systemd
for f in trcr.network trcr-master-state.volume trcr-results-pg-data.volume \
         trcr-results-pg.container trcr-master.container; do
  sudo curl -fsSLo $f https://raw.githubusercontent.com/trcrdev/trcr-docs/main/containers/podman/$f
done
```

Secrets go in one root-only file that both units read:

```bash
PW=$(openssl rand -hex 16)
sudo tee /etc/trcr/master.env >/dev/null <<EOF
TRCR_PG_PASSWORD=${PW}
POSTGRES_PASSWORD=${PW}
EOF
sudo chmod 0600 /etc/trcr/master.env
sudo chown 65532:65532 /etc/trcr
```

Create the configuration and the licence with one-shot runs of the image. The
`--hostname` must match the `HostName=` in the unit:

```bash
sudo podman run --rm --hostname trcr-master -v /etc/trcr:/etc/trcr:Z \
    ghcr.io/trcrdev/trcrd:latest init \
    --advertise-addr trcr-master.example.com:8444 \
    --health-listen-addr 127.0.0.1:8081 \
    --postgres-dsn 'postgres://trcr@trcr-results-pg:5432/trcr_results?sslmode=disable' \
    --postgres-password-env TRCR_PG_PASSWORD

sudo podman run --rm --hostname trcr-master -v /etc/trcr:/etc/trcr:Z \
    ghcr.io/trcrdev/trcrd:latest license request \
    --email you@example.com --company "Your Company" --yes --wait
```

Then start it:

```bash
sudo systemctl daemon-reload
sudo systemctl start trcr-master
sudo systemctl status trcr-master
sudo podman exec trcr-master trcrd enroll-agent
```

`daemon-reload` generates the services; there is nothing to `enable`, the
units start at boot through their `[Install]` sections.

### Agent with quadlets

On the host that should measure:

```bash
sudo mkdir -p /etc/containers/systemd /etc/trcr
cd /etc/containers/systemd
for f in trcr-agent-etc.volume trcr-agent-state.volume trcr-agent.container; do
  sudo curl -fsSLo $f https://raw.githubusercontent.com/trcrdev/trcr-docs/main/containers/podman/$f
done
```

Put the values printed by `trcrd enroll-agent` on the master into a root-only
environment file:

```bash
sudo tee /etc/trcr/agent.env >/dev/null <<'EOF'
TRCR_JOIN=trcr-master.example.com:8444
TRCR_ENROLL_TOKEN=TRCR-ENROLL-1....
TRCR_CA_HASH=sha256:...
EOF
sudo chmod 0600 /etc/trcr/agent.env
sudo systemctl daemon-reload
sudo systemctl start trcr-agent
```

The agent enrols on its first start and keeps its identity in its volume.
Delete the token from `agent.env` once `trcrd agents` on the master lists the
host. The unit uses the host's own name as the agent's node id.

### Rootless Podman

The master runs rootless. Add `UserNS=keep-id:uid=65532,gid=65532` to its unit
under `[Container]`, put the units under `~/.config/containers/systemd/`, and
prepare the configuration directory with
`podman unshare chown 65532:65532 /path/to/etc` instead of `sudo chown`.

Agents that run traceroute should not run rootless. The user-mode network
stack rootless Podman uses does not return the TTL-exceeded replies that
traceroute depends on, so paths come back empty while ping keeps working. Run
those agents as root, or [install the agent on the host](agents.md).

## Upgrading

Change the tag in `.env` (`TRCR_IMAGE=ghcr.io/trcrdev/trcrd:<release>`) or in
the quadlet's `Image=` line, then `docker compose up -d` or
`systemctl daemon-reload && systemctl restart trcr-master`. Configuration,
state and licence live in the mounted directory and the volumes, so a new
image picks them up as they are. The quadlets carry `AutoUpdate=registry`, so
`podman auto-update` (or its timer) also moves a pinned `latest` forward.

## Checking

```bash
docker compose exec trcr-master trcrd agents      # which agents report in
docker compose exec trcr-master trcrd probes      # which probes run where
docker compose exec trcr-master trcrd run ping 1.1.1.1
curl -s http://127.0.0.1:9101/metrics | head     # Prometheus metrics on the host
```

With Podman, replace `docker compose exec trcr-master` with
`sudo podman exec trcr-master`. The rest of [Operations](operations.md)
applies as it does to a host install; where it says `systemctl restart
trcrd-master`, use `docker compose restart trcr-master` or
`systemctl restart trcr-master`.
