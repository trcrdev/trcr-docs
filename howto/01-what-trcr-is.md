# What TRCR is, in two minutes

Hi. This is a short walkthrough of TRCR, the network monitoring daemon you run on your own machines.

TRCR has two parts. A master, and agents. The master holds your probe configuration, issues certificates, collects results and writes them to a database you own. Agents are the machines that actually do the measuring. You put them where your users are: a branch office, a cloud region, a home connection. Each agent pings, traces routes, checks DNS, watches TLS certificates and tests throughput, then sends the results back to the master over mutual TLS.

Nothing leaves your network except an optional licence heartbeat. Results go to PostgreSQL, InfluxDB, Elasticsearch or Prometheus. Grafana dashboards ship with it.

Getting started takes one command on a Linux host. It installs the master, a local agent, PostgreSQL and Grafana with the dashboards already loaded. Adding another agent is one more command, which the master prints for you. There is also a container image for Docker and Podman if you would rather not install packages.

The free tier covers five agents and all probe types. In the next walkthrough we install it.
