# Installation

All installs use one script. It works out your platform, downloads the matching
`trcrd` binary, verifies it, and installs it to `/usr/local/bin/trcrd`.

```bash
curl -fsSL https://trcr.dev/install/install.sh | sh
```

To pass options through the pipe, add `sh -s --` before them, as the examples
below do.

Pick the install that matches what you want.

| You want | Use |
|---|---|
| One host that does everything, with a database and dashboards | [All-in-one](#all-in-one-recommended-for-a-first-install) |
| A master that writes to a database you already run | [Master with your own database](#master-with-your-own-database) |
| Another host to measure from | [An agent](agents.md) |

## What the installer does

1. Downloads the list of checksums for one specific release, and its signature.
2. Verifies the signature with the public key built into the script **before**
   trusting any checksum. A bad or missing signature stops the install.
3. Downloads the binary, checks it against the verified checksum, and installs
   it as `root:root`, mode `0755`.
4. On Linux, creates the `trcr` service account and runs `trcrd init`, which
   creates `/etc/trcr` with a starter `master.yaml`, a `conf.d/` folder with
   sample probes, and reference copies of every example config under
   `/etc/trcr/examples/`.

The whole script is read before anything runs, so a connection that drops
halfway executes nothing. Running the installer again upgrades the binary in
place and never overwrites your configuration.

## All-in-one (recommended for a first install)

Linux only. This gives you a master, a local agent, PostgreSQL, Grafana with
the ready-made dashboards, three starter probes and a free licence.

```bash
curl -fsSL https://trcr.dev/install/install.sh | sh -s -- --all-in-one \
  --email you@example.com --company "Your Company"
```

If you already hold a licence file, give it instead of an email address:

```bash
curl -fsSL https://trcr.dev/install/install.sh | sh -s -- --all-in-one \
  --license /path/to/license.lic
```

With neither option, the installer asks you on the terminal. If there is no
terminal, it prints the two commands that remain.

### What happens next

**The master will not start without a licence**, and an agent cannot enrol
until the master is running.

- With `--license`, everything starts in the same run.
- With `--email` and `--company`, the installer requests a free licence and
  **exits**. It does not wait for you to open your inbox. A background service,
  `trcr-firstboot`, checks every 15 seconds for the licence. When you open the
  verification link, whether in a minute or tomorrow, it finishes the setup by
  itself: it starts the master, enrols the local agent, and stops watching.
  The link is valid for 24 hours.

Watch it finish:

```bash
sudo journalctl -fu trcr-firstboot
```

Or finish by hand at any time. This is safe to run as often as you like:

```bash
sudo /etc/trcr/finish-setup.sh
```

It claims a pending licence, starts whatever is not running, enrols the local
agent if needed, and prints the command for adding more agents.

### What the all-in-one install sets up

- **PostgreSQL**, from your distribution's packages, with a `trcr` user and a
  `trcr_results` database. TRCR creates what it needs in that database; there
  is no migration step. The password is generated, stored in
  `/etc/trcr/postgres.env` (readable by root and the `trcr` group only), and
  passed to the service through systemd. It is never written into
  `master.yaml`.
- **`master.yaml`** pointing at that database as its only results store.
- **`conf.d/standalone.yaml`** with three probes against real targets, so you
  see data straight away.
- **Grafana**, with the datasource connected and the TRCR dashboards loaded.
- **A local agent**, enrolled over the loopback address. The master never runs
  probes itself, so a single host needs this agent to collect anything.

### Options

| Option | Effect |
|---|---|
| `--all-in-one` | Master, local agent, PostgreSQL and Grafana. |
| `--datastore-only` | As above, without Grafana. |
| `--timescaledb` | Also install the TimescaleDB extension and use it for the results tables. If no package exists for your PostgreSQL version, the installer falls back to standard partitioning and tells you. The stock PostgreSQL 13 on Enterprise Linux 9 is too old for current TimescaleDB. |
| `--email`, `--company` | Request a free licence. |
| `--license FILE` | Use a licence file you already hold. |
| `--open-firewall` | Open the TRCR ports in firewalld or ufw. Without it the installer only prints the commands. |
| `--open-grafana` | Make Grafana listen on every interface and open port 3000. |

### Reaching Grafana

Grafana listens on `127.0.0.1` only, unless you gave `--open-grafana`. From
your own machine, open a tunnel:

```bash
ssh -L 3000:127.0.0.1:3000 <your-trcr-host>
```

Then open `http://localhost:3000`. The dashboards are in the **TRCR** folder.

Grafana is installed with a random 24-character admin password, not
`admin/admin`. Sign-up and anonymous access are off. The password is printed
once in the install summary and kept in `/etc/trcr/grafana-admin.env`.
`sudo /etc/trcr/finish-setup.sh` shows it again. Running the installer again
never changes it.

If you had already edited `grafana.ini` by hand, the installer leaves it alone
and prints the settings to add.

## Master with your own database

```bash
curl -fsSL https://trcr.dev/install/install.sh | sh
```

Then:

1. Edit `/etc/trcr/master.yaml`. It contains a commented example for every
   kind of results store. Uncomment one and fill it in. See
   [Storing results](backends.md).
2. If agents on other hosts will connect, set `master.advertise_addr`. See
   [Configuration](configuration.md#advertise_addr-is-required-for-remote-agents).
   `trcrd init` fills it in from the host's outbound IP address; check that the
   value is one your agents can reach.
3. Copy the sample probes to an active name and edit the targets:

   ```bash
   sudo cp /etc/trcr/conf.d/_samples.yaml /etc/trcr/conf.d/probes.yaml
   ```

   Files whose names start with `_` are ignored, which is why the samples do
   nothing until you copy them.
4. Check the configuration:

   ```bash
   sudo trcrd validate --config /etc/trcr/master.yaml
   ```

5. Get a licence and start everything:

   ```bash
   sudo trcrd license request --email you@example.com --company "Your Company" --wait
   sudo /etc/trcr/finish-setup.sh
   ```

## Firewall

The master listens on two TCP ports that agents on other hosts must reach:

| Port | Use |
|---|---|
| 8443 | Agents fetch their probes and send results. Needed all the time. |
| 8444 | Enrolment. Needed while you add agents. |

**Open both.** With only 8444 open, an agent enrols and then fails every call
after that.

When firewalld or ufw is active, the installer prints the commands to run, for
example:

```bash
sudo firewall-cmd --permanent --add-port=8443/tcp
sudo firewall-cmd --permanent --add-port=8444/tcp
sudo firewall-cmd --reload
```

`--open-firewall` runs them for you. It never opens Grafana's port; that is
what `--open-grafana` is for. An all-in-one host with no remote agents needs no
ports opened at all.

Cloud providers usually have a second firewall (security groups, network ACLs)
outside the host. Open the same ports there.

## Installing only the binary

```bash
curl -fsSL https://trcr.dev/install/install.sh | TRCR_SKIP_SETUP=1 sh
```

Set `TRCR_INSTALL_DIR` to install somewhere other than `/usr/local/bin`.

Direct downloads follow one pattern:

```
https://trcr.dev/download/latest/linux-amd64
https://trcr.dev/download/latest/linux-arm64
https://trcr.dev/download/latest/linux-arm        (32-bit Raspberry Pi OS)
https://trcr.dev/download/latest/darwin-amd64
https://trcr.dev/download/latest/darwin-arm64
https://trcr.dev/download/latest/windows-amd64
https://trcr.dev/download/latest/SHA256SUMS
```

## Checking the install

```bash
trcrd version                      # which release is installed
sudo systemctl status trcrd-master # is the master running
sudo trcrd agents                  # which agents are enrolled and reporting
sudo trcrd probes                  # which probes are configured, and where they run
trcrd run ping 1.1.1.1             # run one probe now and print the result
```

A master that is running is not always a master that is storing data. If the
results store is misconfigured, the master still starts and discards results,
with a warning in its log:

```bash
sudo journalctl -u trcrd-master | grep -i discard
```

`finish-setup.sh` makes this check for you.

## Upgrading and uninstalling

See [Operations](operations.md#upgrading).
