import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 10,
  duration: '30s',
  thresholds: {
    http_req_duration: ['p(95)<500']
  }
};

export default function() {
  const baseUrl = __ENV.BASE_URL || 'http://localhost:8000'; // Default to local development server
  
  // Test the health endpoint
  let response = http.get(`${baseUrl}/health`);
  check(response, {
    'health endpoint status is 200': (r) => r.status === 200,
  });

  // Test the auth endpoints
  response = http.get(`${baseUrl}/auth/me`, {
    headers: {
      'Authorization': 'Bearer ' + __ENV.ACCESS_TOKEN, // Use token from environment
      'Content-Type': 'application/json',
    }
  });
  check(response, {
    'auth endpoint status is 200': (r) => r.status === 200,
  });

  // Test the jobs endpoint
  response = http.get(`${baseUrl}/jobs`, {
    headers: {
      'Authorization': 'Bearer ' + __ENV.ACCESS_TOKEN,
      'Content-Type': 'application/json',
    }
  });
  check(response, {
    'jobs endpoint status is 200': (r) => r.status === 200,
  });

  // Test creating a job (if token is available)
  if (__ENV.ACCESS_TOKEN) {
    const payload = JSON.stringify({
      product_id: 'test-product-id',
      adjustments: {
        background_style: 'minimal',
        tone: 'professional',
        emphasis: 'features',
        duration_preference: 30,
        additional_instructions: 'Make it engaging'
      }
    });
    
    response = http.post(`${baseUrl}/jobs`, payload, {
      headers: {
        'Authorization': 'Bearer ' + __ENV.ACCESS_TOKEN,
        'Content-Type': 'application/json',
      }
    });
    check(response, {
      'create job endpoint status is 201': (r) => r.status === 201,
    });
  }

  sleep(1); // Pause between requests
}