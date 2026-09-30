import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { CircleMarker, MapContainer, TileLayer, Tooltip as MapTooltip } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import { COMMUNITY_AREA_COORDS } from '../constants/tables'

export default function ChartView({ table, data }) {
  if (!Array.isArray(data) || data.length === 0) {
    return <p className="chart-empty">No chart data available for this selection.</p>
  }

  if (table === 'hourly_crimes') {
    const rows = [...data]
      .map(row => ({
        ...row,
        hour_num: Number(row.hour),
        crime_count_num: Number(row.crime_count),
      }))
      .filter(row => Number.isFinite(row.hour_num) && Number.isFinite(row.crime_count_num))
      .sort((a, b) => a.hour_num - b.hour_num)

    return (
      <div className="chart-block">
        <div className="chart-title">Crime volume by hour of day</div>
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height={290}>
            <BarChart data={rows}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="hour_num" label={{ value: 'Hour of Day', position: 'insideBottom', offset: -5 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="crime_count_num" fill="#10b981" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    )
  }

  if (table === 'yearly_crimes') {
    const rows = [...data]
      .map(row => ({
        ...row,
        year_num: Number(row.year),
        total_crimes_num: Number(row.total_crimes),
      }))
      .filter(row => Number.isFinite(row.year_num) && Number.isFinite(row.total_crimes_num))
      .sort((a, b) => a.year_num - b.year_num)

    return (
      <div className="chart-block">
        <div className="chart-title">Yearly crime trend</div>
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height={290}>
            <LineChart data={rows}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="year_num" />
              <YAxis />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="total_crimes_num"
                stroke="#2563eb"
                strokeWidth={2.5}
                dot={{ r: 2.5 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    )
  }
  if (table === 'sport_location_crimes') {
  const rows = [...data]
    .map(row => ({
      crime: String(row.crime_category || "Unknown"), 
      total: Number(row.total_crimes)
    }))
    .filter(row => Number.isFinite(row.total))
    .sort((a, b) => b.total - a.total)
    .slice(0, 10);

  return (
    <div className="chart-block">
      <div className="chart-title">
        Crime types at sports arenas and stadiums
      </div>

      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={320}>
          <BarChart
            layout="vertical"
            data={rows}
            margin={{ top: 10, right: 10, left: -50, bottom: 10 }} 
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />

            <XAxis type="number" tick={{ fontSize: 11 }} />

            <YAxis
              type="category"
              dataKey="crime"
              width={180}
              tick={{ fontSize: 11 }}
            />

            <Tooltip formatter={(value) => value.toLocaleString()} />

            <Bar
              dataKey="total"
              fill="#ef4444"
              radius={[0, 6, 6, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}


  if (table === "downtown_vs_residential_theft_robbery") {
    const rows = [...data].map(row => ({
      area: String(row.area_type),
      rate: Number(row.rate),
      total: Number(row.total_crimes),
      tr: Number(row.tr_crimes)
    }));
  
    return (
      <div className="chart-block">
        <div className="chart-title">
          Theft and Robbery Rate: Downtown vs Residential Areas
        </div>
  
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height={320}>
            <BarChart
              data={rows}
              margin={{ top: 20, right: 40, left: 20, bottom: 20 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
  
              <XAxis
                dataKey="area"
                tick={{ fontSize: 12 }}
              />
  
              <YAxis
                tickFormatter={(v) => (v * 100).toFixed(0) + "%"}
              />
  
              <Tooltip
                formatter={(v) => (v * 100).toFixed(1) + "%"}
                labelFormatter={(label) => `${label} Area`}
              />
  
              <Bar
                dataKey="rate"
                fill="#ef4444"
                radius={[6,6,0,0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    );
  }
  if (table === "crimes_by_location_and_type") {
    const rows = [...data]
      .map(row => ({
        location: String(row.location_category),
        crime: String(row.primary_type),
        total: Number(row.total)
      }))
      .sort((a, b) => b.total - a.total);
  
    return (
      <div className="chart-block">
        <div className="chart-title">
          Most Common Crime Type by Location Category
        </div>
  
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height={420}>
            <BarChart
              data={rows}
              layout="vertical"
              margin={{ top: 20, right: 10, left: -40, bottom: 20 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
  
              <XAxis type="number" />
  
              <YAxis
                type="category"
                dataKey="location"
                width={140}
                tick={{ fontSize: 11 }}
              />
  
              <Tooltip
                formatter={(value, name, props) =>
                  [`${value.toLocaleString()} crimes`, props.payload.crime]
                }
              />
  
              <Bar
                dataKey="total"
                fill="#6366f1"
                radius={[0,6,6,0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    );
  }

  if (table === 'crimes_by_location') {
    const rows = [...data]
      .map(row => ({
        ...row,
        location_category: String(row.location_category || 'Unknown'),
        total_crimes_num: Number(row.total_crimes),
      }))
      .filter(row => Number.isFinite(row.total_crimes_num))
      .sort((a, b) => b.total_crimes_num - a.total_crimes_num)
      .slice(0, 10);

    return (
      <div className="chart-block">
        <div className="chart-title">
          Top 10 Location Types by Total Crime
        </div>
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height={400}>
            <BarChart
              layout="vertical"
              data={rows}
              margin={{ top: 20, right: 30, left: 100, bottom: 20 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              {/* X-axis is the total crime scale */}
              <XAxis type="number" tick={{ fontSize: 12 }} />
              {/* Y-axis shows categories on the left */}
              <YAxis
                type="category"
                dataKey="location_category"
                tick={{ fontSize: 12 }}
              />
              <Tooltip formatter={(value) => value.toLocaleString()} />
              <Bar
                dataKey="total_crimes_num"
                fill="#0a70d5"
                radius={[6, 6, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    );
  }

  if (table === 'time_period_crimes') {
  const hoursPerPeriod = {
    'Overnight': 8, // 12AM–7:59AM
    'Daytime': 8,   // 8AM–3:59PM
    'Evening': 8    // 4PM–11:59PM
  };

  const rows = [...data]
    .map(row => ({
      period: String(row.time_period || 'Unknown'),
      avg_crimes: Number(row.total_crimes) / (hoursPerPeriod[row.time_period] || 1)
    }))
    .filter(row => Number.isFinite(row.avg_crimes));

  return (
    <div className="chart-block">
      <div className="chart-title">Average hourly crime by time of day</div>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={260}>
          <BarChart layout="vertical" data={rows} margin={{ top: 10, right: 20, left: -100, bottom: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis type="number" tick={{ fontSize: 12 }} />
            <YAxis type="category" dataKey="period" tick={{ fontSize: 12 }} width={180} />
            <Tooltip formatter={value => value.toFixed(0)} />
            <Bar dataKey="avg_crimes" fill="#3b82f6" radius={[0,6,6,0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}


 if (table === 'holiday_vs_nonholiday') {
  const rows = [...data]
    .map(row => {
      let days = 1;
      if (row.day_type === 'Holiday') days = 11 * 20;       
      else if (row.day_type === 'Non-Holiday') days = 365 * 20 - 220; 
      return {
        day_type: String(row.day_type || 'Unknown'),
        avg_crimes_per_day: Number(row.total_crimes) / days,
      };
    })
    .filter(row => Number.isFinite(row.avg_crimes_per_day));

  return (
    <div className="chart-block">
      <div className="chart-title">Average Daily Crimes: Holiday vs Non-Holiday</div>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={290}>
          <BarChart data={rows}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="day_type" />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip formatter={(value) => value.toLocaleString()} />
            <Bar dataKey="avg_crimes_per_day" fill="#f43f5e" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}


  if (table === 'community_area_crimes') {
    const topRows = [...data]
      .map(row => ({
        ...row,
        community_area_text: String(row.community_area),
        total_crimes_num: Number(row.total_crimes),
      }))
      .filter(row => Number.isFinite(row.total_crimes_num))
      .sort((a, b) => b.total_crimes_num - a.total_crimes_num)
      .slice(0, 15)

    const mapRows = topRows.filter(row => COMMUNITY_AREA_COORDS[row.community_area_text])

    return (
      <div className="chart-block">
        <div className="chart-title">Top community areas by reported crime</div>
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height={290}>
            <BarChart data={topRows}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="community_area_text" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="total_crimes_num" fill="#2563eb" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="map-wrap">
          <MapContainer center={[41.8781, -87.6298]} zoom={10} className="crime-map">
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {mapRows.map(row => {
              const [lat, lng] = COMMUNITY_AREA_COORDS[row.community_area_text]
              return (
                <CircleMarker
                  key={row.community_area_text}
                  center={[lat, lng]}
                  radius={10}
                  pathOptions={{ color: '#1d4ed8', fillColor: '#60a5fa', fillOpacity: 0.52 }}
                >
                  <MapTooltip>
                    Community Area {row.community_area_text}: {row.total_crimes_num} crimes
                  </MapTooltip>
                </CircleMarker>
              )
            })}
          </MapContainer>
        </div>
      </div>
    )
  }

if (table === 'thanksgiving_vs_nonthanksgiving_by_type') {
  const THANKSGIVING_DAYS = 1 * 20;
  const NON_THANKSGIVING_DAYS = (365 - 1) * 20;

  const crimeTypes = ["BATTERY", "THEFT", "CRIMINAL DAMAGE", "ASSAULT"];

  const groupedData = crimeTypes.map(type => {
    const thanksgivingRow = data.find(
      row => row.primary_type === type && row.day_type === 'Thanksgiving'
    );

    const nonThanksgivingRow = data.find(
      row => row.primary_type === type && row.day_type === 'Non-Thanksgiving'
    );

    const thanksgivingPerDay = thanksgivingRow
      ? Number(thanksgivingRow.total) / THANKSGIVING_DAYS
      : 0;

    const nonThanksgivingPerDay = nonThanksgivingRow
      ? Number(nonThanksgivingRow.total) / NON_THANKSGIVING_DAYS
      : 0;

    return {
      crime: type,
      Thanksgiving: thanksgivingPerDay,
      "Non-Thanksgiving": nonThanksgivingPerDay
    };
  });

  return (
    <div className="chart-block">
      <div className="chart-title">
        Crime Comparison: Thanksgiving vs Non-Thanksgiving (Average per Day)
      </div>

      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={320}>
          <BarChart
            data={groupedData}
            margin={{ top: 20, right: 40, left: 10, bottom: 40 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />

            <XAxis dataKey="crime" angle={0} textAnchor="end" height={80} />

            <YAxis tick={{ fontSize: 12 }} />

            <Tooltip
              formatter={(value) => `${value.toFixed(2)} per day`}
            />

            <Bar dataKey="Thanksgiving" fill="#f2a50c" radius={[6,6,0,0]} />

            <Bar dataKey="Non-Thanksgiving" fill="#655005" radius={[6,6,0,0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

if (table === 'airport_theft_count_comparison') {
  const rows = [...data]
    .map(row => ({
      location_type: String(row.location_type || 'Unknown'),
      theft_rate_num: Number(row.theft_rate),
    }))
    .filter(row => Number.isFinite(row.theft_rate_num))
    .sort((a, b) => b.theft_rate_num - a.theft_rate_num)

  return (
    <div className="chart-block">
      <div className="chart-title">Theft Rate by Location Type</div>

      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={290}>
          <BarChart data={rows}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />

            <XAxis dataKey="location_type" />

            <YAxis
              tickFormatter={(v) => (v * 100).toFixed(0) + "%"}
              tick={{ fontSize: 12 }}
            />

            <Tooltip
              formatter={(v) => (v * 100).toFixed(1) + "%"}
            />

            <Bar
              dataKey="theft_rate_num"
              fill="#0a70d5"
              radius={[6,6,0,0]}
            />

          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
if (table === 'crimes_by_location') {
  const rows = [...data]
    .map(row => ({
      ...row,
      location_category: String(row.location_category || "Unknown"),
      total_crimes_num: Number(row.total_crimes)
    }))
    .filter(row => Number.isFinite(row.total_crimes_num))
    .sort((a, b) => b.total_crimes_num - a.total_crimes_num)
    .slice(0, 10); // Top 10

  return (
    <div className="chart-block">
      <div className="chart-title">
        Top 10 Location Types by Total Crime
      </div>

      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={400}>
          <BarChart
            layout="vertical"
            data={rows}
            margin={{ top: 20, right: 30, left: 100, bottom: 20 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />

            {/* X-axis is the total crime scale */}
            <XAxis type="number" tick={{ fontSize: 12 }} />

            {/* Y-axis shows categories on the left */}
            <YAxis 
              type="category" 
              dataKey="location_category" 
              tick={{ fontSize: 12 }}
            />

            <Tooltip
              formatter={(value) => value.toLocaleString()}
            />

            <Bar
              dataKey="total_crimes_num"
              fill="#0a70d5"
              radius={[6, 6, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}


if (table === 'season_crimes') {
  const rows = [...data]
    .map(row => {
      let months = 1;
      if (row.season === 'Summer') months = 3;
      else if (row.season === 'Late Winter') months = 2;
      else if (row.season === 'Other') months = 7;

      return {
        season: String(row.season || 'Unknown'),
        avg_per_month: Number(row.total_crimes) / months,
      };
    })
    .filter(row => Number.isFinite(row.avg_per_month))
    .sort((a, b) => b.avg_per_month - a.avg_per_month);

  return (
    <div className="chart-block">
      <div className="chart-title">Average monthly crime by season</div>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={290}>
          <BarChart data={rows}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="season" />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip formatter={(value) => value.toLocaleString()} />
            <Bar dataKey="avg_per_month" fill="#8b5cf6" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

  if (table === 'theft_by_location') {
  const rows = [...data]
    .map(row => ({
      location: String(row.location_description || 'Unknown'),
      theft_rate: Number(row.total_thefts) / Number(row.total_crimes || 1),
    }))
    .filter(row => Number.isFinite(row.theft_rate))
    .sort((a, b) => b.theft_rate - a.theft_rate)
    .slice(0, 10)

  return (
    <div className="chart-block">
      <div className="chart-title">Theft rate by location</div>

      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={320}>
          <BarChart
            layout="vertical"   
            data={rows}
            margin={{ top: 10, right: 10, left: 40, bottom: 10 }}  
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />

            <XAxis type="number" tick={{ fontSize: 12 }} />
            <YAxis
              type="category"
              dataKey="location"
              width={120}
              tick={{ fontSize: 12 }}
            />

            <Tooltip
              formatter={(value) => (value * 100).toFixed(2) + '%'} 
            />

            <Bar
              dataKey="theft_rate"
              fill="#f59e0b"
              radius={[0, 6, 6, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}



  if (table === 'great_recession_by_type') {
    const rows = [...data]
      .map(row => ({
        crime: String(row.primary_type || "Unknown"),
        total: Number(row.total)
      }))
      .filter(row => Number.isFinite(row.total))
      .sort((a, b) => b.total - a.total)
      .slice(0, 10)
  
    return (
      <div className="chart-block">
        <div className="chart-title">
          Most common crime types during the Great Recession (2007–2009)
        </div>
  
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height={320}>
            <BarChart
              layout="vertical"
              data={rows}
              margin={{ top: 10, right: 10, left: -75, bottom: 10 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
  
              <XAxis
                type="number"
                tick={{ fontSize: 11 }}
              />
  
              <YAxis
                type="category"
                dataKey="crime"
                width={220}
                tick={{ fontSize: 11 }}
              />
  
              <Tooltip />
  
              <Bar
                dataKey="total"
                fill="#3b82f6"
                radius={[0, 6, 6, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    )
  }

  if (table === 'monthly_crimes') {
  const monthNames = [
    'Jan','Feb','Mar','Apr','May','Jun',
    'Jul','Aug','Sep','Oct','Nov','Dec'
  ]

  const rows = [...data]
    .map(row => ({
      month_num: Number(row.month),
      total_crimes_num: Number(row.total_crimes),
      month_label: monthNames[Number(row.month) - 1]
    }))
    .filter(row => Number.isFinite(row.month_num) && Number.isFinite(row.total_crimes_num))
    .sort((a, b) => a.month_num - b.month_num)

  return (
    <div className="chart-block">
      <div className="chart-title">Crime trends by month</div>

      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={290}>
          <BarChart data={rows}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />

            <XAxis dataKey="month_label" />

            <YAxis />

            <Tooltip />

            <Bar
              dataKey="total_crimes_num"
              fill="#6366f1"
              radius={[6,6,0,0]}
            />

          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

if (table === 'christmas_vs_nonchristmas_by_type') {
  const CHRISTMAS_DAYS = 31;
  const NON_CHRISTMAS_DAYS = 365 - 31;

  const crimeTypes = ["THEFT", "BURGLARY", "ROBBERY"];
  const groupedData = crimeTypes.map(type => {
    const christmasRow = data.find(
      row => row.primary_type === type && row.day_type === 'Christmas'
    );
    const nonChristmasRow = data.find(
      row => row.primary_type === type && row.day_type === 'Non-Christmas'
    );

    const christmasPerDay = christmasRow ? Number(christmasRow.total) / CHRISTMAS_DAYS : 0;
    const nonChristmasPerDay = nonChristmasRow ? Number(nonChristmasRow.total) / NON_CHRISTMAS_DAYS : 0;

    return {
      crime: type,
      Christmas: christmasPerDay,
      "Non-Christmas": nonChristmasPerDay
    };
  });

  return (
    <div className="chart-block">
      <div className="chart-title">Crime Comparison: Christmas vs Non-Christmas (Per Day)</div>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={320}>
          <BarChart
            data={groupedData}
            margin={{ top: 20, right: 40, left: 10, bottom: 40 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="crime" angle={0} textAnchor="end" height={80} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip
              formatter={(value, name) => `${value.toFixed(2)} per day`}
            />
            <Bar dataKey="Christmas" fill="#dc2626" radius={[6,6,0,0]} />
            <Bar dataKey="Non-Christmas" fill="#0d9488" radius={[6,6,0,0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

if (table === 'halloween_vs_nonhalloween_by_type') {
  const HALLOWEEN_DAYS = 1 * 20;     
  const NON_HALLOWEEN_DAYS = (365 - 1) * 20; 

  const crimeTypes = ["ASSAULT", "BATTERY", "PUBLIC PEACE VIOLATION"];

  const groupedData = crimeTypes.map(type => {
    const halloweenRow = data.find(
      row => row.primary_type === type && row.day_type === 'Halloween'
    );
    const nonHalloweenRow = data.find(
      row => row.primary_type === type && row.day_type === 'Non-Halloween'
    );

    const halloweenPerDay = halloweenRow ? Number(halloweenRow.total) / HALLOWEEN_DAYS : 0;
    const nonHalloweenPerDay = nonHalloweenRow ? Number(nonHalloweenRow.total) / NON_HALLOWEEN_DAYS : 0;

    return {
      crime: type,
      Halloween: halloweenPerDay,
      "Non-Halloween": nonHalloweenPerDay
    };
  });

  return (
    <div className="chart-block">
      <div className="chart-title">
        Crime Comparison: Halloween vs Non-Halloween (Average per Day)
      </div>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={320}>
          <BarChart
            data={groupedData}
            margin={{ top: 20, right: 40, left: 10, bottom: 40 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="crime" angle={0} textAnchor="end" height={80} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip
              formatter={(value, name) => `${value.toFixed(2)} per day`}
            />
            <Bar dataKey="Halloween" fill="#a3a3a3" radius={[6, 6, 0, 0]} />
            <Bar dataKey="Non-Halloween" fill="#14b8a6" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
  
if (table === 'transit_vs_commercial_robbery_count') {
  const rows = [...data]
    .map(row => ({
      ...row,
      location_type: String(row.location_type || 'Unknown'),
      robbery_count_num: Number(row.robbery_count),
      total_crimes_num: Number(row.total_crimes),
      robbery_rate_num: Number(row.robbery_rate),
    }))
    .filter(row => Number.isFinite(row.robbery_rate_num))

  return (
    <div className="chart-block">
      <div className="chart-title">Robbery rate: Transit vs Commercial</div>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={290}>
          <BarChart data={rows}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="location_type" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="robbery_rate_num" fill="#ef4444" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
  if (table === 'season_crimes') {
  const monthsPerSeason = {
    "Summer": 3,
    "Late Winter": 2,
    "Other": 7,
    "Unknown": 1,
  };

  const rows = [...data]
    .map(row => {
      const season = String(row.season || 'Unknown');
      const total_crimes_num = Number(row.total_crimes);
      const avg_crimes_per_month = Number.isFinite(total_crimes_num) 
        ? total_crimes_num / (monthsPerSeason[season] || 1)
        : 0;
      return {
        ...row,
        season,
        total_crimes_num,
        avg_crimes_per_month,
      };
    })
    .filter(row => Number.isFinite(row.avg_crimes_per_month))
    .sort((a, b) => b.avg_crimes_per_month - a.avg_crimes_per_month);

  return (
    <div className="chart-block">
      <div className="chart-title">Average Crime per Month by Season</div>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={290}>
          <BarChart data={rows}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="season" />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip formatter={(v) => v.toFixed(1)} />
            <Bar dataKey="avg_crimes_per_month" fill="#8b5cf6" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

if (table === 'airport_theft_count_comparison') {
  const rows = [...data]
    .map(row => ({
      ...row,
      location_type: String(row.location_type || 'Unknown'),
      theft_rate_num: Number(row.theft_rate),
    }))
    .filter(row => Number.isFinite(row.theft_rate_num))
    .sort((a, b) => b.theft_rate_num - a.theft_rate_num)

  return (
    <div className="chart-block">
      <div className="chart-title">Theft rate: Airport vs Other locations</div>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={290}>
          <BarChart data={rows}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="location_type" />
            <YAxis />
            <Tooltip 
              formatter={(value) => `${(value * 100).toFixed(2)}%`}
            />
            <Bar dataKey="theft_rate_num" fill="#f97316" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}


  return (
    <div className="chart-block">
      <div className="chart-title">Visualization</div>
      <p className="chart-empty">A chart for this question is coming soon.</p>
    </div>
  )
}

