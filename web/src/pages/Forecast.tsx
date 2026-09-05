import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { AsyncView, Empty } from "../components/States";
import { backend } from "../lib/api";
import { date, money } from "../lib/format";
import { useAccountId } from "../lib/useAccountId";
import { useAsync } from "../lib/useAsync";

export default function Forecast() {
  const accountId = useAccountId();
  const state = useAsync(
    () =>
      accountId
        ? backend.accountForecast(accountId)
        : Promise.reject(new Error("no account")),
    [accountId],
  );

  if (!accountId) return <Empty label="Select an account to see its forecast." />;

  return (
    <AsyncView
      state={state}
      isEmpty={(data) => data.points.length === 0}
      emptyLabel="The forecast service returned no points."
    >
      {(forecast) => {
        // recharts needs numbers, while the api sends decimals as strings
        const points = forecast.points.map((point) => ({
          date: point.date,
          balance: Number(point.expected_balance),
        }));

        return (
          <div className="space-y-4">
            <div className="flex flex-wrap items-baseline gap-x-6 gap-y-1 text-sm text-muted">
              <span>Horizon {forecast.horizon_days} days</span>
              <span>Model {forecast.model_version}</span>
            </div>

            <div className="rounded-lg border border-line bg-surface p-4">
              <ResponsiveContainer width="100%" height={320}>
                <LineChart data={points} margin={{ top: 8, right: 16, bottom: 8 }}>
                  <CartesianGrid stroke="#e2e8f0" vertical={false} />
                  <XAxis
                    dataKey="date"
                    tickFormatter={date}
                    tick={{ fontSize: 12, fill: "#64748b" }}
                    minTickGap={24}
                  />
                  <YAxis
                    tickFormatter={(value: number) => money(value)}
                    tick={{ fontSize: 12, fill: "#64748b" }}
                    width={90}
                  />
                  <Tooltip
                    formatter={(value) => money(value as number)}
                    labelFormatter={(label) => date(String(label))}
                  />
                  <Line
                    type="monotone"
                    dataKey="balance"
                    stroke="#0f172a"
                    strokeWidth={2}
                    dot={false}
                    name="Expected balance"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        );
      }}
    </AsyncView>
  );
}
