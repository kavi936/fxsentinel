export default function handler(req, res) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Stripe-Signature');

  // Handle preflight requests
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  // Handle webhook endpoint
  if (req.method === 'POST') {
    console.log('📡 Stripe webhook received');
    
    // Return 200 status code for Stripe
    res.status(200).json({
      success: true,
      message: 'Webhook received'
    });
    return;
  }

  // Handle health check
  if (req.method === 'GET') {
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
}
