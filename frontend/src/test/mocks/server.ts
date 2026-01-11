import { setupServer } from 'msw/node';
import { handlers } from './handlers';

// Setup server for API mocking
export const server = setupServer(...handlers);