# Install TRCR in one command

Let's install TRCR on a Linux host. You need a machine with about two gigabytes of memory, root or sudo, and an email address you can open right now.

On the host, paste the install command from the docs. It looks like this: curl, the install script from trcr dot dev, piped into sh, with the all-in-one option, your email address and your company name.

```
curl -fsSL https://trcr.dev/install/install.sh | sh -s -- --all-in-one --email you@example.com --company "Your Company"
```

The script checks the release signature first, then installs the daemon, PostgreSQL and Grafana with the TRCR dashboards already loaded. On most hosts that takes one to two minutes. Most of that time is the Grafana package download.

When it finishes, it asks TRCR for a free license and tells you: almost done, one click left. Open the email, click the link, and the host finishes setting itself up. It starts the master, enrolls a local agent, and within a few seconds the first measurements land in the database.

If you already have a license file, pass it with the license option instead, and the whole thing finishes in the same run.

At the end you see a summary of what is on the host now. The important lines are the Grafana address and the admin password. Grafana only listens on the host itself, so from your laptop open an SSH tunnel to port 3000, then browse to localhost 3000. The dashboards are in the TRCR folder, and the Overview dashboard already has data.

Two things to remember. First, agents on other hosts need ports 8443 and 8444 open on this one, including in your cloud firewall. Second, if you change probes later, restart the master. There is no hot reload.

That's it. In the next walkthrough we add a second agent.
