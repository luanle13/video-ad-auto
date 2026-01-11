import { http, HttpResponse } from 'msw';

// Define common API handlers for mocking
export const handlers = [
  // Example handler - replace with actual API endpoints as needed
  http.get('/api/health', () => {
    return HttpResponse.json({ status: 'ok' });
  }),
  
  // Add more handlers as needed for your API endpoints
];