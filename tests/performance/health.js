// ================================================================================
// K6 PERFORMANCE TESTS
// ================================================================================
// Performance testovi za AI Learning System koristeći k6
//
// Pokretanje:
//   k6 run tests/performance/health.js
//   k6 run tests/performance/health.js --vus 10 --duration 30s
//   k6 run tests/performance/health.js --out influxdb=http://localhost:8086/k6
// ================================================================================

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Definicija metrika
const errorRate = new Rate('errors');
const healthCheckDuration = new Trend('health_check_duration');
const apiResponseTime = new Trend('api_response_time');

// Konfiguracija
const BASE_URL = __ENV.API_URL || 'http://localhost:8010';
const VUS = parseInt(__ENV.VUS || '5');
const DURATION = __ENV.DURATION || '30s';

export const options = {
  scenarios: {
    health_check: {
      executor: 'constant-vus',
      vus: VUS,
      duration: DURATION,
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_duration: ['p(99)<1000'],
    errors: ['rate<0.1'],
  },
};

export default function () {
  // ============================================
  // Health Endpoint Tests
  // ============================================
  
  const healthRes = http.get(`${BASE_URL}/health`, {
    tags: { name: 'health' },
  });
  
  const healthDuration = healthRes.timings.duration;
  healthCheckDuration.add(healthDuration);
  
  check(healthRes, {
    'health returns 200': (r) => r.status === 200,
    'health returns healthy': (r) => r.json('status') === 'healthy',
  }) || errorRate.add(1);
  
  sleep(1);

  // ============================================
  // Live Endpoint Tests
  // ============================================
  
  const liveRes = http.get(`${BASE_URL}/live`, {
    tags: { name: 'live' },
  });
  
  check(liveRes, {
    'live returns 200': (r) => r.status === 200,
    'live returns alive': (r) => r.json('status') === 'alive',
  }) || errorRate.add(1);
  
  sleep(0.5);

  // ============================================
  // Ready Endpoint Tests
  // ============================================
  
  const readyRes = http.get(`${BASE_URL}/ready`, {
    tags: { name: 'ready' },
  });
  
  check(readyRes, {
    'ready returns 200': (r) => r.status === 200,
    'ready returns ready': (r) => r.json('status') === 'ready',
  }) || errorRate.add(1);
  
  sleep(1);

  // ============================================
  // Response Time Tracking
  // ============================================
  
  apiResponseTime.add(healthRes.timings.duration + liveRes.timings.duration + readyRes.timings.duration);
}

export function handleSummary(data) {
  return {
    'stdout': textSummary(data),
    'summary.json': JSON.stringify(data),
  };
}

function textSummary(data) {
  const metrics = data.metrics;
  return `


K6 Performance Test Results
========================

Test Configuration:
- Base URL: ${BASE_URL}
- Virtual Users: ${VUS}
- Duration: ${DURATION}

Results:
--------
HTTP Req Duration:
- avg: ${metrics.http_req_duration.values.avg?.toFixed(2)}ms
- p(95): ${metrics.http_req_duration.values['p(95)']?.toFixed(2)}ms
- p(99): ${metrics.http_req_duration.values['p(99)']?.toFixed(2)}ms
- max: ${metrics.http_req_duration.values.max?.toFixed(2)}ms

Errors:
--------
- Error Rate: ${(metrics.errors?.values?.rate || 0 * 100).toFixed(2)}%

HTTP Status Codes:
--------------
${Object.entries(metrics.http_status_code?.values || {})
  .map(([code, count]) => `  ${code}: ${count}`)
  .join('\n')}

  `;
}