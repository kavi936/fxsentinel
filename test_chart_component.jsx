import React from 'react';
import { createRoot } from 'react-dom/client';
import EconomicChartPopup from './src/components/EconomicChartPopup.jsx';

// Test data
const testEvent = {
  title: "CPI",
  currency: "USD",
  impact: "high"
};

// Test component
function TestApp() {
  const [isOpen, setIsOpen] = React.useState(false);

  return (
    <div>
      <h1>Chart Popup Test</h1>
      <button onClick={() => setIsOpen(true)}>Open Chart Popup</button>
      
      <EconomicChartPopup
        event={testEvent}
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
      />
    </div>
  );
}

// Render test
const container = document.getElementById('root');
if (container) {
  const root = createRoot(container);
  root.render(<TestApp />);
}
