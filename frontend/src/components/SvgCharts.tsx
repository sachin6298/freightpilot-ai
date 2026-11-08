// Hand-built SVG Charts matching FreightPilot AI 3-Colour Specification
// Navy: #14213D, Cream: #F4EDE0, Coral: #FF6B5B

export function ShipmentVolumeChart({
  points,
  height = 180,
}: {
  points?: Array<{ label: string; value: number }>;
  height?: number;
}) {
  const data = points && points.length >= 2 ? points : [
    { label: 'Apr', value: 42 },
    { label: 'May', value: 78 },
    { label: 'Jun', value: 65 },
    { label: 'Jul', value: 110 },
    { label: 'Aug', value: 95 },
    { label: 'Sep', value: 138 },
    { label: 'Oct', value: 128 },
  ];

  const maxVal = Math.max(...data.map((d) => d.value), 160);
  const width = 560;
  const paddingX = 36;
  const paddingY = 24;
  const chartW = width - paddingX * 2;
  const chartH = height - paddingY * 2;

  const coords = data.map((d, i) => ({
    x: paddingX + (i / (data.length - 1)) * chartW,
    y: paddingY + chartH - (d.value / maxVal) * chartH,
    ...d,
  }));

  // Build smooth cubic bezier curve
  let curvePath = `M ${coords[0].x},${coords[0].y}`;
  for (let i = 0; i < coords.length - 1; i++) {
    const current = coords[i];
    const next = coords[i + 1];
    const controlX1 = current.x + (next.x - current.x) / 2;
    const controlY1 = current.y;
    const controlX2 = current.x + (next.x - current.x) / 2;
    const controlY2 = next.y;
    curvePath += ` C ${controlX1},${controlY1} ${controlX2},${controlY2} ${next.x},${next.y}`;
  }

  const areaPath = `${curvePath} L ${coords[coords.length - 1].x},${height - paddingY} L ${coords[0].x},${height - paddingY} Z`;

  return (
    <div className="svg-area-chart-wrap">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
        className="svg-area-chart"
      >
        <defs>
          <linearGradient id="volumeAreaGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#FF6B5B" stopOpacity="0.4" />
            <stop offset="65%" stopColor="#FF6B5B" stopOpacity="0.08" />
            <stop offset="100%" stopColor="#14213D" stopOpacity="0.0" />
          </linearGradient>
          <linearGradient id="volumeLineGrad" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#FF6B5B" />
            <stop offset="70%" stopColor="#FF8A76" />
            <stop offset="100%" stopColor="#F4EDE0" />
          </linearGradient>
          <filter id="lineGlow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur in="SourceGraphic" stdDeviation="3" />
          </filter>
        </defs>

        {/* Horizontal gridlines */}
        <line
          x1={paddingX}
          y1={paddingY}
          x2={width - paddingX}
          y2={paddingY}
          stroke="rgba(244, 237, 224, 0.08)"
          strokeDasharray="4 4"
        />
        <line
          x1={paddingX}
          y1={paddingY + chartH / 2}
          x2={width - paddingX}
          y2={paddingY + chartH / 2}
          stroke="rgba(244, 237, 224, 0.08)"
          strokeDasharray="4 4"
        />
        <line
          x1={paddingX}
          y1={height - paddingY}
          x2={width - paddingX}
          y2={height - paddingY}
          stroke="rgba(244, 237, 224, 0.15)"
        />

        {/* Area fill */}
        <path d={areaPath} fill="url(#volumeAreaGrad)" />

        {/* Glowing curve shadow */}
        <path
          d={curvePath}
          fill="none"
          stroke="url(#volumeLineGrad)"
          strokeWidth="4"
          filter="url(#lineGlow)"
          opacity="0.5"
        />

        {/* Main curve stroke */}
        <path
          d={curvePath}
          fill="none"
          stroke="url(#volumeLineGrad)"
          strokeWidth="2.8"
          strokeLinecap="round"
        />

        {/* Data points */}
        {coords.map((pt) => (
          <g key={pt.label} className="chart-point-group">
            <circle cx={pt.x} cy={pt.y} r="5" fill="#FF6B5B" stroke="#14213D" strokeWidth="2.5" />
            <circle cx={pt.x} cy={pt.y} r="2" fill="#F4EDE0" />
            <text
              x={pt.x}
              y={height - 6}
              textAnchor="middle"
              fill="rgba(244, 237, 224, 0.75)"
              fontSize="11"
              fontFamily="Inter, sans-serif"
            >
              {pt.label}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}

export function ShipmentsByModeChart({
  counts,
  total = 128,
}: {
  counts?: Record<string, number>;
  total?: number;
}) {
  const modes = [
    { label: 'Sea', count: counts?.['Sea'] ?? 66, pct: 52, color: '#FF6B5B' },
    { label: 'Air', count: counts?.['Air'] ?? 31, pct: 24, color: '#F4EDE0' },
    { label: 'Road', count: counts?.['Road'] ?? 21, pct: 16, color: 'rgba(255, 107, 91, 0.65)' },
    { label: 'Rail', count: counts?.['Rail'] ?? 10, pct: 8, color: 'rgba(244, 237, 224, 0.4)' },
  ];

  const size = 150;
  const strokeWidth = 20;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;

  let accumulatedPercent = 0;

  return (
    <div className="svg-donut-container">
      <div className="svg-donut-graphic">
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="svg-donut">
          {/* Base track */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="rgba(244, 237, 224, 0.08)"
            strokeWidth={strokeWidth}
          />
          {modes.map((m) => {
            const percent = m.pct / 100;
            const strokeDasharray = `${percent * circumference} ${circumference}`;
            const strokeDashoffset = -accumulatedPercent * circumference;
            accumulatedPercent += percent;

            return (
              <circle
                key={m.label}
                cx={size / 2}
                cy={size / 2}
                r={radius}
                fill="none"
                stroke={m.color}
                strokeWidth={strokeWidth}
                strokeDasharray={strokeDasharray}
                strokeDashoffset={strokeDashoffset}
                transform={`rotate(-90 ${size / 2} ${size / 2})`}
                className="donut-segment"
              >
                <title>{`${m.label}: ${m.pct}%`}</title>
              </circle>
            );
          })}
        </svg>
        <div className="donut-center-stat">
          <strong>{total}</strong>
          <span>Total</span>
        </div>
      </div>
      <div className="donut-legend">
        {modes.map((m) => (
          <div className="legend-row" key={m.label}>
            <span className="legend-dot" style={{ background: m.color }} />
            <span className="legend-label">{m.label}</span>
            <strong className="legend-pct">{m.pct}%</strong>
          </div>
        ))}
      </div>
    </div>
  );
}

export function SpendTrendBarChart({
  items,
}: {
  items?: Array<{ month: string; amount: number }>;
}) {
  const data = items || [
    { month: 'Apr', amount: 85000 },
    { month: 'May', amount: 125000 },
    { month: 'Jun', amount: 98000 },
    { month: 'Jul', amount: 168000 },
    { month: 'Aug', amount: 142000 },
    { month: 'Sep', amount: 195000 },
    { month: 'Oct', amount: 248320 },
  ];

  const maxVal = 260000;
  const height = 180;
  const width = 520;
  const paddingX = 36;
  const paddingY = 24;
  const chartW = width - paddingX * 2;
  const chartH = height - paddingY * 2;
  const barWidth = 32;
  const step = chartW / data.length;

  return (
    <div className="svg-bar-chart-wrap">
      <svg viewBox={`0 0 ${width} ${height}`} className="svg-bar-chart">
        <defs>
          <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#FF6B5B" />
            <stop offset="100%" stopColor="rgba(255, 107, 91, 0.45)" />
          </linearGradient>
        </defs>

        {/* Horizontal gridlines */}
        <line x1={paddingX} y1={paddingY} x2={width - paddingX} y2={paddingY} stroke="rgba(244, 237, 224, 0.08)" strokeDasharray="4 4" />
        <line x1={paddingX} y1={paddingY + chartH / 2} x2={width - paddingX} y2={paddingY + chartH / 2} stroke="rgba(244, 237, 224, 0.08)" strokeDasharray="4 4" />
        <line x1={paddingX} y1={height - paddingY} x2={width - paddingX} y2={height - paddingY} stroke="rgba(244, 237, 224, 0.15)" />

        {data.map((d, i) => {
          const barH = (d.amount / maxVal) * chartH;
          const x = paddingX + i * step + (step - barWidth) / 2;
          const y = paddingY + chartH - barH;

          return (
            <g key={d.month} className="bar-group">
              <rect
                x={x}
                y={y}
                width={barWidth}
                height={barH}
                rx="6"
                fill="url(#barGrad)"
                className="animated-bar"
              >
                <title>{`${d.month}: $${d.amount.toLocaleString()}`}</title>
              </rect>
              <text
                x={x + barWidth / 2}
                y={height - 6}
                textAnchor="middle"
                fill="rgba(244, 237, 224, 0.75)"
                fontSize="11"
                fontFamily="Inter, sans-serif"
              >
                {d.month}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

export function RiskGauge({ score = 23 }: { score?: number }) {
  const radius = 64;
  const stroke = 14;
  const size = 160;
  const arcLength = Math.PI * radius;
  const safeScore = Math.min(Math.max(score, 0), 100);
  const strokeDashoffset = arcLength * (1 - safeScore / 100);

  return (
    <div className="svg-gauge-wrap">
      <svg width={size} height={96} viewBox={`0 0 ${size} 96`} className="svg-gauge">
        <defs>
          <linearGradient id="gaugeGrad" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#F4EDE0" stopOpacity="0.6" />
            <stop offset="50%" stopColor="rgba(255, 107, 91, 0.7)" />
            <stop offset="100%" stopColor="#FF6B5B" />
          </linearGradient>
        </defs>
        {/* Base Track */}
        <path
          d={`M 16,88 A ${radius},${radius} 0 0,1 144,88`}
          fill="none"
          stroke="rgba(244, 237, 224, 0.12)"
          strokeWidth={stroke}
          strokeLinecap="round"
        />
        {/* Fill Arc */}
        <path
          d={`M 16,88 A ${radius},${radius} 0 0,1 144,88`}
          fill="none"
          stroke="url(#gaugeGrad)"
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={arcLength}
          strokeDashoffset={strokeDashoffset}
          className="gauge-fill-arc"
        />
      </svg>
      <div className="gauge-score-readout">
        <strong>{score}</strong>
        <span>Active Alerts</span>
      </div>
    </div>
  );
}

// Keep aliases for backward compatibility
export const SvgDonutChart = ShipmentsByModeChart;
export const SvgAreaChart = ShipmentVolumeChart;
export const SvgRiskGauge = RiskGauge;
export const SvgBarComparison = SpendTrendBarChart;
