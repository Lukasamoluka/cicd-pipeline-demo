const test = require('node:test');
const assert = require('node:assert');
const app = require('./app');

test('GET /health returns healthy', async () => {
  const server = app.listen(0);
  const { port } = server.address();
  try {
    const res = await fetch(`http://127.0.0.1:${port}/health`);
    const body = await res.json();
    assert.strictEqual(res.status, 200);
    assert.deepStrictEqual(body, { status: 'healthy' });
  } finally {
    server.close();
  }
});
