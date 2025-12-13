# UniRateAPI Setup Guide - Free Forex Data Integration

## 🎉 Why UniRateAPI?

- **Completely FREE forever** - No credit card required
- **Unlimited API calls** - No usage limits
- **170+ fiat currencies** + 420+ cryptocurrencies
- **Real-time rates** updated continuously
- **26 years of historical data** (since 1999)
- **Professional data sources** (ECB, major banks)
- **Simple REST API** - Easy integration

## 🚀 Getting Your Free API Key

### Step 1: Visit UniRateAPI
1. Go to [https://unirateapi.com/](https://unirateapi.com/)
2. Click **"Get Free API Key"** button
3. Fill out the registration form:
   - Email address
   - Password
   - Name (optional)
4. **No credit card required!**

### Step 2: Get Your API Key
1. After registration, you'll be redirected to your dashboard
2. Your API key will be displayed prominently
3. Copy the API key - it looks like: `abc123def456ghi789`

### Step 3: Test Your Key
You can test your API key immediately:
```bash
curl "https://api.unirateapi.com/api/rates?api_key=YOUR_API_KEY&from=USD"
```

## 🔧 Setting Up Environment Variables

### Backend Setup
Create or update `.env` file in the `backend/` directory:
```env
UNIRATE_API_KEY=your_actual_unirate_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
FLASK_ENV=development
FLASK_DEBUG=True
```

### Frontend Setup (if needed)
Create or update `.env` file in the root directory:
```env
VITE_UNIRATE_API_KEY=your_actual_unirate_api_key_here
VITE_API_URL=http://localhost:8000
```

## 📊 API Endpoints We'll Use

### 1. Current Exchange Rates
```
GET https://api.unirateapi.com/api/rates?api_key=YOUR_KEY&from=USD
```

**Response:**
```json
{
  "base": "USD",
  "rates": {
    "EUR": 0.85,
    "GBP": 0.73,
    "JPY": 110.0,
    "CAD": 1.25
  }
}
```

### 2. Currency Conversion
```
GET https://api.unirateapi.com/api/convert?api_key=YOUR_KEY&from=USD&to=EUR&amount=100
```

**Response:**
```json
{
  "amount": 100,
  "from": "USD",
  "to": "EUR",
  "result": 85.0
}
```

### 3. Historical Rates
```
GET https://api.unirateapi.com/api/historical/rates?api_key=YOUR_KEY&date=2024-01-01&from=USD
```

## 🔄 Migration from Polygon.io

### What Changes:
1. **API Provider**: Polygon.io → UniRateAPI
2. **Cost**: $50/month → $0/month
3. **Rate Limits**: 100/day → Unlimited
4. **Break-even**: 4 users → 2 users

### What Stays the Same:
1. **Frontend Interface**: No changes needed
2. **Data Quality**: Professional-grade forex data
3. **Error Handling**: Graceful fallback mechanisms
4. **Caching Strategy**: Still implemented for performance

## 🛠️ Implementation Steps

### Step 1: Update Backend Configuration
The backend code has been updated to use UniRateAPI instead of Polygon.io.

### Step 2: Test the Integration
Run the test script:
```bash
python test_unirate_integration.py
```

### Step 3: Verify Data Flow
Check that your frontend displays real-time forex prices correctly.

## 📈 Rate Limiting Strategy

### UniRateAPI Limits:
- **30 requests per minute** (to prevent abuse)
- **Unlimited daily requests**
- **No monthly limits**

### Implementation:
- **Smart caching**: 5-minute cache to reduce API calls
- **Graceful degradation**: Fallback to static data if needed
- **Error handling**: Automatic retry with exponential backoff

## 🎯 Benefits for FXSentinel

### 1. Cost Savings
- **$50/month saved** on data costs
- **Break-even reduced** from 4 to 2 users
- **Higher profit margins** at all user levels

### 2. Better Scalability
- **Unlimited requests** = no growth constraints
- **No need to upgrade** as user base grows
- **Predictable costs** (always $0)

### 3. Professional Data
- **ECB and bank sources** = reliable data
- **Real-time updates** = accurate prices
- **26 years history** = comprehensive data

## 🔍 Testing Your Setup

### 1. Test API Key
```bash
curl "https://api.unirateapi.com/api/rates?api_key=YOUR_API_KEY&from=USD"
```

### 2. Test Backend Endpoint
```bash
curl http://localhost:8000/api/forex-prices
```

### 3. Test API Status
```bash
curl http://localhost:8000/api/api-status
```

## ⚠️ Important Requirements

### Attribution Requirement
UniRateAPI requires attribution on your website. Add this link to your footer or about page:
```html
<a href="https://unirateapi.com">Exchange Rates By UniRateAPI</a>
```

### Usage Terms
- **Personal and commercial use** allowed
- **Caching permitted** for performance
- **Redistribution prohibited** - don't resell the data
- **Attribution required** as mentioned above

## 🚨 Troubleshooting

### Common Issues:

1. **"API key not found"**
   - Check your `.env` file exists
   - Verify the API key is correct
   - Restart your backend server

2. **"Rate limit exceeded"**
   - Wait a few minutes (30 requests/minute limit)
   - Check your caching implementation
   - App will use fallback data automatically

3. **"No data returned"**
   - Verify currency codes are correct
   - Check API key permissions
   - App will use fallback data automatically

### Debug Information:
The API status endpoint (`/api/api-status`) provides:
- Current usage statistics
- Rate limit information
- Last update timestamp
- Data source information

## 📊 Budget Impact Summary

### Before (Polygon.io):
- **Monthly Cost**: $76
- **Break-even**: 4 users
- **Profit at 10 users**: $174

### After (UniRateAPI):
- **Monthly Cost**: $26
- **Break-even**: 2 users
- **Profit at 10 users**: $224

### Savings:
- **$50/month saved** on data costs
- **2 fewer users** needed to break even
- **$50 more profit** at 10 users

## 🎯 Next Steps

1. **Get your free API key** from UniRateAPI
2. **Update environment variables** with your key
3. **Test the integration** with the provided script
4. **Add attribution link** to your website
5. **Monitor usage** via the API status endpoint
6. **Focus on user acquisition** with your lower break-even point

## 📞 Support

- **UniRateAPI Support**: Email support@unirateapi.com
- **Documentation**: https://unirateapi.com/docs
- **API Status**: Check `/api/api-status` endpoint
- **Test Script**: Run `python test_unirate_integration.py`

---

**UniRateAPI is the perfect choice for your MVP - free, unlimited, and professional-grade data that will help you break even faster and scale more profitably!** 