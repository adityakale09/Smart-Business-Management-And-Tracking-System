import { useQuery } from '@tanstack/react-query'
import { analyticsAPI } from '../api/analytics'
import { 
  BarChart, Bar, LineChart, Line, PieChart, Pie, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell 
} from 'recharts'
import { TrendingUp, Package, IndianRupee, ShoppingCart } from 'lucide-react'
import './Analytics.css'

const Analytics = () => {
  const { data: salesTrend, isLoading: salesLoading } = useQuery({
    queryKey: ['sales-trend'],
    queryFn: () => analyticsAPI.getSalesTrend(30, 'day'),
  })

  const { data: inventoryAnalysis, isLoading: inventoryLoading } = useQuery({
    queryKey: ['inventory-analysis'],
    queryFn: () => analyticsAPI.getInventoryAnalysis(),
  })

  // Colors for pie chart
  const COLORS = ['#667eea', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16']

  // Format currency
  const formatCurrency = (value) => `₹${value.toLocaleString('en-IN')}`

  // Custom tooltip for charts
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div style={{ backgroundColor: '#fff', padding: '10px', border: '1px solid #ccc', borderRadius: '4px' }}>
          <p style={{ margin: '0 0 5px 0', fontWeight: 'bold' }}>{label}</p>
          {payload.map((entry, index) => {
            const isRevenue = entry.name.toLowerCase().includes('revenue') || entry.dataKey === 'revenue' || entry.name === 'total_value'
            return (
              <p key={index} style={{ margin: '2px 0', color: entry.color }}>
                {entry.name}: {isRevenue ? formatCurrency(entry.value) : entry.value}
              </p>
            )
          })}
        </div>
      )
    }
    return null
  }

  return (
    <div className="analytics-page">
      <div className="page-header">
        <div>
          <h1>Analytics & Reports</h1>
          <p>Data-driven insights for your business</p>
        </div>
      </div>

      <div className="analytics-grid">
        {/* Sales Trend - Line Chart */}
        <div className="analytics-card full-width">
          <h2><TrendingUp size={20} style={{ marginRight: '8px', verticalAlign: 'middle' }} />Sales Trend (Last 30 Days)</h2>
          {salesLoading ? (
            <div className="chart-loading">Loading chart...</div>
          ) : salesTrend?.data && salesTrend.data.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={salesTrend.data}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis tickFormatter={(value) => value < 100 ? value : `₹${value.toLocaleString('en-IN')}`} />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Line type="monotone" dataKey="revenue" name="Revenue" stroke="#667eea" strokeWidth={2} />
                <Line type="monotone" dataKey="count" name="Sales Count" stroke="#10b981" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="no-data">
              <ShoppingCart size={48} color="#ccc" />
              <p>No sales data available. Add some sales to see the trend!</p>
            </div>
          )}
        </div>

        {/* Sales Revenue Area Chart */}
        <div className="analytics-card">
          <h2><IndianRupee size={20} style={{ marginRight: '8px', verticalAlign: 'middle' }} />Revenue Trend</h2>
          {salesLoading ? (
            <div className="chart-loading">Loading chart...</div>
          ) : salesTrend?.data && salesTrend.data.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={salesTrend.data}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis tickFormatter={(value) => `₹${value.toLocaleString('en-IN')}`} />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Area type="monotone" dataKey="revenue" name="Revenue" stroke="#667eea" fill="#667eea" fillOpacity={0.6} />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="no-data">
              <p>No revenue data available</p>
            </div>
          )}
        </div>

        {/* Inventory by Category - Bar Chart */}
        <div className="analytics-card">
          <h2><Package size={20} style={{ marginRight: '8px', verticalAlign: 'middle' }} />Inventory by Category</h2>
          {inventoryLoading ? (
            <div className="chart-loading">Loading chart...</div>
          ) : inventoryAnalysis?.category_distribution && inventoryAnalysis.category_distribution.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={inventoryAnalysis.category_distribution}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="category" />
                <YAxis />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Bar dataKey="count" name="Products" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="no-data">
              <p>No inventory data available</p>
            </div>
          )}
        </div>

        {/* Category Distribution - Pie Chart */}
        <div className="analytics-card">
          <h2>Category Distribution</h2>
          {inventoryLoading ? (
            <div className="chart-loading">Loading chart...</div>
          ) : inventoryAnalysis?.category_distribution && inventoryAnalysis.category_distribution.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={inventoryAnalysis.category_distribution}
                  dataKey="count"
                  nameKey="category"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label={(entry) => `${entry.category}: ${entry.count}`}
                >
                  {inventoryAnalysis.category_distribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="no-data">
              <p>No category data available</p>
            </div>
          )}
        </div>

        {/* Inventory Value - Pie Chart */}
        <div className="analytics-card">
          <h2>Inventory Value by Category</h2>
          {inventoryLoading ? (
            <div className="chart-loading">Loading chart...</div>
          ) : inventoryAnalysis?.category_distribution && inventoryAnalysis.category_distribution.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={inventoryAnalysis.category_distribution}
                  dataKey="total_value"
                  nameKey="category"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label={(entry) => `${entry.category}: ${formatCurrency(entry.total_value)}`}
                >
                  {inventoryAnalysis.category_distribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="no-data">
              <p>No value data available</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Analytics








