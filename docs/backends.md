# Storing results

The master writes every result to the stores listed under `backends:` in
`/etc/trcr/master.yaml`. Stores are free in every tier, and you can use several
at once. `trcrd init` writes a commented example of each into `master.yaml`.

| Type | Use it for |
|---|---|
| `postgres` | The default choice. Works with the PostgreSQL edition of the dashboards. |
| `influxdb_v2` | InfluxDB 2.x. Works with the InfluxDB edition of the dashboards. |
| `elasticsearch` | Searching results in Elasticsearch and Kibana. |
| `prometheus` | Exposing the latest results for an existing Prometheus to scrape. |
| `file` | Writing results to a local file, for a log shipper or a host with no network access. |
| `stdout` | Printing results. For a first look and for debugging only. |

One store failing never stops the master or the other stores. A store that
cannot be opened is skipped with an error in the log, and the master carries
on. **That means a master can run and store nothing**, so check the log after
changing this section:

```bash
sudo journalctl -u trcrd-master | grep -iE "backend|discard"
```

## Passwords and tokens

Never put a password or token in `master.yaml`. Each store reads its secret
from an environment variable that you name with a `*_env` setting. Supply the
variable through a systemd drop-in that points at a protected file:

```bash
sudo install -m 0640 -o root -g trcr /dev/null /etc/trcr/postgres.env
echo 'TRCR_PG_PASSWORD=your-password' | sudo tee /etc/trcr/postgres.env >/dev/null
sudo systemctl edit trcrd-master
```

```ini
[Service]
EnvironmentFile=/etc/trcr/postgres.env
```

The all-in-one install does exactly this for you.

## PostgreSQL

```yaml
backends:
  - name: postgres-main
    type: postgres
    dsn: "postgres://trcr@db.example.com:5432/trcr_results?sslmode=require"
    password_env: TRCR_PG_PASSWORD
    auto_create_tables: true
    batch_size: 100
    flush_interval: 5s
    partitioning:
      granularity: monthly     # monthly or daily
      prebuild_months: 2       # create this many partitions ahead
      retention_months: 12     # drop data older than this; 0 keeps everything
```

- Create an empty database and a user that owns it. With
  `auto_create_tables: true`, TRCR creates and maintains everything it needs
  inside that database, including new partitions. There is no migration step
  when you upgrade.
- Data is partitioned by month and kept for 12 months unless you change
  `retention_months`. Old partitions are dropped automatically.
- For Grafana, create a separate read-only user. It only needs `SELECT`.

### TimescaleDB

```yaml
    timescaledb:
      enabled: true
      chunk_interval: 1 day
      compression_after: 7d    # 0 never compresses
```

The TimescaleDB extension must already be installed in the database. If the
configuration says it is enabled and the extension is missing, this store will
not open. When TimescaleDB is on, the `partitioning:` block is ignored. The
installer's `--timescaledb` option sets all of this up.

## InfluxDB v2

```yaml
backends:
  - name: influx-main
    type: influxdb_v2
    url: http://influx.example.com:8086
    token_env: TRCR_INFLUX_TOKEN
    org: trcr
    bucket: trcr-results
```

Create the bucket and a token with write access to it. Results are sent in
batches. Set the bucket's retention period in InfluxDB to control how long
data is kept. The ready-made dashboards show how to query the data.

## Elasticsearch

```yaml
backends:
  - name: es-main
    type: elasticsearch
    urls: ["https://es.example.com:9200"]
    index_prefix: "trcr-results-"
    index_rollover: daily        # daily, monthly or never
    bulk_size: 100
    auth:
      user: trcr
      password_env: TRCR_ES_PASSWORD
      # or: api_key_env: TRCR_ES_API_KEY
```

One document per result. Use your cluster's index lifecycle rules to remove old
indices.

## Prometheus

```yaml
backends:
  - name: prometheus-exporter
    type: prometheus
    listen: 127.0.0.1:9102       # use 0.0.0.0:9102 to scrape from another host
    metrics_path: /metrics
    label_allowlist: [site, region]
    # metric_allowlist: [avg_rtt_ms, packet_loss_pct, cert_days_remaining]
    expire_after: 15m
```

This is not a store. It shows the **latest** result of each probe for
Prometheus to scrape, and Prometheus keeps the history.

- Only the probe labels in `label_allowlist` become Prometheus labels. Leave it
  empty for none. This keeps the number of series under control.
- `metric_allowlist` limits which measurements are exposed. Leave it out for
  all of them.
- A probe that stops reporting disappears after `expire_after`.

Do not confuse this with the master's own health metrics on port 9101, which
describe TRCR itself. See [Operations](operations.md#metrics).

## File and standard output

```yaml
backends:
  - name: results-file
    type: file
    path: /var/log/trcr/results.jsonl
    rotate_daily: true
    rotate_keep_days: 14

  - name: console
    type: stdout
    format: json                 # json or text
```

The file store appends one JSON object per line. The service may only write
under `/var/log/trcr` and `/var/lib/trcr`, so keep the file in one of those.

With `stdout`, results go to the journal: `sudo journalctl -fu trcrd-master`.
The starter configuration uses it so that a new install shows something
straight away. Replace it before you rely on the data.

## If the master is down

Agents send results as they are produced. While the master cannot be reached,
results from that period are not kept. Agents carry on probing and start
sending again when the master returns. Plan the master's host accordingly.

Next: [Alerting](alerting.md).
