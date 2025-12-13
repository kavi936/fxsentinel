#!/usr/bin/env python3
"""
Update Economic Calendar for Next Week
Prepares calendar with upcoming high-impact events
"""

from datetime import datetime, timedelta

# Calculate next week's date range
today = datetime.now()
# If it's weekend, start from Monday
if today.weekday() >= 5:  # Saturday or Sunday
    days_until_monday = 7 - today.weekday()
    start_date = today + timedelta(days=days_until_monday)
else:
    start_date = today

end_date = start_date + timedelta(days=7)

print("=" * 80)
print("UPDATE ECONOMIC CALENDAR FOR NEXT WEEK")
print("=" * 80)
print()
print(f"Current Date: {today.strftime('%A, %B %d, %Y')}")
print(f"Next Week Range: {start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}")
print()

print("=" * 80)
print("KEY FOREX EVENTS - Week of October 21-25, 2025")
print("=" * 80)
print()

# I'll provide guidance on what events to look for
print("📅 MAJOR ECONOMIC EVENTS TO ADD:")
print()

print("MONDAY, Oct 21:")
print("  • Check ForexFactory for any central bank speeches")
print("  • Look for: Manufacturing PMI releases (if scheduled)")
print()

print("TUESDAY, Oct 22:")
print("  • US Existing Home Sales")
print("  • Any Fed speaker events")
print()

print("WEDNESDAY, Oct 23:")
print("  • US New Home Sales")
print("  • FOMC Member speeches (check for Bullard, Williams, etc.)")
print("  • Canadian CPI (if scheduled)")
print()

print("THURSDAY, Oct 24:")
print("  • US Durable Goods Orders")
print("  • US Unemployment Claims (Weekly)")
print("  • ECB speeches or press conferences")
print()

print("FRIDAY, Oct 25:")
print("  • US GDP (Advance estimate - MAJOR)")
print("  • US PCE Price Index (Fed's preferred inflation gauge - MAJOR)")
print("  • University of Michigan Consumer Sentiment")
print()

print("=" * 80)
print("HOW TO UPDATE THE CALENDAR")
print("=" * 80)
print()

print("OPTION 1: Manual Update (Recommended for accuracy)")
print("─" * 80)
print("1. Visit: https://www.forexfactory.com/calendar")
print("2. Filter by:")
print("   • Date range: Oct 21-25, 2025")
print("   • Impact: High only")
print("   • Currencies: USD, EUR, GBP, JPY, AUD, CAD")
print()
print("3. Copy events and paste into:")
print("   backend/services/hybrid_economic_calendar.py")
print("   Starting at line 84 (replace old events)")
print()
print("4. Format:")
events_example = """
    {
        'title': 'US GDP q/q',
        'date': 'Fri, Oct 25',
        'time': '12:30 UTC',
        'currency': 'USD',
        'impact': 'high',
        'actual': 'TBD',
        'forecast': '2.3%',
        'previous': '2.1%'
    },
"""
print(events_example)
print()

print("OPTION 2: Use Pre-Filled Template")
print("─" * 80)
print("I can generate a template file with common weekly events")
print("that you can customize with actual values from ForexFactory.")
print()

print("=" * 80)
print("IMPORTANT NOTES")
print("=" * 80)
print()
print("✅ What to focus on:")
print("  • HIGH impact events only (they trigger pre-event alerts)")
print("  • Major currencies: USD, EUR, GBP, JPY, AUD, CAD")
print("  • Central bank speeches/decisions")
print("  • Employment data (NFP, unemployment claims)")
print("  • Inflation data (CPI, PCE)")
print("  • GDP releases")
print()
print("❌ What to skip:")
print("  • Low/Medium impact events (users filter these out)")
print("  • Minor currencies unless specifically requested")
print("  • Events without clear time schedules")
print()

print("=" * 80)
print("NEXT STEPS")
print("=" * 80)
print()
print("1. Update calendar file with next week's events")
print("2. Commit and push to GitHub: git add . && git commit -m 'Update calendar' && git push")
print("3. Railway will auto-deploy the updated calendar")
print("4. Verify worker is running on Railway")
print()
print("Then your alerts will work automatically when:")
print("  • 2 hours before each high-impact event")
print("  • 1 hour before each high-impact event")
print("  • 10 minutes before each high-impact event")
print()

