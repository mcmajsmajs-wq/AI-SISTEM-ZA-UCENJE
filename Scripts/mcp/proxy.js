const http = require('http');
const net = require('net');
const { URL } = require('url');

const PORT = 8888;
const TARGET_HOST = '192.168.1.16';
const TARGET_PORT = 8081;

const server = http.createServer((req, res) => {
  const options = {
    hostname: TARGET_HOST,
    port: TARGET_PORT,
    path: req.url,
    method: req.method,
    headers: req.headers
  };

  const proxyReq = http.request(options, (proxyRes) => {
    res.writeHead(proxyRes.statusCode, proxyRes.headers);
    proxyRes.pipe(res);
  });

  req.pipe(proxyReq);
  
  proxyReq.on('error', (err) => {
    res.writeHead(502);
    res.end('Proxy error: ' + err.message);
  });
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`Proxy running on http://localhost:${PORT} -> http://${TARGET_HOST}:${TARGET_PORT}`);
});
