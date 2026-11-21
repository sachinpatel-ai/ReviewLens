import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { SENTIMENT_COLORS } from "../utils/format";

export function SentimentDonut({ distribution }) {
  const data = Object.entries(distribution).map(([name, value]) => ({ name, value }));
  const total = data.reduce((s, d) => s + d.value, 0);
  if (!total) return <p className="muted">No analyzed reviews yet.</p>;
  return (
    <>
      <div className="chart-box">
        <ResponsiveContainer>
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="name" innerRadius={58} outerRadius={90} paddingAngle={2}>
              {data.map((d) => <Cell key={d.name} fill={SENTIMENT_COLORS[d.name]} />)}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="legend">
        {data.map((d) => (
          <span key={d.name}><i style={{ background: SENTIMENT_COLORS[d.name] }} />{d.name} {d.value} ({Math.round((d.value / total) * 100)}%)</span>
        ))}
      </div>
    </>
  );
}

export function RatingBars({ distribution }) {
  const data = Object.entries(distribution).map(([rating, count]) => ({ rating: `${rating}★`, count }));
  if (!data.some((d) => d.count)) return <p className="muted">No valid ratings in this upload.</p>;
  return (
    <div className="chart-box">
      <ResponsiveContainer>
        <BarChart data={data}>
          <CartesianGrid vertical={false} stroke="#e8ecea" />
          <XAxis dataKey="rating" tickLine={false} axisLine={false} />
          <YAxis allowDecimals={false} tickLine={false} axisLine={false} width={28} />
          <Tooltip cursor={{ fill: "#f0f3f2" }} />
          <Bar dataKey="count" name="Reviews" fill="#0e7c86" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function CategoryBars({ distribution }) {
  const data = Object.entries(distribution).map(([name, count]) => ({ name, count }));
  if (!data.length) return <p className="muted">No categories yet.</p>;
  return (
    <div className="chart-box">
      <ResponsiveContainer>
        <BarChart data={data} layout="vertical" margin={{ left: 8 }}>
          <CartesianGrid horizontal={false} stroke="#e8ecea" />
          <XAxis type="number" allowDecimals={false} tickLine={false} axisLine={false} />
          <YAxis type="category" dataKey="name" width={110} tickLine={false} axisLine={false} />
          <Tooltip cursor={{ fill: "#f0f3f2" }} />
          <Bar dataKey="count" name="Reviews" fill="#2c5f6b" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function ThemeList({ themes, color }) {
  if (!themes.length) return <p className="muted">Nothing mentioned yet.</p>;
  const max = Math.max(...themes.map((t) => t.count));
  return themes.map((t) => (
    <div className="theme" key={t.theme}>
      <span>{t.theme}</span>
      <span className="bar"><div style={{ width: `${(t.count / max) * 100}%`, background: color }} /></span>
      <span className="count">{t.count}</span>
    </div>
  ));
}
