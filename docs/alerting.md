# Alerting

Dashboards show you what happened. Alerts tell you while it's happening, so
you don't have to be watching. The master checks every result against your
alert rules as it arrives, at the same time as it stores the result. When a
rule fires, the alert goes to the outputs you name.

- Rules say when to alert. They can live in `master.yaml` or in any `conf.d`
  fragment, next to the probes they watch.
- Outputs say where alerts go. They can only be defined in `master.yaml`.

Here's a complete example with two outputs and two rules. The first rule warns
when ping latency stays above 100 ms; the second pages you when a website
check keeps failing:

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

`severity` is `info`, `warning` or `critical`. It's `warning` when you leave it
out.

## Avoid noise with `for` and `cooldown`

Single failed runs are normal on anything measured across the internet, so an
alert on every failure soon gets ignored. Two settings keep alerts worth
reading:

- `for: N` means the condition must be true on N results in a row before the
  alert fires. Any result that doesn't match resets the count.
- `cooldown: 10m` means that after firing, the same alert stays quiet for that
  long.

Both are counted separately for each combination of rule, probe and target, so
a flapping probe doesn't reset the count for another probe under the same rule.

Start with `for: 3` on anything measured across the internet.

## Outputs

| Kind | Notes |
|---|---|
| `webhook` | An HTTP request to a URL. Give the URL with `url:` or, better, `url_env:`. Set `method` and `headers`, and shape the body with `template:`. |
| `stdout` | Writes the alert to the journal, as `json` or `text`. |
| `elasticsearch` | Indexes alerts. Takes `urls`, `index_prefix` and `auth`, like the [Elasticsearch store](backends.md#elasticsearch). |

A slow output doesn't hold up the others.

### Webhook templates

Templates can use these fields:

`.Ts` `.AlertID` `.RuleName` `.RuleType` `.Severity` `.ProbeName` `.ProbeType`
`.Target` `.AgentID` `.Reason` `.Metric` `.Value` `.ErrorClass` `.PrevPath`
`.NewPath`

When you build a JSON body, pipe each value through `json`, as in the example
above. It adds the quotes and escapes special characters. Without it, a target
or label containing a quote mark produces a broken body.

With no template, the body is the whole alert as JSON, with some extra context
fields. If the receiving service rejects fields it doesn't know, add
`include_annotation: false` to the output to leave those out.

## Rules for bundles you aren't licensed for

A rule that matches a probe type outside your license is switched off when the
master starts. It doesn't cause an error, so you can keep the same rules on
every master.

## Check that alerts work

It's worth firing an alert on purpose before you rely on one:

1. Add the `stdout` output to a rule's `outputs:`.
2. Make the rule fire straight away for a moment, for example a threshold rule
   with `value: 0` and `for: 1`.
3. Restart the master and watch its log:

   ```bash
   sudo systemctl restart trcrd-master
   sudo journalctl -fu trcrd-master
   ```

   Within a minute or two, the alert appears in the log as a JSON line with the
   rule's name, the probe and the reason. If your webhook output is on the
   same rule, check that it arrived too.
4. Put the real value back and restart the master again.

The master's own metrics count alerts fired and deliveries that succeeded or
failed. See [Operations](operations.md#metrics).

## Alerting when TRCR itself has a problem

Alert rules watch your targets. To watch TRCR itself:

- `trcrd agents --stale` exits with status 1 when an agent isn't reporting.
  Run it from cron.
- Scrape the master's metrics and alert on failed writes to your results
  store.
- Point your load balancer or uptime monitor at the master's health check.
  It's off until you set `master.health_listen_addr`; see
  [Operations](operations.md#health-checks).

Next, look at your results: [Dashboards](dashboards.md).
