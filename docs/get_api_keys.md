# Getting Multiple Alpha Vantage API Keys

## Why Multiple Keys?
- Each free Alpha Vantage API key has a limit of 25 requests per day
- With 4 keys, you get 100 requests per day (4 × 25)
- This allows for more frequent price updates and better reliability

## How to Get Multiple Keys

### Method 1: Different Email Addresses (Recommended)
1. Go to https://www.alphavantage.co/support/#api-key
2. Use different email addresses for each key:
   - `your-email@gmail.com`
   - `your-email+1@gmail.com` (Gmail allows + aliases)
   - `your-email+2@gmail.com`
   - `your-email+3@gmail.com`

### Method 2: Different Browsers/Incognito
1. Use different browsers or incognito windows
2. Use different email addresses
3. Each registration will give you a unique API key

### Method 3: Family/Friends
1. Ask family or friends to register for you
2. Use their email addresses
3. They'll receive the API keys via email

## Setting Up the Keys

Once you have 4 API keys, update your environment variables:

```bash
# In your .env file or environment
ALPHA_VANTAGE_API_KEY_1=your_first_key_here
ALPHA_VANTAGE_API_KEY_2=your_second_key_here
ALPHA_VANTAGE_API_KEY_3=your_third_key_here
ALPHA_VANTAGE_API_KEY_4=your_fourth_key_here
```

## Testing Your Keys

You can test each key individually:

```bash
# Test Key 1
curl "https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=EUR&to_currency=USD&apikey=YOUR_KEY_1"

# Test Key 2
curl "https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=EUR&to_currency=USD&apikey=YOUR_KEY_2"
```

## Monitoring Usage

Check your API key usage:
```bash
curl http://localhost:8000/api/api-status
```

This will show you:
- How many requests each key has used
- How many requests remain
- Which keys are available/exhausted

## Benefits of This Approach

1. **100 requests per day** instead of 25
2. **Automatic rotation** - system uses available keys
3. **Better reliability** - if one key is exhausted, others are used
4. **Cost-effective** - all keys are free
5. **Easy to scale** - add more keys as needed

## Important Notes

- Each key is tied to an email address
- Keys reset daily at midnight UTC
- The system automatically tracks usage and rotates keys
- If all keys are exhausted, it falls back to cached/fallback data 