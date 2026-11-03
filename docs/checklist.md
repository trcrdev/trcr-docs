# Before you go to production

Most problems with a TRCR deployment come from a short list of causes. This
page collects them, grouped by when you'd deal with each one.

If you're trying TRCR on one host for the first time, you can skip this page
for now. [Install it](install.md#install-everything-on-one-host), look at the
dashboards, and come back here before you rely on the data.

## Before you install

- [ ] Decide where the master goes. Put it near your database, on a host every
      agent can reach. It doesn't need to be a good place to measure from.
- [ ] Plan for at least three agents, so you can tell where a problem is, not
      only that there is one. The free license allows five, including the
      all-in-one's local agent. See
      [Getting started](getting-started.md#how-many-agents).
- [ ] Check OpenSSL with `openssl version`. The installer needs 1.1.1 or later
      to check the download's signature.
- [ ] Check the clock on every host. License expiry and certificates depend on
      the time being right, so make sure NTP or chrony is running.
- [ ] Use an email address you can open now. The free license needs you to
      click a link, and the link works for 24 hours.
- [ ] Give each host a sensible hostname first. An agent's name defaults to
      its hostname, and you'll see that name in every dashboard.

## Before you add remote agents

- [ ] Open both 8443 and 8444 on the master, in the host firewall and in any
      cloud firewall. With only 8444 open, an agent enrolls and then never
      reports.
- [ ] Set `master.advertise_addr` to an address your agents can reach, with
      the enrollment port, for example `trcr-master.example.com:8444`. Restart
      the master after changing it. Without it, remote agents enroll and then
      fail every call. This is the most common reason an agent is stuck at
      `never-seen`. See
      [Configuration](configuration.md#advertise_addr-is-required-for-remote-agents).
- [ ] Decide which way enrollment goes. If the agent can reach the master,
      use a join command; this works behind NAT. If only the master can reach
      the agent, use a pairing code. See [Agents](agents.md).
- [ ] Allow the master out to `trcr.dev` and `api.trcr.dev` on port 443, or
      plan to [run without internet access](security.md#run-trcr-without-internet-access).
- [ ] For bandwidth tests, open port 5202 between the agents involved.

## Before you rely on the data

- [ ] Point the master at a real results store. A master installed with no
      options writes results to the journal only. The all-in-one install and
      `--postgres-dsn` set up PostgreSQL for you. For a database without
      TLS, the URL needs `sslmode=disable`, or the store never opens. See
      [Storing results](backends.md).
- [ ] Copy the sample probes before you edit them. Files whose names start
      with `_` are ignored, so `_samples.yaml` does nothing until you copy it.
      Copy it with `install`, so the master can read the copy:
      `sudo install -o root -g trcr -m 0640 /etc/trcr/conf.d/_samples.yaml /etc/trcr/conf.d/probes.yaml`
- [ ] Replace the sample targets with your own. The samples point at public
      services so they produce data straight away, but they don't tell you
      anything about your network.
- [ ] Run `sudo trcrd validate --config /etc/trcr/master.yaml` after every
      edit. It reports every problem at once, names the file and the key, and
      warns about any file the master can't read and any password variable
      its service doesn't set. A misspelled key is an error, not something
      that gets ignored.
- [ ] Restart the master after every change to its configuration:
      `sudo systemctl restart trcrd-master`. The master reads its files only
      when it starts, and `validate` reminds you when a restart is due.
      Agents pick up probe changes from the master by themselves within a
      minute.
- [ ] Monitoring private addresses? Add `allow_private_targets: true` to those
      probes, or they're refused. See
      [Probes](probes.md#private-and-internal-targets).
- [ ] Keep passwords out of YAML. Use the `*_env` settings, with the values in
      `/etc/trcr/master.env`, which the installer creates with the right
      permissions, or `trcrd encrypt-password`. See
      [Security](security.md#secrets-in-configuration).
- [ ] Install files with `sudo install -o root -g trcr -m 0640`, not `cp`,
      license included. The master runs as the `trcr` user and won't start if
      it can't read one.

## Once it's running

- [ ] `sudo trcrd agents` shows every agent as `up`.
- [ ] `sudo trcrd probes` shows your probes and where each one runs.
- [ ] The master's log has no line saying results are DISCARDED:
      `sudo journalctl -u trcrd-master | grep -i discard` prints nothing. Read
      any `WARN` or `ERROR` line; on a healthy master there are almost none.
      See [what a healthy log looks like](operations.md#what-a-healthy-master-log-looks-like).
- [ ] `sudo trcrd license status` shows `last heartbeat:` with `ok`, unless
      you've turned check-ins off.
- [ ] Grafana shows data in the **TRCR** folder within a few minutes.
- [ ] Back up `/etc/trcr` and `/var/lib/trcr` on the master. The second holds
      your deployment's certificate authority; if you lose it, every agent
      has to enroll again. See [Operations](operations.md#backups).
- [ ] Keep a copy of your license file somewhere else.
- [ ] Get told when an agent stops reporting. `trcrd agents --stale` exits
      with status 1 when any agent isn't reporting, so it fits in a cron job.
