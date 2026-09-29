const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

app.get('/', (req, res) => {
  res.json({ 
    message: 'Hello from CI/CD pipeline!!!',
    status: 'running',
    timestamp: new Date().toISOString()
  });
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

if (require.main === module) {
  app.listen(PORT, '0.0.0.0', () => {
    console.log(`App listening on port ${PORT}`);
  });
}

module.exports = app;
