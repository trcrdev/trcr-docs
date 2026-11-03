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

- A Linux host you can use `sudo` on, or log in to as root: Debian, Ubuntu,
  Fedora, or RHEL and its relatives (CentOS Stream, Rocky, Alma, Oracle
  Linux). Give it at least 2 GB of memory, because PostgreSQL and Grafana run
  there too. As root on a host without `sudo`, run the same commands; the
  installer leaves `sudo` off the commands it prints.
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

If you're not root, `sudo` may ask for your password first, before the
installer prints anything.

Options go after `sh -s --`. Without it, `sh` keeps the options for itself and
the installer never sees them.

If you leave out both `--email` and `--license`, the installer asks for your
email address on the terminal. Press Enter to skip that, and it tells you the
two commands to run later.

## What you'll see

Installing the Grafana package is the slow part. It can take a few minutes, and
the installer says so before it starts. Grafana's first start can take another
minute or two, and the installer says so too. You'll see something like this
(shortened):

```
==> Installing TRCR v26.11.0 for linux-amd64
==> Signature checked: this download is the release TRCR signed.
==> Installed /usr/local/bin/trcrd (trcrd v26.11.0)
...
==> PostgreSQL is ready: database trcr_results, user trcr, password in /etc/trcr/postgres.env.
...
==> Added 7 starter probes so you see data straight away (/etc/trcr/conf.d/standalone.yaml).
==> Installing Grafana and the TRCR dashboards (apt-get). The Grafana package is large, so this can take a few minutes.
...
==> Starting Grafana (its first start can take a minute or two) ...
...
==> Requesting your free license for you@example.com ...
...
==> Almost done. One click left.
    We have sent a verification link to you@example.com.
    Open it whenever suits you. You can close this terminal.
    About 15 seconds after you click, this host starts the master,
    enrolls its local agent and starts recording.
...
  What is on this host now:
    PostgreSQL   database trcr_results on this host only (127.0.0.1:5432); password in /etc/trcr/postgres.env
    Grafana      Only reachable from this host. From your own computer, run:
                   ssh -L 3000:127.0.0.1:3000 <this-host>
                 then open http://localhost:3000 and look in the TRCR folder.
                 Sign in as admin / <password>  (also in /etc/trcr/grafana-admin.env)
                 To reach it directly instead, run the installer again with --open-grafana.
    Probes       7 starter probes in /etc/trcr/conf.d/standalone.yaml; change them whenever you like
```

Three things matter:

- `Signature checked` means the download is the release TRCR signed. If the
  check fails, the installer stops before it installs anything.
- `PostgreSQL is ready` tells you where your results will be kept.
- The Grafana address and admin password. With `--email`, they're under
  `What is on this host now:` at the end, as above. With `--license`, that
  block lists only PostgreSQL and the probes. The password is on the
  `Grafana:` line a little higher up, just before the command for adding
  another host. Copy it now. It's also kept in `/etc/trcr/grafana-admin.env`.

On a small host, Grafana may still be starting when the install ends. The
installer then says `Grafana is still starting; it will be ready in a minute or two.`,
and says `Still starting; it will be ready in a minute or two.` again under
the Grafana address at the end. Give it that long before you open it.

Where the `ssh -L` command says `<this-host>`, put in the name or address you
use to reach the host over SSH. The summary fills in the host's own address
only when it's a public one; a private address is often not the one you'd
connect to.

Every run ends with a line pointing at the full log of that run,
`/var/log/trcr-install.log`. If anything goes wrong, that's the first file to
read. Each run's part of it ends with `=== install.sh exit status N ===`,
where 0 means the run finished without an error.

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
    Data is flowing: ping http dns tcp ssl_expiry traceroute alive

You are all set. The master and a local agent are running and recording.

    Dashboards with data now      Ping, HTTP, DNS, SSL Expiry, Cert Fleet, Traceroute, Map, Alive, Overview, Per-Agent Operations, SLO Landing
    Once a second agent joins     Agent-to-Agent, Agent Mesh, Cross-Vantage RTT Divergence
    Need their own probes         Throughput, BGP, DNS Propagation (see /etc/trcr/examples/)
```

When you see `You are all set`, you're done. It appears only when the master
opened your results store, probes are configured and the local agent is
running.

The wait ends about ten seconds after the first result arrives, so your list
may be shorter than this. It's built from the results that have arrived: a
probe type that hasn't reported yet is listed under `Within the hour` instead,
with `(as those probes first run)`. Once a second agent is enrolled, the
agent-to-agent dashboards appear under `Dashboards with data now`, or under
`Within minutes` with `(as the agent-to-agent probes first run)` until their
first results arrive. An empty Traceroute or Agent Mesh panel in the first few
minutes is normal.

If something is missing, you'll see one of these instead:

- `Nothing is measured yet: no probes are configured.` The host is fine, but
  there's nothing to measure. It prints the three commands that copy the
  sample probes, check them and restart the master.
- `The master did not start.` The setup waits up to 45 seconds for the master
  before it says this. The next line is the master's own error. If the
  `trcr` user can't read a file, such as a license copied with `cp`, it also
  prints the `chgrp` and `chmod` commands that fix it.
- `The master is running, but it is not saving results anywhere, so they are
  being thrown away.` The `Its log says:` line quotes the error from your
  results store, for example a wrong database password, and the lines after it
  say where to fix it.
- `The master and a local agent are running, but the master has not said which
  results store it opened, so whether results are being saved is not known
  yet.` This appears only on a host without `psql`, where the setup relies on
  the master's log instead of looking for rows. It gives a master that has
  just started up to a minute to report its stores; if it hasn't by then, look
  again with `sudo journalctl -u trcrd-master -n 30`. `backend ready` means results are
  being saved; `DISCARDED` means they aren't.

Fix what it names, then run `sudo /etc/trcr/finish-setup.sh` again. For more
on each one, see [Troubleshooting](troubleshooting.md#the-install-ends-without-you-are-all-set).

The local agent is named after the host, with `-local` on the end.

`trcr-firstboot` exists only when you installed with `--email`. With
`--license`, the same output appears in your terminal at the end of the
install instead. If it ends with one of the messages above, the installer
ends with `Fix what it reported above, then run: sudo /etc/trcr/finish-setup.sh`
and exits with status 1.

To finish by hand at any time, run this on the host. It's safe to run as often
as you like:

```bash
sudo /etc/trcr/finish-setup.sh
```

It claims a waiting license, starts whatever isn't running, enrolls the local
agent if there isn't one, and shows the Grafana password again. Its output
also goes to `/var/log/trcr-install.log`.

## Open your dashboards

Grafana only listens on the host itself (127.0.0.1), so nobody else can reach
it. To open it from your own computer, start an SSH tunnel to the host:

```bash
ssh -L 3000:127.0.0.1:3000 <your-trcr-host>
```

Then open `http://localhost:3000` in your browser and sign in as `admin` with
the password from the install summary. If you've lost it, it's in
`/etc/trcr/grafana-admin.env`, and `sudo /etc/trcr/finish-setup.sh` shows it
again. Copy it rather than retyping it: after five wrong passwords, Grafana
locks the account for five minutes.

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
printed one, and it works for an hour. Only the run that enrolls the local
agent prints a ready-made command; running the installer or `finish-setup.sh`
again says `To add another host, run this here on the master and paste the
command it prints on that host:` and points at `sudo trcrd enroll-agent`
instead.

On the agent, you'll see:

```
==> Enrolling with the master at 192.0.2.10:8444 ...
...
==> This host is enrolled and the agent is running. Nothing else to do here.
...
    To upgrade this agent later, run:  curl -fsSL https://trcr.dev/install/install.sh | sh
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
- The setup ended without `You are all set`: see
  [Troubleshooting](troubleshooting.md#the-install-ends-without-you-are-all-set).
- The installer stopped with a signature or OpenSSL error: see
  [Troubleshooting](troubleshooting.md#the-installer-stops-with-a-signature-or-openssl-error).
- The installer stopped while installing PostgreSQL or Grafana, with the
  package manager's error and then:

  ```
  error: Installing Grafana failed: the package repository returned an error (see above).
         This is usually temporary. Run the same command again in a few minutes; it picks up
         where it stopped.
  ```

  This usually means the package repository had a short-lived problem. Do
  what it says: wait a few minutes and run the same install command again.
  If it keeps failing, the package manager's error above it says why.
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
Leave it out of the URL: the installer refuses a URL with `USER:PASSWORD@` in
it, so the password stays out of your shell history, the install log and
`master.yaml`. Then run this on the master host:

```bash
curl -fsSL https://trcr.dev/install/install.sh | sh -s -- \
  --postgres-dsn 'postgres://trcr@db.example.com:5432/trcr_results?sslmode=require' \
  --postgres-password-file pg-password.txt
```

The quotes keep the `?` from the shell. `sslmode=require` is right for a
database that has TLS. A database without TLS, which includes many LAN
installs and the stock PostgreSQL container image, needs `sslmode=disable`;
otherwise the master's connection is refused at the handshake and nothing is
saved.

The installer copies the password into `/etc/trcr/postgres.env`, as one line,
`TRCR_PG_PASSWORD=<password>`. Only root and the `trcr` group can read that
file, and systemd hands it to the master. The password never goes into
`master.yaml`, and you can delete your file afterwards. If `psql` is installed on the host, the installer checks it can
connect, and stops if it can't. Without `psql`, the connection is tried when
the master starts. Once the configuration is written, the installer says:

```
==> Pointed the master at your PostgreSQL database (the password stays in /etc/trcr/postgres.env, not in master.yaml).
```

If the password is already in an exported environment variable, use
`--postgres-password-env <NAME>` instead of `--postgres-password-file`. Either
way, the password can't contain a quote mark or a backslash.

The `backends:` entry the installer writes carries the comment
`# written by the TRCR installer (--postgres-dsn)` above it. If the address
or `sslmode` turns out to be wrong, run the installer again with the corrected
`--postgres-dsn`. It updates the `dsn:` line of that entry and says
`Updated the database address in /etc/trcr/master.yaml.`; if the master is
running, it follows with `Restarting trcrd-master so it uses the new address ...`.

A wrong password works the same way. Run the installer again with the
corrected `--postgres-password-file`. It says
`Updated the database password in /etc/trcr/postgres.env.` and, if the master
is running, `Restarting trcrd-master so it uses the new password ...`. If both
changed, one restart covers both. After a restart for a new address or
password, the installer gives the master up to a minute to open the database
before it says whether results are being saved, so a database far away has
time to answer.

If `/etc/trcr/master.yaml` was already on the host and the installer didn't
write it, it's left as it is, and the end of the run says so:

```
  note: Your existing /etc/trcr/master.yaml was kept as it was, because the installer did not
  write it. Nothing in it names the database address you gave, so results are not
  going there yet. To use it, add this under backends: (or change the dsn: of the
  entry that is there):
      - name: postgres-main
        type: postgres
        dsn: "postgres://trcr@db.example.com:5432/trcr_results?sslmode=require"
        password_env: TRCR_PG_PASSWORD
        auto_create_tables: true
  Or regenerate it from scratch, which discards every other edit in it:
```

The last line is followed by a `sudo trcrd init --force` command. Use it only
if nothing else in the file matters to you.

So that your database gets data straight away, the installer also writes seven
starter probes that measure this host's connection to the internet:

```
==> Added 7 starter probes so you see data in your database straight away (/etc/trcr/conf.d/standalone.yaml).
```

Without a license, the installer stops there and prints the steps that are
left. Here they are with the reason for each:

1. If agents on other hosts will connect, set `master.advertise_addr` in
   `/etc/trcr/master.yaml` to a name or address they can reach. See
   [Configuration](configuration.md#advertise_addr-is-required-for-remote-agents).
2. Add probes of your own. The starter probes run as soon as the master
   starts, so this can wait.
   To start from the sample probes, copy them to an active name, then edit the
   targets:

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

   Already have a license file? Install it so the master can read it:

   ```bash
   sudo install -o root -g trcr -m 0640 license.lic /etc/trcr/license.lic
   ```

5. Start everything:

   ```bash
   sudo /etc/trcr/finish-setup.sh
   ```

   This starts the master, enrolls a local agent and prints the command for
   adding more agents. Without `psql` on the host, a working connection shows
   as:

   ```
       The master opened your PostgreSQL database; results are going there.
       (psql is not installed on this host, so the first rows were not looked at.)
   ```

   If the master can't reach the database, the step ends with `The master is
   running, but it is not saving results anywhere, so they are being thrown
   away.` and quotes the database's error. For a connection or TLS failure,
   the next lines are:

   ```
       Fix the database, or the sslmode/host in the dsn: line of /etc/trcr/master.yaml (a database without TLS needs sslmode=disable), then:
         sudo systemctl restart trcrd-master && sudo /etc/trcr/finish-setup.sh
       (Or run the installer again with the corrected --postgres-dsn; it updates that line and restarts the master.)
       The full log: sudo journalctl -u trcrd-master -n 30
   ```

You can also add `--license /path/to/license.lic` to the install command. The
master then starts straight away with the starter probes, and the install ends
the way the all-in-one install does. If the master can't open the database,
the install ends with `Fix what it reported above, then run: sudo /etc/trcr/finish-setup.sh`
and exits with status 1. To add probes afterwards, copy them in, validate, and
restart the master with `sudo systemctl restart trcrd-master`.

The summary at the end shows what the master uses:

```
  What is on this host now:
    PostgreSQL   your database trcr_results at db.example.com:5432; password in /etc/trcr/postgres.env
    Probes       7 starter probes in /etc/trcr/conf.d/standalone.yaml; change them whenever you like
```

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
plus choosing the store.

For PostgreSQL, step 1 tells you to run the installer again with
`--postgres-dsn` and `--postgres-password-file`, which writes the
configuration for you. The URL it shows is in single quotes, with the
reminder that a database without TLS needs `sslmode=disable`. For any other
store, you edit `backends:` in `master.yaml` yourself, and a password the
store names with `password_env` goes in `/etc/trcr/master.env` as
`NAME=value`. The master's service reads that file, and the installer has
already created it, empty, with the right permissions. See
[Storing results](backends.md).

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
| `TRCR_SKIP_SETUP=1` | Install or upgrade the binary only. Nothing in `/etc/trcr` is touched, and the run ends after the `Installed` line; on an agent host it adds that the host is an agent. | `curl -fsSL https://trcr.dev/install/install.sh \| TRCR_SKIP_SETUP=1 sh` |
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
  overwritten, except `_samples.yaml` and the examples, which are refreshed
  for every release. Edit a copy of them, not the files themselves.
- Installs the `trcrd-master` service and `/etc/trcr/finish-setup.sh`, the
  script that starts the master and enrolls a local agent once a license is in
  place.
- Creates `/etc/trcr/master.env`, empty and readable by root and the `trcr`
  group only, for passwords that results stores read from the environment.
  The master's service reads it.
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
`trcrd`, restarts the TRCR services that were running, and leaves your
configuration, license and data alone. With no options, it keeps the way the
host was set up: an all-in-one host stays all-in-one, Grafana included, and
a master on your own PostgreSQL keeps using it. On either of those, a run
with nothing to upgrade and everything running takes seconds and says
`Nothing to do: trcrd v26.11.0 is installed and everything is running.`,
whether you give the options you installed with or none. See
[Operations](operations.md#upgrade-trcr).

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
check, search the log back to the master's latest start, so a problem you've
already fixed and restarted from doesn't show up again:

```bash
sudo journalctl -u trcrd-master -r | sed '/master ready/q' | grep -i discard
```

No output means nothing is being thrown away. `finish-setup.sh` runs this check
for you. To learn what else belongs in a healthy log, see
[Operations](operations.md#what-a-healthy-master-log-looks-like).

If you're logged in as root on a host without `sudo`, leave `sudo` off these
commands. The installer does the same in the commands it prints.

### Upgrade or uninstall

See [Operations](operations.md#upgrade-trcr) and
[Operations](operations.md#uninstall-trcr).
