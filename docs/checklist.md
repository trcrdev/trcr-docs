# Checklist for a successful installation

Most installation problems come from a short list of causes. Going through
this list first saves time.

## Before you install

- [ ] **Decide where the master goes.** Near your database, reachable by every
      agent. It does not need to be a good place to measure from.
- [ ] **Plan for at least three agents** if you want to locate problems, not
      only detect them. Agents are free. See
      [Getting started](getting-started.md#how-many-agents).
- [ ] **Check OpenSSL is 1.1.1 or later** with `openssl version`. The installer
      needs it to verify the download.
- [ ] **Check the clock.** Licence expiry and certificates depend on the time
      being right. Make sure NTP or chrony is running on every host.
- [ ] **Use an email address you can open now.** The free licence needs you to
      click a link, and the link lasts 24 hours.
- [ ] **Give each host a sensible hostname first.** An agent's name defaults to
      its hostname, and you will see that name in every dashboard.

## Network

- [ ] **Open both 8443 and 8444** on the master, in the host firewall and in
      any cloud firewall. Opening only 8444 gives you an agent that enrols and
      then never reports.
- [ ] **Set `master.advertise_addr`** to an address your agents can reach,
      using the enrolment port, for example `trcr-master.example.com:8444`.
      Restart the master after changing it. Without it, remote agents enrol and
      then fail every call. This is the most common cause of an agent stuck at
      `never-seen`.
- [ ] **Decide which way enrolment goes.** If the master can reach the agent,
      use a pairing code. If the agent is behind NAT, use the token one-liner.
      See [Agents](agents.md).
- [ ] **Allow the master out to `trcr.dev` and `api.trcr.dev` on 443**, or plan
      for [running without internet access](security.md#running-without-internet-access).
- [ ] **For throughput tests, open port 5202** between the agents involved.

## Configuration

- [ ] **Run `trcrd validate` after every edit.** It reports every problem at
      once and names the file and the key. An unknown or misspelt key is an
      error, not something that gets ignored.
- [ ] **Copy the samples before editing them.** Files starting with `_` are
      ignored, so `_samples.yaml` does nothing until you copy it to another
      name.
- [ ] **Replace the placeholder targets.** The samples use `192.0.2.1` and
      `example.com`, which are documentation addresses.
- [ ] **Point probes at a real results store.** The starter configuration
      writes to standard output. Set up PostgreSQL, InfluxDB or another store
      before you rely on the data. See [Storing results](backends.md).
- [ ] **Monitoring private addresses?** Add `allow_private_targets: true` to
      those probes, or they are refused. See
      [Probes](probes.md#private-and-internal-targets).
- [ ] **Keep passwords out of YAML.** Use the `*_env` settings or
      `trcrd encrypt-password`. See [Security](security.md#secrets-in-configuration).
- [ ] **Restart the master after changing its configuration.** There is no
      reload signal. Agents pick up probe changes from the master by themselves
      within a minute.

## After you install

- [ ] `sudo trcrd agents` shows every agent as `up`.
- [ ] `sudo trcrd probes` shows your probes and where each one runs.
- [ ] The master's log has no "results DISCARDED" warning.
- [ ] Grafana shows data in the **TRCR** folder within a few minutes.
- [ ] **Back up `/etc/trcr` and `/var/lib/trcr` on the master.** The second
      holds the certificate authority for your deployment. If you lose it,
      every agent must enrol again.
- [ ] **Keep a copy of your licence file** somewhere else.
- [ ] **Add a check that alerts when an agent stops reporting**:
      `trcrd agents --stale` exits with status 1 when any agent is not
      reporting, so it fits in a cron job.
