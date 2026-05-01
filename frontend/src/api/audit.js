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
    if (params.date_from) queryParams.append("date_from", params.date_from);
    if (params.date_to) queryParams.append("date_to", params.date_to);
    if (params.search) queryParams.append("search", params.search);
    
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
   * Delete an audit log entry
   */
  deleteAuditLog: (logId) => client.delete(`/api/audit-logs/${logId}`),
};
