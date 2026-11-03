# Install TRCR

If this is your first time, start here. One command sets up a complete,
working TRCR on a single Linux host: the master, an agent, a PostgreSQL
database for your results and Grafana with the TRCR dashboards. The install
itself takes a few minutes, and you'll see your first graphs a minute or two
after you click the link in the license email.

Already know what you want? Skip to
[A master with a database you already run](#a-master-with-a-database-you-already-run),
[Other ways to install](#other-ways-to-install), or
[Containers](containers.md) if you'd rather use Docker or Podman.

## Before you start

- A Linux host you can use `sudo` on: Debian, Ubuntu, Fedora, or RHEL and its
  relatives (CentOS Stream, Rocky, Alma, Oracle Linux). Give it at least 2 GB
  of memory, because PostgreSQL and Grafana run there too.
- An email address you can open now. The free license is confirmed by a link
  we email you, and the link works for 24 hours. If you already have a license
  file, you won't need the email.
- Outbound HTTPS from the host to `trcr.dev` and `api.trcr.dev`. The host also
  downloads PostgreSQL from your distribution's package mirrors and Grafana
  from Grafana's own package repository.

## Install everything on one host

The `--email` and `--company` options ask for your free license as part of the
install, so there's nothing left to do afterwards except click the link. Run
this on the host:

```bash
curl -fsSL https://trcr.dev/install/install.sh | sh -s -- --all-in-one \
  --email you@example.com --company "Your Company"
```

Already have a license file? Use `--license /path/to/license.lic` instead of
`--email` and `--company`, and everything starts in the same run.

Options go after `sh -s --`. Without it, `sh` keeps the options for itself and
the installer never sees them.

If you leave out both `--email` and `--license`, the installer asks for your
email address on the terminal. Press Enter to skip that, and it tells you the
two commands to run later.

## What you'll see

Installing the Grafana package is the slow part. It can take a few minutes, and
the installer says so before it starts. You'll see something like this
(shortened):

```
==> Installing TRCR v26.11.0 for linux-amd64
==> Signature checked: this download is the release TRCR signed.
==> Installed /usr/local/bin/trcrd (trcrd v26.11.0 ...)
...
==> PostgreSQL is ready: database trcr_results, user trcr, password in /etc/trcr/postgres.env.
...
==> Added 7 starter probes so you see data straight away (/etc/trcr/conf.d/standalone.yaml).
==> Installing Grafana and the TRCR dashboards (apt-get). The Grafana package is large, so this can take a few minutes.
...
==> Requesting your free license for you@example.com ...
...
==> Almost done. One click left.
    We have sent a verification link to you@example.com.
    Open it whenever suits you. You can close this terminal.
    About 15 seconds after you click, this host starts the master,
    enrolls its local agent and starts recording.
```

Three lines matter:

- `Signature checked` means the download is the release TRCR signed. If the
  check fails, the installer stops before it installs anything.
- `PostgreSQL is ready` tells you where your results will be kept.
- The summary at the end, under `What is on this host now:`, shows how to reach
  Grafana and the admin password. The password is shown once here, so copy it
  now. It's also kept in `/etc/trcr/grafana-admin.env`.

Every run ends with a line pointing at the full log of that run,
`/var/log/trcr-install.log`. If anything goes wrong, that's the first file to
read.

## Click the link in your email

The master needs a license before it can start. Until you click the link,
nothing is running yet, and that's expected.

You don't need to wait at the terminal. The installer has set up a small
service, `trcr-firstboot`, that checks for your license every 15 seconds. When
you click the link, whether that's in a minute or tomorrow, it starts the
master, enrolls the local agent and waits for the first results. Then it
switches itself off.

To follow along, run this on the host:

```bash
sudo journalctl -fu trcr-firstboot
```

You'll see something like this once you've clicked:

```
==> Starting the master ...
==> Enrolling a local agent ...
enrolled as web-01-local
...
==> Waiting for the first results (up to 90 seconds) ...
    Data is flowing: ping http dns tcp

You are all set. The master and a local agent are running and recording.

    Dashboards with data now      Ping, HTTP, DNS, Overview, Per-Agent Operations, SLO Landing
    Within the hour               SSL Expiry, Cert Fleet (1h probe), Traceroute, Map, Alive
    Once a second agent joins     Agent-to-Agent, Agent Mesh, Cross-Vantage RTT Divergence
    Need their own probes         Throughput, BGP, DNS Propagation (see /etc/trcr/examples/)
```

When you see `You are all set`, you're done. The list tells you which
dashboards fill straight away and which stay empty for now. An empty
Traceroute or Agent Mesh panel in the first few minutes is normal.

The local agent is named after the host, with `-local` on the end.

`trcr-firstboot` exists only when you installed with `--email`. With
`--license`, the same output appears in your terminal at the end of the
install instead.

To finish by hand at any time, run this on the host. It's safe to run as often
as you like:

```bash
sudo /etc/trcr/finish-setup.sh
```

It claims a waiting license, starts whatever isn't running, enrolls the local
agent if there isn't one, and shows the Grafana password again.

## Open your dashboards

Grafana only listens on the host itself (127.0.0.1), so nobody else can reach
it. To open it from your own computer, start an SSH tunnel to the host:

```bash
ssh -L 3000:127.0.0.1:3000 <your-trcr-host>
```

Then open `http://localhost:3000` in your browser and sign in as `admin` with
the password from the install summary. If you've lost it, it's in
`/etc/trcr/grafana-admin.env`, and `sudo /etc/trcr/finish-setup.sh` shows it
again.

The dashboards are in the **TRCR** folder. Open **SLO Landing** first: it
shows at a glance whether your probes are succeeding. For what the other
dashboards show, see [Dashboards](dashboards.md).

To reach Grafana directly instead of through a tunnel, run the installer again
with `--open-grafana`. That makes Grafana listen on every interface and opens
port 3000.

## Add your first remote agent

This takes a couple of minutes, and it's where TRCR starts to pay off: with a
second agent you can see your network from two places, and TRCR starts
measuring between the agents too.

Before you start, open ports 8443 and 8444 on the master. An agent uses 8444
once, to enroll, and 8443 for everything after that. See
[Ports and firewalls](#ports-and-firewalls).

To get the command that adds an agent, run this on the **master**:

```bash
sudo trcrd enroll-agent
```

It prints one command with a single-use token in it. Run that command on the
**agent** host. If you installed with `--license`, the install summary already
printed one, and it works for an hour.

On the agent, you'll see:

```
==> Enrolling with the master at 192.0.2.10:8444 ...
==> This host is enrolled and the agent is running. Nothing else to do here.
```

To check, run `sudo trcrd agents` on the **master**. The new agent should show
`up` within a minute.

> **Note:** The address after `--join` is the master's `advertise_addr`, which
> the installer guessed from the master's outbound IP address. On a cloud host
> that's often a private address. If your agent reaches the master by another
> name or address, use that instead, and set `advertise_addr` to match. See
> [Configuration](configuration.md#advertise_addr-is-required-for-remote-agents).

If the master can reach the agent but not the other way round, use a pairing
code instead. [Agents](agents.md) covers both ways.

The free license allows five agents, and the local agent counts as one of
them. See [Licensing](licensing.md).

## If something doesn't look right

- The installer ignored your options: put `sh -s --` before them, as in the
  commands above.
- The install finished but nothing is running: you haven't clicked the link in
  the license email yet. See [Click the link in your email](#click-the-link-in-your-email).
- The installer stopped with a signature or OpenSSL error: see
  [Troubleshooting](troubleshooting.md#the-installer-stops-with-a-signature-or-openssl-error).
- An agent enrolled but never reports in: port 8443 is closed, or
  `advertise_addr` is wrong. See
  [Troubleshooting](troubleshooting.md#an-agent-is-stuck-at-never-seen).

For anything else, read `/var/log/trcr-install.log`, then see
[Troubleshooting](troubleshooting.md).

## A master with a database you already run

If you already run PostgreSQL, TRCR can keep its results there. You don't get
the local database or Grafana; point your own Grafana at the database instead
(see [Dashboards](dashboards.md#with-your-own-grafana)).

First, create an empty database and a user that owns it. TRCR creates and
maintains its own tables inside that database, so there's no schema to load.

Put the database password on the first line of a file that only you can read.
Then run this on the master host:

```bash
curl -fsSL https://trcr.dev/install/install.sh | sh -s -- \
  --postgres-dsn "postgres://trcr@db.example.com:5432/trcr_results?sslmode=require" \
  --postgres-password-file pg-password.txt
```

The installer copies the password into `/etc/trcr/postgres.env`, which only
root and the `trcr` group can read, and hands it to the master through
systemd. It never goes into `master.yaml`, and you can delete your file
afterwards. If `psql` is installed on the host, the installer checks it can
connect, and stops if it can't.

If the password is already in an exported environment variable, use
`--postgres-password-env <NAME>` instead of `--postgres-password-file`. Either
way, the password can't contain a quote mark or a backslash.

The installer then prints the steps that are left. Here they are with the
reason for each:

1. If agents on other hosts will connect, set `master.advertise_addr` in
   `/etc/trcr/master.yaml` to a name or address they can reach. See
   [Configuration](configuration.md#advertise_addr-is-required-for-remote-agents).
2. Give the master something to measure. To start from the sample probes,
   copy them to an active name, then edit the targets:

   ```bash
   sudo install -o root -g trcr -m 0640 /etc/trcr/conf.d/_samples.yaml /etc/trcr/conf.d/probes.yaml
   ```

   Files whose names start with `_` are ignored, which is why the samples do
   nothing until you copy them. Use `install` rather than `cp`, so the master,
   which runs as the `trcr` user, can read the copy.
3. Check the configuration. This catches typos and files the master can't
   read:

   ```bash
   sudo trcrd validate --config /etc/trcr/master.yaml
   ```

4. Get your free license. We email you a link, and the command finishes once
   you click it:

   ```bash
   sudo trcrd license request --email you@example.com --company "Your Company" --wait
   ```

   Already have a license file? Copy it to `/etc/trcr/license.lic` instead.
5. Start everything:

   ```bash
   sudo /etc/trcr/finish-setup.sh
   ```

   This starts the master, enrolls a local agent and prints the command for
   adding more agents.

You can also add `--license /path/to/license.lic` to the install command. The
master then starts straight away, before you've added any probes. Add them
afterwards, validate, and restart the master with
`sudo systemctl restart trcrd-master`.

To use a store other than PostgreSQL, install with no options (see below) and
follow [Storing results](backends.md).

---

## Reference: installer options and other ways to install

### Other ways to install

| You want | Run |
|---|---|
| Everything on one host (master, agent, PostgreSQL, Grafana) | `curl -fsSL https://trcr.dev/install/install.sh \| sh -s -- --all-in-one` |
| The same, without Grafana | `curl -fsSL https://trcr.dev/install/install.sh \| sh -s -- --datastore-only` |
| A master that uses your own PostgreSQL | [A master with a database you already run](#a-master-with-a-database-you-already-run) |
| A master you configure yourself | `curl -fsSL https://trcr.dev/install/install.sh \| sh` |
| Another host to measure from | [Agents](agents.md) |
| Docker or Podman | [Containers](containers.md) |
| Only the `trcrd` program | [Install only the binary](#install-only-the-binary) |
| macOS or Windows | See [Getting started](getting-started.md#supported-platforms) |

With no options, the installer installs `trcrd`, writes a starter
configuration in `/etc/trcr` and sets up the master's service without starting
it. The starter `master.yaml` sends results to the journal only, so the
installer ends with the five steps you still need: choose a results store,
copy the sample probes, validate, get a license and start. They're the same
steps as in
[A master with a database you already run](#a-master-with-a-database-you-already-run),
plus choosing the store. See [Storing results](backends.md).

### Installer options

To see every option on the command line:

```bash
curl -fsSL https://trcr.dev/install/install.sh | sh -s -- --help
```

Setting up a master:

| Option | What it does |
|---|---|
| `--all-in-one` | Everything on this host: master, local agent, PostgreSQL, Grafana and the dashboards. `--aio` and `--standalone` mean the same. |
| `--datastore-only` | The same, without Grafana. |
| `--email ADDR` and `--company NAME` | Request a free license. Give both. Once you click the emailed link, the host finishes setting itself up. |
| `--license FILE` | Use a license file you already have. |
| `--postgres-dsn URL` | Store results in a PostgreSQL database you already run. The URL starts with `postgres://` or `postgresql://`. Needs exactly one of the next two options. Can't be combined with `--all-in-one`, `--datastore-only`, `--timescaledb` or the agent options. |
| `--postgres-password-file FILE` | Read the database password from the first line of this file. |
| `--postgres-password-env VAR` | Read the database password from this environment variable. |
| `--timescaledb` | With `--all-in-one`: also install the TimescaleDB extension and use it for your results. If there's no package for your PostgreSQL version, the installer carries on with standard partitioning and tells you. The PostgreSQL 13 that Enterprise Linux 9 ships is too old for current TimescaleDB. |
| `--open-firewall` | Open ports 8443 and 8444 in firewalld or ufw. Without it, the installer prints the commands instead. |
| `--open-grafana` | Let other machines reach Grafana on port 3000. Without it, use an SSH tunnel. |

Adding an agent (no email or license needed):

| Option | What it does |
|---|---|
| `--agent` | Install an agent that waits for the master to connect, and print a pairing code and fingerprint. `--agent-only` means the same. See [Agents](agents.md#pair-an-agent-the-master-can-reach). |
| `--accept-from IP[,IP]` | With `--agent`: only accept the master from these addresses. |
| `--bootstrap-port N` | With `--agent`: the port the master connects to (8445 by default). |
| `--node-id NAME` | The agent's name. It defaults to the host's name. |
| `--join HOST:PORT --token TOKEN --ca-hash sha256:HEX` | Connect out to the master and enroll. Don't type these yourself: paste the whole command that `sudo trcrd enroll-agent` prints on the master. |

Other options:

| Option | What it does |
|---|---|
| `--dashboards-only` | Add Grafana and the dashboards to a host you installed earlier with `--datastore-only` or `--no-dashboards`. |
| `--no-dashboards` | Skip Grafana. |
| `--dry-run`, `-n` | Show what would change on this host, without changing anything. |
| `-h`, `--help` | Show the options. |

A dry run is a good way to see the plan before you commit to it. It names the
package tool it would use, whether a license is still needed, and what it would
write:

```bash
curl -fsSL https://trcr.dev/install/install.sh | sh -s -- --all-in-one --dry-run
```

### Environment variables

These go between the pipe and `sh`:

| Variable | What it does | Example |
|---|---|---|
| `TRCR_INSTALL_DIR` | Install `trcrd` somewhere other than `/usr/local/bin`. | `curl -fsSL https://trcr.dev/install/install.sh \| TRCR_INSTALL_DIR=/opt/trcr/bin sh` |
| `TRCR_SKIP_SETUP=1` | Install or upgrade the binary only. Nothing in `/etc/trcr` is touched. | `curl -fsSL https://trcr.dev/install/install.sh \| TRCR_SKIP_SETUP=1 sh` |
| `TRCR_FORCE=1` | Download and reinstall the same version, even if it's already up to date. | `curl -fsSL https://trcr.dev/install/install.sh \| TRCR_FORCE=1 sh` |

### What the installer changes on your host

Every Linux install:

- Installs `trcrd` to `/usr/local/bin/trcrd`, owned by root, mode `0755`. On
  systems where `sudo` doesn't look in `/usr/local/bin`, such as RHEL and its
  relatives, it also links `/usr/bin/trcrd` to it, so `sudo trcrd` works. The
  uninstaller removes that link.
- Creates the `trcr` user, which the TRCR services run as.
- Writes `/etc/trcr/master.yaml`, the example probes in
  `/etc/trcr/conf.d/_samples.yaml`, and annotated reference copies of every
  example configuration in `/etc/trcr/examples/`. Existing files are never
  overwritten. The examples are refreshed on every upgrade.
- Installs the `trcrd-master` service and `/etc/trcr/finish-setup.sh`, the
  script that starts the master and enrolls a local agent once a license is in
  place.
- Writes a log of the run to `/var/log/trcr-install.log`.

The all-in-one install also:

- Installs PostgreSQL from your distribution's packages, with a `trcr` user and
  a `trcr_results` database that accept connections from this host only. The
  password is generated and kept in `/etc/trcr/postgres.env`, readable by root
  and the `trcr` group only, and reaches the master through systemd.
- Writes seven starter probes to `/etc/trcr/conf.d/standalone.yaml`. They
  measure this host's connection to the internet, so you see data straight
  away. Change them whenever you like; a re-install never rewrites the file.
- Installs Grafana from Grafana's package repository, connects it to the
  database and loads the TRCR dashboards. Grafana listens on 127.0.0.1 only,
  sign-up and anonymous access are off, and the admin password is random, not
  `admin`. It's kept in `/etc/trcr/grafana-admin.env`, and running the
  installer again never changes it.
- Enrolls a local agent on the host and starts it, once the license is in
  place.
- With `--email`, adds the `trcr-firstboot` service, which waits for your
  license and switches itself off when it's done.

The installer changes the host firewall only when you give `--open-firewall`.

You can run the installer as often as you like. Running it again upgrades
`trcrd` and leaves your configuration, license and data alone.

### How the installer protects you

Before the installer trusts anything it downloads, it checks a signature. The
release's list of checksums is signed by TRCR, and the public key that checks
it is built into the installer. A bad or missing signature stops the install.
Only then does the installer download `trcrd` and compare it with the checksum
in that verified list.

If your connection drops during the download, nothing runs, because the shell
reads the whole script before it starts.

To read the script before running it, download it first:

```bash
curl -fsSLO https://trcr.dev/install/install.sh
less install.sh
sh install.sh --all-in-one --email you@example.com --company "Your Company"
```

### Ports and firewalls

The master listens on two ports that agents on other hosts need to reach:

| Port | What it's for |
|---|---|
| 8443/tcp | Agents fetch their probes and send results. Needed all the time. |
| 8444/tcp | Enrollment. Needed while you add agents. |

Open both. If only 8444 is open, an agent enrolls without complaint and then
never reports in. That's hard to spot, so check both now. An all-in-one host
with no remote agents doesn't need any ports open.

The installer looks for firewalld and ufw. If one is blocking the ports, it
prints the commands to open them, for example:

```bash
sudo firewall-cmd --permanent --add-port=8443/tcp
sudo firewall-cmd --permanent --add-port=8444/tcp
sudo firewall-cmd --reload
```

With `--open-firewall`, it runs them for you. It never opens Grafana's port;
that's what `--open-grafana` is for. If the host has no firewall, the installer
says `No host firewall found; 8443 and 8444 are open on this host.`

Cloud providers usually have a second firewall outside the host, such as
security groups or network ACLs. Open the same ports there.

For every port TRCR uses, see [Security](security.md#ports).

### Install only the binary

To install or upgrade `trcrd` without touching any configuration:

```bash
curl -fsSL https://trcr.dev/install/install.sh | TRCR_SKIP_SETUP=1 sh
```

To download a binary directly, use one of these addresses:

```
https://trcr.dev/download/latest/linux-amd64
https://trcr.dev/download/latest/linux-arm64
https://trcr.dev/download/latest/linux-arm        (32-bit Raspberry Pi OS)
https://trcr.dev/download/latest/darwin-amd64
https://trcr.dev/download/latest/darwin-arm64
https://trcr.dev/download/latest/windows-amd64
https://trcr.dev/download/latest/SHA256SUMS
```

[Security](security.md#verifying-downloads) shows how to check a binary you
downloaded by hand.

### Check the install

These commands tell you whether everything is working. Run them on the master:

```bash
trcrd version
sudo systemctl status trcrd-master
sudo trcrd agents
sudo trcrd probes
trcrd run ping 1.1.1.1
```

- `systemctl status` should say `active (running)`.
- `trcrd agents` should list every agent as `up`:

  ```
  NODE_ID       STATUS  LAST SEEN  PROBES  CERT EXPIRES
  web-01-local  up      12s ago    7       in 364d

  1 agent(s); down-after 1m30s
  ```

  `PROBES` is how many probes the master is serving to that agent.
- `trcrd probes` lists the probes and where each one runs. It reads the files
  on disk, so a probe you've just added shows up here before the master has
  loaded it. The master only reads its configuration when it starts, so
  restart it after a change: `sudo systemctl restart trcrd-master`.
- `trcrd run` runs one probe straight away and prints the result.

A master can be running without saving anything. If it can't open your
results store, it starts anyway and logs that results are being discarded. To
check, search the log:

```bash
sudo journalctl -u trcrd-master | grep -i discard
```

No output means nothing is being thrown away. `finish-setup.sh` runs this check
for you. To learn what else belongs in a healthy log, see
[Operations](operations.md#what-a-healthy-master-log-looks-like).

If you're logged in as root on a host without `sudo`, leave `sudo` off these
commands. The installer does the same in the commands it prints.

### Upgrade or uninstall

See [Operations](operations.md#upgrade-trcr) and
[Operations](operations.md#uninstall-trcr).
