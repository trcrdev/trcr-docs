# Alerting

The master checks every result against your alert rules as it arrives, at the
same time as it stores the result. When a rule fires, the alert goes to the
outputs you name.

- **Rules** say when to alert. They can live in `master.yaml` or in any
  `conf.d` fragment, next to the probes they watch.
- **Outputs** say where alerts go. They can only be defined in `master.yaml`.

```yaml
# /etc/trcr/master.yaml
alerting:
  outputs:
    - name: pager
      kind: webhook
      url_env: TRCR_PAGER_URL        # keep the URL out of the file; it often contains a secret
      method: POST
      headers: { Content-Type: application/json }
      template: |
        {"text": {{ printf "%s on %s: %s" .Severity .ProbeName .Reason | json }}}

    - name: console
      kind: stdout
      format: json

  rules:
    - name: high-latency
      rule: threshold
      severity: warning
      match: { probe_type: ping }
      metric: avg_rtt_ms
      operator: ">"
      value: 100
      for: 3
      cooldown: 10m
      outputs: [pager, console]

    - name: site-down
      rule: probe_failure
      severity: critical
      match: { probe_name: "website*" }
      for: 2
      cooldown: 15m
      outputs: [pager]
```

## Rule types

| Rule | Fires when |
|---|---|
| `threshold` | A measurement compared with a value is true. Operators: `>`, `>=`, `<`, `<=`, `==`, `!=`. |
| `probe_failure` | A probe run fails. You can narrow it to one `error_class`, for example `cert_expired`. |
| `traceroute_path_change` | The path to a target differs from the last one seen. With `path_level: as` it compares the networks crossed, which is less noisy than comparing every hop. The first run only records the path. |

`match.probe_name` and `match.probe_type` accept `*` wildcards.

`severity` is `info`, `warning` or `critical`. It is `warning` when you leave it
out.

## Avoiding noise: `for` and `cooldown`

- **`for: N`** means the condition must be true on **N results in a row**
  before the alert fires. Any result that does not match resets the count.
- **`cooldown: 10m`** means that after firing, the same alert stays quiet for
  that long.

Both are counted separately for each combination of rule, probe and target. A
flapping probe does not reset the count for another probe under the same rule.

Start with `for: 3` on anything measured across the internet. Single failed
runs are normal.

## Outputs

| Kind | Notes |
|---|---|
| `webhook` | An HTTP request to a URL. Give the URL with `url:` or, better, `url_env:`. Set `method` and `headers`, and shape the body with `template:`. |
| `stdout` | Writes the alert to the journal, as `json` or `text`. |
| `elasticsearch` | Indexes alerts. Takes `urls`, `index_prefix` and `auth`, like the [Elasticsearch store](backends.md#elasticsearch). |

A slow output does not hold up the others.

### Webhook templates

Templates can use these fields:

`.Ts` `.AlertID` `.RuleName` `.RuleType` `.Severity` `.ProbeName` `.ProbeType`
`.Target` `.AgentID` `.Reason` `.Metric` `.Value` `.ErrorClass` `.PrevPath`
`.NewPath`

**Pipe values through `json` when you build a JSON body**, as in the example
above. It adds the quotes and escapes special characters. Without it, a target
or label containing a quote mark produces a broken body.

With no template, the body is the whole alert as JSON, with some extra context
fields. If the receiving service rejects fields it does not know, add
`include_annotation: false` to the output to leave those out.

## Rules for bundles you are not licensed for

A rule that matches a probe type outside your licence is switched off at
startup. It does not cause an error.

## Checking that alerts work

1. Add a `stdout` output to a rule.
2. Make the rule easy to trigger for a moment, for example a threshold of `0`.
3. Restart the master and watch: `sudo journalctl -fu trcrd-master`.
4. Put the real value back.

The master's own metrics count alerts fired and deliveries that succeeded or
failed. See [Operations](operations.md#metrics).

## Alerting when TRCR itself has a problem

Alert rules watch your targets. To watch TRCR:

- `trcrd agents --stale` exits with status 1 when an agent is not reporting.
  Run it from cron.
- Scrape the master's metrics and alert on failed writes to your results
  store.
- Check the master's health address (port 8080) from your load balancer or
  uptime monitor.

Next: [Dashboards](dashboards.md).
