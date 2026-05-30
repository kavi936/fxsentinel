import React from 'react';
import IndicatorMiniChart from '../charts/IndicatorMiniChart.jsx';

export default function AnalysisContextChart({ chart }) {
  if (!chart || !Array.isArray(chart.chartData) || chart.chartData.length < 2) {
    return null;
  }

  const chartKey = chart.id || 'context';

  return (
    <section className="analysis-context-chart-section" aria-label="Macro indicator context">
      <h3 className="section-header">Macro context</h3>
      <div className="analysis-context-chart-card">
        <div className="analysis-context-chart-header">
          <div className="analysis-context-chart-title">{chart.title}</div>
          {chart.currentValue && (
            <div className="analysis-context-chart-value">{chart.currentValue}</div>
          )}
        </div>
        {(chart.asOf || chart.source) && (
          <div className="analysis-context-chart-meta">
            {chart.asOf && <span>As of {chart.asOf}</span>}
            {chart.asOf && chart.source && <span> · </span>}
            {chart.source && <span>{chart.source}</span>}
          </div>
        )}
        <IndicatorMiniChart
          chartId={`analysis-${chartKey}`}
          chartData={chart.chartData}
          chartDates={chart.chartDates}
          showTargetLine={Boolean(chart.showTargetLine)}
          targetValue={chart.targetValue ?? 2}
          indicatorId={chart.id}
          variant="analysis-compact"
        />
        {chart.caption && (
          <p className="analysis-context-chart-caption">{chart.caption}</p>
        )}
      </div>
    </section>
  );
}
