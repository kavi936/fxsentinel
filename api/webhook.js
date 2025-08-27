module.exports = (req, res) => {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  // Handle preflight requests
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  // Handle webhook endpoint
  if (req.url === '/api/stripe-webhook' && req.method === 'POST') {
    console.log('📡 Stripe webhook received');
    res.status(200).json({
      success: true,
      message: 'Webhook received'
    });
    return;
  }

  // Handle health check
  if (req.url === '/api/health' && req.method === 'GET') {
    res.status(200).json({
      status: 'healthy',
      webhook: 'working'
    });
    return;
  }

  // Default response
  res.status(404).json({
    error: 'Not found'
  });
};
