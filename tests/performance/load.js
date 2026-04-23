// ================================================================================
// K6 LOAD TEST
// ================================================================================
//负载测试 for AI Learning System
//
// Usage:
//   k6 run tests/performance/load.js
//   k6 run tests/performance/load.js --vus 50 --duration 1m
// ================================================================================

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Counter, Trend } from 'k6/metrics';

const errors = new Rate('errors');
const requests = new Counter('requests');
const responseTime = new Trend('response_time');

const BASE_URL = __ENV.API_URL || 'http://localhost:8010';

export const options = {
  scenarios: {
    smoke: {
      executor: 'constant-vus',
      vus: 1,
      duration: '10s',
    },
    load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: 10 },
        { duration: '1m', target: 30 },
        { duration: '30s', target: 0 },
      ],
    },
    stress: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '20s', target: 50 },
        { duration: '1m', target: 100 },
        { duration: '20s', target: 0 },
      ],
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<1000'],
    http_req_failed: ['rate<0.05'],
  },
};

export default function () {
  requests.add(1);
  
  const res = http.get(`${BASE_URL}/health`);
  responseTime.add(res.timings.duration);
  
  check(res, {
    'status is 200': (r) => r.status === 200,
    'healthy response': (r) => r.json('status') === 'healthy',
  }) || errors.add(1);
  
  sleep(0.5);
}