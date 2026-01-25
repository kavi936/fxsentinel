# Central Bank Documents Directory

This directory contains central bank documents organized by institution.

## Directory Structure

```
central-bank/
├── fed/          - Federal Reserve documents
├── ecb/          - European Central Bank documents
├── boj/          - Bank of Japan documents
├── boe/          - Bank of England documents
├── rba/          - Reserve Bank of Australia documents
├── boc/          - Bank of Canada documents
├── snb/          - Swiss National Bank documents
├── rbnz/         - Reserve Bank of New Zealand documents
├── charts/       - Central bank charts and visualizations
└── cot-reports/  - Commitment of Traders reports
```

## Adding New Documents

1. **Download the document** (PDF, image, etc.)
2. **Place it in the appropriate subdirectory** based on the central bank
3. **Update `public/central-bank-documents.json`** with the document metadata:
   - Add a new entry to the `documents` array
   - Use a unique `id` (e.g., "fed-2024-01-15-fomc-minutes")
   - Set the correct `filePath` (e.g., "/documents/central-bank/fed/filename.pdf")
   - Fill in all required fields (title, type, date, etc.)

## File Naming Convention

Use descriptive, lowercase filenames with hyphens:
- Good: `fomc-minutes-jan-2024.pdf`
- Good: `powell-speech-feb-2024.pdf`
- Avoid: `FOMC_Jan_2024.pdf` (uppercase, underscores)

## Document Types

- `meeting_minutes` - Official meeting minutes
- `speech` - Central bank official speeches
- `report` - Economic or financial reports
- `cot_report` - Commitment of Traders reports
- `chart` - Charts and visualizations
- `statement` - Policy statements

## Notes

- Files in this directory are served statically by Vercel
- No hosting costs - files are part of the static build
- Maximum file size recommended: 10MB per document
- All files are publicly accessible via their URLs

