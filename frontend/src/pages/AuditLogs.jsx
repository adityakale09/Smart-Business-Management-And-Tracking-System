/**
 * AuditLogs Page Component
 * Main page for viewing and filtering audit logs
 */

import { useState, useEffect } from "react";
import { useAuthStore } from "../store/authStore";
import { auditApi } from "../api/audit";
import { AuditLogsFilter } from "../components/AuditLogsFilter";
import "../pages/AuditLogs.css";

export const AuditLogs = () => {
  const { user } = useAuthStore();
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [actions, setActions] = useState([]);
  const [entityTypes, setEntityTypes] = useState([]);
  const [selectedLog, setSelectedLog] = useState(null);
  const [stats, setStats] = useState(null);

  const [pagination, setPagination] = useState({ skip: 0, limit: 50 });
  const [filters, setFilters] = useState({
    user_id: "",
    action: "",
    entity_type: "",
    status: "",
    date_from: "",
    date_to: "",
    search: "",
  });

  // Check admin access
  useEffect(() => {
    if (user?.role !== "admin") {
      setError("Only administrators can access audit logs");
    }
  }, [user]);

  // Fetch filter options and logs on component mount and when filters change
  useEffect(() => {
    if (user?.role !== "admin") return;

    const fetchData = async () => {
      setIsLoading(true);
      try {
        // Fetch actions and entity types for filters
        const [actionsRes, typesRes, statsRes] = await Promise.all([
          auditApi.getAvailableActions(),
          auditApi.getEntityTypes(),
          auditApi.getStatistics(7),
        ]);

        setActions(actionsRes);
        setEntityTypes(typesRes);
        setStats(statsRes);

        // Fetch audit logs
        await fetchLogs();
      } catch (err) {
        setError(err.message || "Failed to load audit logs");
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [user?.role]);

  // Fetch logs with current filters
  const fetchLogs = async () => {
    try {
      setIsLoading(true);
      const params = {
        skip: pagination.skip,
        limit: pagination.limit,
        ...Object.fromEntries(
          Object.entries(filters).filter(([, v]) => v !== "")
        ),
      };

      const response = await auditApi.getAuditLogs(params);
      setLogs(response.items || []);
      setTotal(response.total || 0);
      setError(null);
    } catch (err) {
      setError(err.message || "Failed to load audit logs");
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
    setPagination({ skip: 0, limit: 50 }); // Reset to first page
  };

  const handleFilterApply = async () => {
    await fetchLogs();
  };

  const handlePageChange = (newSkip) => {
    setPagination({ ...pagination, skip: newSkip });
  };

  const handleLogDetail = async (logId) => {
    try {
      const detail = await auditApi.getAuditLogDetail(logId);
      setSelectedLog(detail);
    } catch (err) {
      setError("Failed to load log details");
      console.error(err);
    }
  };

  const handleDeleteLog = async (logId) => {
    if (!window.confirm("Are you sure you want to delete this audit log?")) {
      return;
    }

    try {
      await auditApi.deleteAuditLog(logId);
      setSelectedLog(null);
      await fetchLogs();
    } catch (err) {
      setError("Failed to delete audit log");
      console.error(err);
    }
  };

  if (user?.role !== "admin") {
    return (
      <div className="audit-logs-container">
        <div className="error-message">
          <h2>Access Denied</h2>
          <p>Only administrators can access audit logs.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="audit-logs-container">
      <div className="page-header">
        <h1>Audit Logs</h1>
        <p>Track all system activities and user actions</p>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {/* Statistics Dashboard */}
      {stats && (
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-value">{stats.total_logs}</div>
            <div className="stat-label">Total Logs (7 days)</div>
          </div>
          <div className="stat-card success">
            <div className="stat-value">{stats.successful_actions}</div>
            <div className="stat-label">Successful Actions</div>
          </div>
          <div className="stat-card danger">
            <div className="stat-value">{stats.failed_actions}</div>
            <div className="stat-label">Failed Actions</div>
          </div>
        </div>
      )}

      {/* Filters */}
      <AuditLogsFilter
        filters={filters}
        onFilterChange={handleFilterChange}
        actions={actions}
        entityTypes={entityTypes}
        isLoading={isLoading}
      />

      {/* Logs Table */}
      <div className="logs-section">
        <div className="logs-header">
          <h2>Audit Logs ({total} total)</h2>
          <button
            className="btn-refresh"
            onClick={handleFilterApply}
            disabled={isLoading}
          >
            {isLoading ? "Loading..." : "Refresh"}
          </button>
        </div>

        {isLoading ? (
          <div className="loading">Loading audit logs...</div>
        ) : logs.length === 0 ? (
          <div className="no-data">No audit logs found</div>
        ) : (
          <>
            <div className="logs-table-wrapper">
              <table className="logs-table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>User</th>
                    <th>Action</th>
                    <th>Entity Type</th>
                    <th>Status</th>
                    <th>IP Address</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log) => (
                    <tr key={log.id} className={`status-${log.status}`}>
                      <td className="td-time">
                        {new Date(log.created_at).toLocaleString()}
                      </td>
                      <td className="td-user">{log.username || "System"}</td>
                      <td className="td-action">{log.action}</td>
                      <td className="td-entity">{log.entity_type}</td>
                      <td className="td-status">
                        <span className={`badge badge-${log.status}`}>
                          {log.status}
                        </span>
                      </td>
                      <td className="td-ip">{log.ip_address || "-"}</td>
                      <td className="td-actions">
                        <button
                          className="btn-view"
                          onClick={() => handleLogDetail(log.id)}
                          title="View details"
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {total > pagination.limit && (
              <div className="pagination">
                <button
                  className="btn-page"
                  onClick={() =>
                    handlePageChange(Math.max(0, pagination.skip - pagination.limit))
                  }
                  disabled={pagination.skip === 0}
                >
                  Previous
                </button>

                <span className="page-info">
                  Page {Math.floor(pagination.skip / pagination.limit) + 1} of{" "}
                  {Math.ceil(total / pagination.limit)}
                </span>

                <button
                  className="btn-page"
                  onClick={() =>
                    handlePageChange(pagination.skip + pagination.limit)
                  }
                  disabled={pagination.skip + pagination.limit >= total}
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {/* Detail Modal */}
      {selectedLog && (
        <div className="modal-overlay" onClick={() => setSelectedLog(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Audit Log Details</h2>
              <button
                className="btn-close"
                onClick={() => setSelectedLog(null)}
              >
                ✕
              </button>
            </div>

            <div className="modal-body">
              <div className="detail-grid">
                <div className="detail-item">
                  <label>ID:</label>
                  <span>{selectedLog.id}</span>
                </div>
                <div className="detail-item">
                  <label>User:</label>
                  <span>{selectedLog.username || "System"}</span>
                </div>
                <div className="detail-item">
                  <label>Action:</label>
                  <span>{selectedLog.action}</span>
                </div>
                <div className="detail-item">
                  <label>Entity Type:</label>
                  <span>{selectedLog.entity_type}</span>
                </div>
                <div className="detail-item">
                  <label>Status:</label>
                  <span className={`badge badge-${selectedLog.status}`}>
                    {selectedLog.status}
                  </span>
                </div>
                <div className="detail-item">
                  <label>Timestamp:</label>
                  <span>
                    {new Date(selectedLog.created_at).toLocaleString()}
                  </span>
                </div>
                <div className="detail-item">
                  <label>IP Address:</label>
                  <span>{selectedLog.ip_address || "-"}</span>
                </div>
                <div className="detail-item">
                  <label>Entity ID:</label>
                  <span>{selectedLog.entity_id || "-"}</span>
                </div>

                {selectedLog.error_message && (
                  <>
                    <div className="detail-item full-width">
                      <label>Error Message:</label>
                      <span className="error-text">{selectedLog.error_message}</span>
                    </div>
                  </>
                )}

                {selectedLog.details && (
                  <div className="detail-item full-width">
                    <label>Details:</label>
                    <pre className="json-display">
                      {JSON.stringify(selectedLog.details, null, 2)}
                    </pre>
                  </div>
                )}

                {selectedLog.user_agent && (
                  <div className="detail-item full-width">
                    <label>User Agent:</label>
                    <span className="user-agent">{selectedLog.user_agent}</span>
                  </div>
                )}
              </div>
            </div>

            <div className="modal-footer">
              <button
                className="btn-delete"
                onClick={() => handleDeleteLog(selectedLog.id)}
              >
                Delete Log
              </button>
              <button
                className="btn-close-modal"
                onClick={() => setSelectedLog(null)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
