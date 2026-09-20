# Dashboards

Ready-made Grafana dashboards for TRCR are published at
**[github.com/trcrdev/trcr-dashboards](https://github.com/trcrdev/trcr-dashboards)**,
with screenshots of what they look like. There are two editions with the same
layout: one for PostgreSQL and one for InfluxDB v2.

## With the all-in-one install

Nothing to do. Grafana is installed, the datasource is connected and the
dashboards are loaded into a folder called **TRCR**. See
[Installation](install.md#reaching-grafana) for how to log in.

## With your own Grafana

1. **Add a datasource** that points at your results store. The dashboards find
   their datasource by its uid, so it must be exactly:

   | Results store | Datasource type | uid |
   |---|---|---|
   | PostgreSQL | PostgreSQL | `trcr-postgres` |
   | InfluxDB v2 | InfluxDB, query language **Flux** | `trcr-influxdb` |

   Use a read-only database user or a read-only token.
2. **Import the dashboards** from the repository above: in Grafana, open
   *Dashboards → New → Import* and upload the JSON files for your edition. Or
   copy them into Grafana's dashboard provisioning folder and restart Grafana.

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

- **Filters come from your labels.** Put labels such as `site` and `region` on
  your probes and the dashboards can be filtered by them. See
  [Probes](probes.md#settings-every-probe-has).
- **The Map needs locations.** Add `location:` to probes, or configure a GeoIP
  database. See [Configuration](configuration.md#location-data-for-the-map).
- **An empty dashboard usually means no probe of that type is running.** The
  Throughput dashboard, for example, stays empty until you set up a bandwidth
  test. Check with `sudo trcrd probes --type throughput`.
- **"Datasource not found"** means the uid does not match. Edit the datasource
  and set the uid shown in the table above.
- You may change the dashboards to suit your deployment. Save your version
  under a new name so an upgrade does not overwrite it.

Next: [Operations](operations.md).
