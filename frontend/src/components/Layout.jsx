import { Outlet, Link, useLocation } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { useTheme } from '../context/ThemeContext'
import { LogOut, LayoutDashboard, ShoppingCart, Package, Users, BarChart3, Receipt, Settings, UserCog, Moon, Sun, Shield, Building2 } from 'lucide-react'
import './Layout.css'

const Layout = () => {
  const { user, logout } = useAuthStore()
  const { theme, toggleTheme } = useTheme()
  const location = useLocation()
  const isSuperAdmin = user?.role === 'super_admin'
  const isAdmin = user?.role === 'admin'

  // Platform-level navigation — super_admin only (manages businesses, not org data)
  const platformNavigation = [
    { name: 'Organizations', path: '/organizations', icon: Building2 },
    { name: 'User Management', path: '/users', icon: UserCog },
    { name: 'Audit Logs', path: '/audit-logs', icon: Shield },
  ]

  // Org-level navigation — visible to regular admins, managers, employees
  const navigation = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Sales', path: '/sales', icon: ShoppingCart },
    { name: 'Inventory', path: '/inventory', icon: Package },
    { name: 'Receipts', path: '/receipts', icon: Receipt },
    { name: 'Employees', path: '/employees', icon: Users },
    { name: 'Analytics', path: '/analytics', icon: BarChart3 },
  ]

  const settingsNavigation = [
    { name: 'Settings', path: '/settings', icon: Settings },
    { name: 'User Management', path: '/users', icon: UserCog, adminOnly: true },
    { name: 'Audit Logs', path: '/audit-logs', icon: Shield, adminOnly: true },
  ]

  const handleLogout = () => {
    logout()
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-header">
          <h1>Business Manager</h1>
        </div>
        <nav className="sidebar-nav">
          {isSuperAdmin ? (
            <>
              <div style={{ padding: '0 1rem', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--text-secondary)' }}>
                  Platform Management
                </span>
              </div>
              {platformNavigation.map((item) => {
                const Icon = item.icon
                const isActive = location.pathname === item.path
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`nav-item ${isActive ? 'active' : ''}`}
                  >
                    <Icon size={20} />
                    <span>{item.name}</span>
                  </Link>
                )
              })}
            </>
          ) : (
            <>
              {navigation.map((item) => {
                const Icon = item.icon
                const isActive = location.pathname === item.path
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`nav-item ${isActive ? 'active' : ''}`}
                  >
                    <Icon size={20} />
                    <span>{item.name}</span>
                  </Link>
                )
              })}

              <div className="nav-divider"></div>

              {settingsNavigation.map((item) => {
                if (item.adminOnly && !isAdmin) return null
                const Icon = item.icon
                const isActive = location.pathname === item.path
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`nav-item ${isActive ? 'active' : ''}`}
                  >
                    <Icon size={20} />
                    <span>{item.name}</span>
                  </Link>
                )
              })}
            </>
          )}
        </nav>
        <div className="sidebar-footer">
          <button onClick={toggleTheme} className="theme-toggle" title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}>
            {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
            {theme === 'light' ? 'Dark Mode' : 'Light Mode'}
          </button>
          <div className="user-info">
            <span className="user-name">{user?.full_name || user?.username}</span>
            <span className="user-role">{user?.role}</span>
          </div>
          <button onClick={handleLogout} className="logout-btn">
            <LogOut size={18} />
            Logout
          </button>
        </div>
      </aside>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  )
}

export default Layout




