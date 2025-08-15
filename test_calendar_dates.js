// Test script to verify calendar date filtering logic
console.log('Testing Calendar Date Filtering Logic');
console.log('=====================================');

// Simulate the handleQuickSelect logic
function testQuickSelect(option) {
  const today = new Date();
  const dayOfWeek = today.getDay();
  let startDate, endDate;

  switch (option) {
    case 'today':
      startDate = new Date(today);
      endDate = new Date(today);
      break;
    case 'yesterday':
      startDate = new Date(today.getTime() - 24 * 60 * 60 * 1000);
      endDate = new Date(today.getTime() - 24 * 60 * 60 * 1000);
      break;
    case 'tomorrow':
      startDate = new Date(today.getTime() + 24 * 60 * 60 * 1000);
      endDate = new Date(today.getTime() + 24 * 60 * 60 * 1000);
      break;
    case 'this-week':
      startDate = new Date(today.getTime() - dayOfWeek * 24 * 60 * 60 * 1000);
      endDate = new Date(startDate.getTime() + 6 * 24 * 60 * 60 * 1000);
      break;
    case 'last-week':
      const lastWeekStart = new Date(today.getTime() - (dayOfWeek + 7) * 24 * 60 * 60 * 1000);
      startDate = lastWeekStart;
      endDate = new Date(lastWeekStart.getTime() + 6 * 24 * 60 * 60 * 1000);
      break;
    case 'next-week':
      const nextWeekStart = new Date(today.getTime() + (7 - dayOfWeek) * 24 * 60 * 60 * 1000);
      startDate = nextWeekStart;
      endDate = new Date(nextWeekStart.getTime() + 6 * 24 * 60 * 60 * 1000);
      break;
    case 'this-month':
      startDate = new Date(today.getFullYear(), today.getMonth(), 1);
      endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0);
      break;
    case 'last-month':
      startDate = new Date(today.getFullYear(), today.getMonth() - 1, 1);
      endDate = new Date(today.getFullYear(), today.getMonth(), 0);
      break;
    case 'next-month':
      startDate = new Date(today.getFullYear(), today.getMonth() + 1, 1);
      endDate = new Date(today.getFullYear(), today.getMonth() + 2, 0);
      break;
    default:
      startDate = today;
      endDate = today;
  }

  return {
    option,
    startDate: startDate.toISOString().split('T')[0],
    endDate: endDate.toISOString().split('T')[0],
    startDateObj: startDate,
    endDateObj: endDate
  };
}

// Test all quick select options
const options = ['today', 'yesterday', 'tomorrow', 'this-week', 'last-week', 'next-week', 'this-month', 'last-month', 'next-month'];

console.log('Current date:', new Date().toISOString().split('T')[0]);
console.log('Day of week:', new Date().getDay()); // 0 = Sunday, 1 = Monday, etc.
console.log('');

options.forEach(option => {
  const result = testQuickSelect(option);
  console.log(`${option.padEnd(12)}: ${result.startDate} to ${result.endDate}`);
});

console.log('');
console.log('Testing API calls with different date ranges:');

// Test API calls with different date ranges
const testRanges = [
  { start: '2025-08-13', end: '2025-08-13' },
  { start: '2025-08-20', end: '2025-08-25' },
  { start: '2025-08-01', end: '2025-08-31' }
];

testRanges.forEach(range => {
  console.log(`Testing range: ${range.start} to ${range.end}`);
  // In a real test, you would make an API call here
});
