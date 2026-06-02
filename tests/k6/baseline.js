// k6 baseline load test for the CRM API.
//
// Hammers the public ping endpoint through the Nginx load balancer so each
// request lands on whichever upstream FastAPI instance least_conn picks.
// The response includes `served_by`, so the test also reports how evenly
// the load balancer spreads work across instances.
//
// Run:
//   BASE_URL=http://localhost:8080 k6 run tests/k6/baseline.js
//
// Configure with env vars:
//   BASE_URL  — default http://localhost:8080
//   STAGES    — comma-separated k6 ramp stages "30s:10,60s:30,30s:0"
//   TAG       — tag results so multiple runs can be compared
//                (e.g. TAG=api1, TAG=api3, TAG=api5)

import http from 'k6/http';
import { check } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';
const TAG      = __ENV.TAG      || 'baseline';

// Custom metrics
const servedBy   = new Counter('served_by_count');
const okRate     = new Rate('http_ok_rate');
const pingLat    = new Trend('ping_latency_ms', true);

// Default progression: warm-up → steady ramp → cool-down (~2.5 min total)
const defaultStages = [
  { duration: '20s', target: 5  },
  { duration: '30s', target: 20 },
  { duration: '60s', target: 50 },  // peak: 50 virtual users
  { duration: '20s', target: 0  },
];

function parseStages(raw) {
  if (!raw) return defaultStages;
  return raw.split(',').map((s) => {
    const [duration, target] = s.split(':');
    return { duration: duration.trim(), target: parseInt(target.trim(), 10) };
  });
}

export const options = {
  stages: parseStages(__ENV.STAGES),
  thresholds: {
    // Pass criteria — used in the report's "expected vs observed" table.
    http_req_failed:    ['rate<0.01'],            // <1% errors
    http_req_duration:  ['p(95)<500'],            // p95 under 500ms
    ping_latency_ms:    ['p(99)<1500'],           // p99 under 1.5s
  },
  tags: { test_run: TAG },
  summaryTrendStats: ['avg', 'min', 'med', 'p(90)', 'p(95)', 'p(99)', 'max'],
};

export default function () {
  const res = http.get(`${BASE_URL}/api/infrastructure/ping`);
  const ok = check(res, {
    'status 200':        (r) => r.status === 200,
    'has served_by':     (r) => r.body && r.body.includes('served_by'),
  });
  okRate.add(ok);
  pingLat.add(res.timings.duration);

  if (res.status === 200) {
    try {
      const j = res.json();
      servedBy.add(1, { instance: j.served_by });
    } catch (_) {}
  }
}

// Pretty-printed summary at end of run.
export function handleSummary(data) {
  return {
    'stdout': textSummary(data),
    [`tests/k6/results/${TAG}-summary.json`]: JSON.stringify(data, null, 2),
  };
}

// Compact ASCII summary helper (k6 v0.48+ ships this in 'k6/x' but we write
// our own to stay version-agnostic).
function textSummary(data) {
  const m = data.metrics;
  const lines = [
    '',
    `=== k6 baseline run (tag=${TAG}) ===`,
    `target URL : ${BASE_URL}/api/infrastructure/ping`,
    `iterations : ${m.iterations.values.count}`,
    `req/s avg  : ${m.http_reqs.values.rate.toFixed(2)}`,
    `error rate : ${(m.http_req_failed.values.rate * 100).toFixed(2)}%`,
    '',
    `latency (ms)  avg=${m.http_req_duration.values.avg.toFixed(1)}`,
    `              p50=${m.http_req_duration.values.med.toFixed(1)}`,
    `              p95=${m.http_req_duration.values['p(95)'].toFixed(1)}`,
    `              p99=${m.http_req_duration.values['p(99)'].toFixed(1)}`,
    `              max=${m.http_req_duration.values.max.toFixed(1)}`,
    '',
  ];
  return lines.join('\n');
}
