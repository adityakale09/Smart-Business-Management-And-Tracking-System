import { useQuery } from '@tanstack/react-query'
import { analyticsAPI } from '../api/analytics'
import { TrendingUp, Package, Users, IndianRupee } from 'lucide-react'
import './Dashboard.css'

const Dashboard = () => {
  const { data: dashboardData, isLoading, error } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => analyticsAPI.getDashboard(),
  })

  if (isLoading) {
    return <div className="dashboard-loading">Loading dashboard...</div>
  }

  const fallbackStats = {
    sales: { total_revenue: 0, total_sales: 0 },
    inventory: { total_products: 0, low_stock_items: 0 },
    employees: { total_active: 0 },
  }

  const stats = {
    sales: {
      total_revenue: Number(dashboardData?.sales?.total_revenue ?? fallbackStats.sales.total_revenue),
      total_sales: Number(dashboardData?.sales?.total_sales ?? fallbackStats.sales.total_sales),
    },
    inventory: {
      total_products: Number(dashboardData?.inventory?.total_products ?? fallbackStats.inventory.total_products),
      low_stock_items: Number(dashboardData?.inventory?.low_stock_items ?? fallbackStats.inventory.low_stock_items),
    },
    employees: {
      total_active: Number(dashboardData?.employees?.total_active ?? fallbackStats.employees.total_active),
    },
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
        <p>Welcome back!</p>
        {error && <p style={{ color: '#1582cb', marginTop: '8px' }}>Could not refresh live dashboard data.</p>}
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

    </div>
  )
}

export default Dashboard


