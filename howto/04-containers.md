# Run TRCR in Docker or Podman

If you would rather not install packages on the host, the same daemon ships as a container image, and the whole stack comes up with one compose command.

Make an empty directory and download the compose file from the docs. Put your license file next to it, or put your email address in the dot env file if you want the free license requested for you. Add one more line to dot env: the advertise address, which is the name or IP agents will use to reach this host, with port 8444.

Then run docker compose up with the detach flag.

An init container prepares everything: it writes the master configuration, generates the database and Grafana passwords into a secrets volume, places the license, and provisions Grafana with the TRCR dashboards. Then PostgreSQL, the master, Grafana and a local agent start. On a laptop the whole thing takes about twenty seconds. The agent enrolls itself on first start, and the token never touches your dot env file.

A few things worth knowing. The containers start as root only to hand the daemon the raw socket capability it needs for ping and traceroute, then drop to an unprivileged user. Grafana listens on localhost only. And if you edit probe files under etc, restart the master container, because there is no hot reload.

For an agent on another host, there is a smaller compose file with just the agent. On the master run trcrd enroll-agent with the env option. It prints the two lines to put in that host's dot env. Then docker compose up there.

Podman works the same way. With podman compose you use the same file. For a service that starts at boot, the docs ship quadlet files: put the license and a small setup file in etc trcr-container, install the units, and start them with systemctl.
