/**
 * Audit Logs API client
 */

import client from "./client";

export const auditApi = {
  /**
   * Get audit logs with filtering and pagination
   */
  getAuditLogs: (params = {}) => {
    const queryParams = new URLSearchParams();
    
    if (params.skip !== undefined) queryParams.append("skip", params.skip);
    if (params.limit !== undefined) queryParams.append("limit", params.limit);
    if (params.user_id) queryParams.append("user_id", params.user_id);
    if (params.action) queryParams.append("action", params.action);
    if (params.entity_type) queryParams.append("entity_type", params.entity_type);
    if (params.status) queryParams.append("status", params.status);
    if (params.severity) queryParams.append("severity", params.severity);
    if (params.date_from) queryParams.append("date_from", params.date_from);
    if (params.date_to) queryParams.append("date_to", params.date_to);
    if (params.search) queryParams.append("search", params.search);
    if (params.correlation_id) queryParams.append("correlation_id", params.correlation_id);
    
    return client.get(`/api/audit-logs?${queryParams}`);
  },

  /**
   * Get available actions for filter dropdown
   */
  getAvailableActions: () => client.get("/api/audit-logs/actions"),

  /**
   * Get available entity types for filter dropdown
   */
  getEntityTypes: () => client.get("/api/audit-logs/entity-types"),

  /**
   * Get audit log statistics
   */
  getStatistics: (days = 7) =>
    client.get(`/api/audit-logs/statistics?days=${days}`),

  /**
   * Get detailed audit log entry
   */
  getAuditLogDetail: (logId) => client.get(`/api/audit-logs/${logId}`),

  /**
   * Export audit logs in CSV or JSON format (compliance reporting)
   */
  exportAuditLogs: (format = "csv", filters = {}) => {
    const queryParams = new URLSearchParams();
    if (filters.date_from) queryParams.append("date_from", filters.date_from);
    if (filters.date_to) queryParams.append("date_to", filters.date_to);
    if (filters.action) queryParams.append("action", filters.action);
    if (filters.entity_type) queryParams.append("entity_type", filters.entity_type);
    if (filters.status) queryParams.append("status", filters.status);
    if (filters.user_id) queryParams.append("user_id", filters.user_id);
    if (filters.severity) queryParams.append("severity", filters.severity);
    
    return client.get(`/api/audit-logs/export/${format}?${queryParams}`, {
      responseType: "blob",
    });
  },

  /**
   * Verify audit log hash chain integrity (tamper detection)
   */
  verifyIntegrity: () => client.get("/api/audit-logs/integrity/verify"),

  /**
   * Clean up audit logs older than retention period
   */
  cleanupRetention: (retentionDays = 365, dryRun = true) =>
    client.delete(`/api/audit-logs/retention/cleanup?retention_days=${retentionDays}&dry_run=${dryRun}`),
};
