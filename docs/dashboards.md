# Dashboards

TRCR comes with ready-made Grafana dashboards, published at
[github.com/trcrdev/trcr-dashboards](https://github.com/trcrdev/trcr-dashboards)
with screenshots of what they look like. There are two editions with the same
layout: one for PostgreSQL and one for InfluxDB v2.

## With the all-in-one install

You're already set up. The installer put Grafana on the host, connected it to
your results and loaded every dashboard into a folder called **TRCR**.
[Here's how to sign in](install.md#open-your-dashboards).

## With your own Grafana

If you already run Grafana, or keep your results in a database the installer
didn't set up, connect the dashboards yourself:

1. Add a datasource that points at your results store. The dashboards find
   their datasource by its uid, so it must be exactly:

   | Results store | Datasource type | uid |
   |---|---|---|
   | PostgreSQL | PostgreSQL | `trcr-postgres` |
   | InfluxDB v2 | InfluxDB, query language **Flux** | `trcr-influxdb` |

   Use a read-only database user or a read-only token.
2. Import the dashboards from the repository above. In Grafana, open
   **Dashboards**, then **New**, then **Import**, and upload the JSON files
   for your edition. Or copy them into Grafana's dashboard provisioning folder
   and restart Grafana.

## What you should see in the first hour

Not every dashboard fills at once. Some probes run less often, and some
dashboards need more than one agent. On a new all-in-one host with its seven
starter probes:

| When | Dashboards |
|---|---|
| Within a minute or two | Ping, HTTP, DNS, Overview, Per-Agent Operations, SLO Landing |
| Within the hour | SSL Expiry, Cert Fleet, Traceroute, Map, Alive |
| Once a second agent joins | Agent-to-Agent, Agent Mesh, Cross-Vantage RTT Divergence |
| Once you add probes for them | Throughput, BGP, DNS Propagation (see `/etc/trcr/examples/`) |

## What to look at first

| Dashboard | Use it to |
|---|---|
| SLO Landing | See at a glance whether everything is all right. |
| Ping | See round-trip time and packet loss for each agent and target. |
| Cross-Vantage RTT Divergence | Tell a problem at the target from a problem on one path. |
| Agent Mesh | See latency and loss between your own sites. |
| Per-Agent Operations | Check the agents themselves: how many probes they run and how many succeed. |
| SSL Expiry, Cert Fleet | Find certificates that are about to expire. |

## Tips

- Filters come from your labels. Put labels such as `site` and `region` on
  your probes, and you can filter the dashboards by them. See
  [Probes](probes.md#settings-every-probe-has).
- The Map needs locations. Add `location:` to probes, or configure a GeoIP
  database. See [Configuration](configuration.md#location-data-for-the-map).
- An empty dashboard usually means no probe of that type is running. The
  Throughput dashboard, for example, stays empty until you set up a bandwidth
  test. Check with `sudo trcrd probes --type throughput`.
- "Datasource not found" means the uid doesn't match. Edit the datasource and
  set the uid shown in the table above.
- You're welcome to change the dashboards to suit your deployment. Save your
  version under a new name, so an upgrade doesn't overwrite it.

Next, learn the everyday commands and how to upgrade: [Operations](operations.md).
