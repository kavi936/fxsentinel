# Central Bank Documents - User Guide

## Overview

The Central Bank Analysis card provides traders with access to official documents, meeting minutes, speeches, reports, and COT data from major central banks. All documents are stored locally in the project and served statically (no hosting costs).

## How to Add Documents

### Step 1: Download the Document
Download the PDF or file you want to add from the central bank's official website.

### Step 2: Place File in Directory
Place the file in the appropriate subdirectory:
- `public/documents/central-bank/fed/` - Federal Reserve documents
- `public/documents/central-bank/ecb/` - European Central Bank documents
- `public/documents/central-bank/boj/` - Bank of Japan documents
- `public/documents/central-bank/boe/` - Bank of England documents
- `public/documents/central-bank/rba/` - Reserve Bank of Australia documents
- `public/documents/central-bank/boc/` - Bank of Canada documents
- `public/documents/central-bank/snb/` - Swiss National Bank documents
- `public/documents/central-bank/rbnz/` - Reserve Bank of New Zealand documents
- `public/documents/central-bank/charts/` - Charts and visualizations
- `public/documents/central-bank/cot-reports/` - COT reports

**File naming convention**: Use lowercase with hyphens (e.g., `fomc-minutes-jan-2024.pdf`)

### Step 3: Update Metadata File
Edit `public/central-bank-documents.json` and add a new entry to the `documents` array:

```json
{
  "id": "fed-2024-01-15-fomc-minutes",
  "title": "FOMC Meeting Minutes - January 2024",
  "type": "meeting_minutes",
  "centralBank": "FED",
  "date": "2024-01-15",
  "category": "monetary_policy",
  "impact": "high",
  "affectedCurrencies": ["USD", "EUR", "GBP"],
  "description": "Federal Open Market Committee meeting minutes discussing interest rate policy.",
  "fileName": "fomc-minutes-jan-2024.pdf",
  "filePath": "/documents/central-bank/fed/fomc-minutes-jan-2024.pdf",
  "fileSize": "2.4 MB",
  "fileFormat": "PDF",
  "tags": ["interest_rates", "inflation", "monetary_policy"],
  "aiAnalysis": null,
  "sentiment": null
}
```

### Required Fields

- **id**: Unique identifier (e.g., "fed-2024-01-15-fomc-minutes")
- **title**: Document title
- **type**: One of: `meeting_minutes`, `speech`, `report`, `cot_report`, `chart`, `statement`
- **centralBank**: One of: `FED`, `ECB`, `BOJ`, `BOE`, `RBA`, `BOC`, `SNB`, `RBNZ`
- **date**: Date in YYYY-MM-DD format
- **category**: One of: `monetary_policy`, `economic_outlook`, `financial_stability`, `market_data`
- **impact**: One of: `high`, `medium`, `low`
- **affectedCurrencies**: Array of currency codes (e.g., ["USD", "EUR"])
- **description**: Brief description of the document
- **fileName**: The actual filename (e.g., "fomc-minutes-jan-2024.pdf")
- **filePath**: Full path from public directory (e.g., "/documents/central-bank/fed/fomc-minutes-jan-2024.pdf")
- **fileSize**: Human-readable file size (e.g., "2.4 MB")
- **fileFormat**: File format (e.g., "PDF")
- **tags**: Array of relevant tags
- **aiAnalysis**: Leave as `null` for now (future AI integration)
- **sentiment**: Leave as `null` for now (future AI integration)

### Step 4: Deploy
After adding documents:
1. Commit changes to git
2. Push to GitHub
3. Vercel will automatically rebuild and deploy
4. Documents will be accessible via the Central Bank Analysis card

## Features

### Search
Users can search documents by:
- Title
- Description
- Tags
- Central bank name

### Filters
Users can filter by:
- **Central Bank**: FED, ECB, BOJ, BOE, RBA, BOC, SNB, RBNZ
- **Document Type**: Meeting Minutes, Speech, Report, COT Report, Chart, Statement
- **Impact Level**: High, Medium, Low

### Download
Users can download documents directly by clicking the "Download" button. Files are served from Vercel's CDN (fast and free).

## File Size Recommendations

- **Recommended maximum**: 10MB per document
- **For larger files**: Consider compressing PDFs or splitting into multiple parts
- **Total storage**: Vercel free tier includes 100GB bandwidth/month

## Future Enhancements

- AI analysis integration (dovish/hawkish sentiment)
- Document preview in browser
- Favorites/bookmarking
- Email notifications for new documents
- Document versioning

## Troubleshooting

### Document not showing up?
1. Check that the file exists in the correct directory
2. Verify the `filePath` in JSON matches the actual file location
3. Ensure JSON syntax is valid (use a JSON validator)
4. Clear browser cache and refresh

### Download not working?
1. Verify the file path is correct
2. Check that the file exists in the `public/documents/` directory
3. Ensure Vercel deployment completed successfully
4. Check browser console for errors

### File too large?
1. Compress PDF using tools like Adobe Acrobat or online PDF compressors
2. Consider splitting large documents into parts
3. Use image optimization for charts/images

