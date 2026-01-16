import { useQuery } from '@tanstack/react-query'
import { analyticsAPI } from '../api/analytics'
import { aiAPI } from '../api/ai'
import { TrendingUp, Package, Users, IndianRupee, AlertTriangle } from 'lucide-react'
import './Dashboard.css'

const Dashboard = () => {
  const { data: dashboardData, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => analyticsAPI.getDashboard(),
  })

  const { data: taskSuggestions } = useQuery({
    queryKey: ['task-suggestions'],
    queryFn: () => aiAPI.getTaskSuggestions(),
    enabled: false, // Disabled - AI automation module not available
    retry: false,
  })

  if (isLoading) {
    return <div className="dashboard-loading">Loading dashboard...</div>
  }

  const stats = dashboardData || {
    sales: { total_revenue: 0, total_sales: 0 },
    inventory: { total_products: 0, low_stock_items: 0 },
    employees: { total_active: 0 },
  }

  const statCards = [
    {
      title: 'Total Revenue',
      value: `₹${stats.sales.total_revenue.toLocaleString('en-IN')}`,
      icon: IndianRupee,
      color: '#10b981',
      subtitle: `${stats.sales.total_sales} sales`,
    },
    {
      title: 'Total Products',
      value: stats.inventory.total_products,
      icon: Package,
      color: '#3b82f6',
      subtitle: `${stats.inventory.low_stock_items} low stock`,
    },
    {
      title: 'Active Employees',
      value: stats.employees.total_active,
      icon: Users,
      color: '#8b5cf6',
      subtitle: 'Currently active',
    },
    {
      title: 'Sales Trend',
      value: '+12%',
      icon: TrendingUp,
      color: '#f59e0b',
      subtitle: 'vs last month',
    },
  ]

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Dashboard</h1>
        <p>Welcome back! Here's what's happening with your business.</p>
      </div>

      <div className="stats-grid">
        {statCards.map((stat, index) => {
          const Icon = stat.icon
          return (
            <div key={index} className="stat-card">
              <div className="stat-icon" style={{ backgroundColor: `${stat.color}20`, color: stat.color }}>
                <Icon size={24} />
              </div>
              <div className="stat-content">
                <h3>{stat.title}</h3>
                <p className="stat-value">{stat.value}</p>
                <p className="stat-subtitle">{stat.subtitle}</p>
              </div>
            </div>
          )
        })}
      </div>

      {taskSuggestions && taskSuggestions.count > 0 && (
        <div className="suggestions-section">
          <div className="section-header">
            <AlertTriangle size={20} color="#f59e0b" />
            <h2>AI Suggestions</h2>
          </div>
          <div className="suggestions-list">
            {taskSuggestions.suggestions.map((suggestion, index) => (
              <div key={index} className="suggestion-card">
                <span className="suggestion-priority">{suggestion.priority}</span>
                <div>
                  <h4>{suggestion.title}</h4>
                  <p>{suggestion.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default Dashboard








