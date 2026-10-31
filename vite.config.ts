import { defineConfig, Plugin } from 'vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath, URL } from 'node:url';
import type { IncomingMessage, ServerResponse } from 'node:http';
import statusHandler from './api/status';
import trafficHandler from './api/traffic';
import chatHandler from './api/chat';

interface ApiRequest extends IncomingMessage {
  query?: Record<string, string>;
  body?: unknown;
}

interface ApiResponse extends ServerResponse {
  status?: (code: number) => ApiResponse;
  json?: (data: unknown) => void;
}

/**
 * Vite Dev Server Middleware Plugin:
 * Serves the serverless API routes (/api/status, /api/traffic, /api/chat) directly
 * within Vite's local dev server, matching the production serverless environment.
 */
function apiDevServerPlugin(): Plugin {
  return {
    name: 'api-dev-server',
    configureServer(server) {
      server.middlewares.use(async (req: ApiRequest, res: ApiResponse, next) => {
        if (!req.url || !req.url.startsWith('/api/')) {
          return next();
        }

        try {
          const parsedUrl = new URL(req.url, 'http://localhost:5173');
          const pathname = parsedUrl.pathname;

          // Polyfill query parameters
          req.query = Object.fromEntries(parsedUrl.searchParams.entries());

          // Polyfill Express/Vercel helper methods on ServerResponse
          if (!res.status) {
            res.status = function (code: number) {
              res.statusCode = code;
              return res;
            };
          }
          if (!res.json) {
            res.json = function (data: unknown) {
              res.setHeader('Content-Type', 'application/json');
              res.end(JSON.stringify(data));
            };
          }

          if (pathname === '/api/status') {
            return await statusHandler(req, res);
          }

          if (pathname === '/api/traffic') {
            return await trafficHandler(req, res);
          }

          if (pathname === '/api/chat') {
            if (req.method === 'POST') {
              let bodyStr = '';
              req.on('data', (chunk) => {
                bodyStr += chunk;
              });
              req.on('end', async () => {
                try {
                  req.body = bodyStr ? JSON.parse(bodyStr) : {};
                  await chatHandler(req, res);
                } catch {
                  if (res.status && res.json) {
                    res.status(400).json({ error: 'Invalid JSON request payload' });
                  }
                }
              });
              return;
            } else {
              return await chatHandler(req, res);
            }
          }

          if (res.status && res.json) {
            res.status(404).json({ error: 'Endpoint not found', pathname });
          }
        } catch (err: unknown) {
          res.statusCode = 500;
          res.setHeader('Content-Type', 'application/json');
          const msg = err instanceof Error ? err.message : 'Server error occurred';
          res.end(JSON.stringify({ error: msg }));
        }
      });
    },
  };
}

// https://vitejs.dev/config/
export default defineConfig({
  base: '/',
  server: {
    host: true,
    port: 5173,
  },
  plugins: [react(), apiDevServerPlugin()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  optimizeDeps: {
    exclude: ['lucide-react'],
  },
  build: {
    chunkSizeWarningLimit: 1600,
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-leaflet': ['leaflet'],
          'vendor-recharts': ['recharts'],
          'vendor-react': ['react', 'react-dom'],
        },
      },
    },
  },
});
