/**
 * AuditLogsFilter - Filter component for audit logs
 */

import { useState, useEffect } from "react";
import "../styles/AuditLogsFilter.css";

export const AuditLogsFilter = ({
  filters,
  onFilterChange,
  actions,
  entityTypes,
  isLoading,
}) => {
  const [localFilters, setLocalFilters] = useState(filters);

  useEffect(() => {
    setLocalFilters(filters);
  }, [filters]);

  const handleFilterChange = (field, value) => {
    const updated = { ...localFilters, [field]: value };
    setLocalFilters(updated);
    onFilterChange(updated);
  };

  const handleDateChange = (field, value) => {
    const updated = { ...localFilters, [field]: value };
    setLocalFilters(updated);
    onFilterChange(updated);
  };

  const handleClearFilters = () => {
    const cleared = {
      user_id: "",
      action: "",
      entity_type: "",
      status: "",
      date_from: "",
      date_to: "",
      search: "",
    };
    setLocalFilters(cleared);
    onFilterChange(cleared);
  };

  return (
    <div className="audit-filter-container">
      <div className="filter-group">
        <div className="filter-section">
          <label htmlFor="search">Search</label>
          <input
            id="search"
            type="text"
            className="filter-input"
            placeholder="Search action, entity, or username..."
            value={localFilters.search || ""}
            onChange={(e) => handleFilterChange("search", e.target.value)}
          />
        </div>

        <div className="filter-section">
          <label htmlFor="action">Action</label>
          <select
            id="action"
            className="filter-select"
            value={localFilters.action || ""}
            onChange={(e) => handleFilterChange("action", e.target.value)}
          >
            <option value="">All Actions</option>
            {(Array.isArray(actions) ? actions : []).map((a) => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-section">
          <label htmlFor="entity_type">Entity Type</label>
          <select
            id="entity_type"
            className="filter-select"
            value={localFilters.entity_type || ""}
            onChange={(e) => handleFilterChange("entity_type", e.target.value)}
          >
            <option value="">All Entity Types</option>
            {(Array.isArray(entityTypes) ? entityTypes : []).map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-section">
          <label htmlFor="status">Status</label>
          <select
            id="status"
            className="filter-select"
            value={localFilters.status || ""}
            onChange={(e) => handleFilterChange("status", e.target.value)}
          >
            <option value="">All Statuses</option>
            <option value="success">Success</option>
            <option value="failure">Failure</option>
          </select>
        </div>
      </div>

      <div className="filter-group">
        <div className="filter-section">
          <label htmlFor="date_from">From Date</label>
          <input
            id="date_from"
            type="datetime-local"
            className="filter-input"
            value={localFilters.date_from || ""}
            onChange={(e) => handleDateChange("date_from", e.target.value)}
          />
        </div>

        <div className="filter-section">
          <label htmlFor="date_to">To Date</label>
          <input
            id="date_to"
            type="datetime-local"
            className="filter-input"
            value={localFilters.date_to || ""}
            onChange={(e) => handleDateChange("date_to", e.target.value)}
          />
        </div>

        <div className="filter-section">
          <label htmlFor="user_id">User ID</label>
          <input
            id="user_id"
            type="number"
            className="filter-input"
            placeholder="User ID"
            value={localFilters.user_id || ""}
            onChange={(e) => handleFilterChange("user_id", e.target.value)}
          />
        </div>

        <div className="filter-actions">
          <button
            className="btn-clear"
            onClick={handleClearFilters}
            disabled={isLoading}
          >
            Clear Filters
          </button>
        </div>
      </div>
    </div>
  );
};
