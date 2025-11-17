"use client";

import { AuthGate } from "src/components/AuthGate";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "src/lib/appClient";

interface ComplianceStats {
  total_checks: number;
  compliant_count: number;
  warning_count: number;
  violation_count: number;
  compliance_rate: number;
}

interface ComplianceIssue {
  issue_type: string;
  count: number;
  severity: string;
}

interface RecentCheck {
  content_id: number;
  user_email: string;
  campaign_name: string;
  content_type: string;
  status: string;
  checked_at: string;
  issues_count: number;
}

interface ComplianceSummary {
  stats: ComplianceStats;
  common_issues: ComplianceIssue[];
  recent_checks: RecentCheck[];
  checks_over_time: Array<{
    date: string;
    total: number;
    compliant: number;
    warning: number;
    violation: number;
  }>;
}

export default function AdminCompliancePage() {
  const [days, setDays] = useState(30);

  const { data: complianceData, isLoading } = useQuery<ComplianceSummary>({
    queryKey: ["admin-compliance", days],
    queryFn: async () => (await api.get(`/api/admin/compliance/summary?days=${days}`)).data,
  });

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case "compliant":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
      case "warning":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200";
      case "violation":
        return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300";
    }
  };

  const getSeverityBadgeClass = (severity: string) => {
    switch (severity) {
      case "high":
        return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200";
      case "medium":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200";
      case "low":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300";
    }
  };

  return (
    <AuthGate requiredRole="admin">
      <div className="p-6">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2" style={{ color: "var(--text-primary)" }}>
              Compliance Monitoring
            </h1>
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              Track FTC compliance and affiliate network guidelines
            </p>
          </div>

          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="px-4 py-2 border rounded-lg"
            style={{ borderColor: "var(--card-border)" }}
          >
            <option value={7}>Last 7 Days</option>
            <option value={30}>Last 30 Days</option>
            <option value={90}>Last 90 Days</option>
            <option value={365}>Last Year</option>
          </select>
        </div>

        {isLoading ? (
          <div className="text-center py-12" style={{ color: "var(--text-secondary)" }}>
            Loading compliance data...
          </div>
        ) : (
          <>
            {/* Compliance Stats Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <div className="card rounded-xl p-6">
                <p className="text-sm font-medium mb-1" style={{ color: "var(--text-secondary)" }}>
                  Total Checks
                </p>
                <p className="text-3xl font-bold" style={{ color: "var(--text-primary)" }}>
                  {complianceData?.stats.total_checks.toLocaleString() || 0}
                </p>
              </div>

              <div className="card rounded-xl p-6">
                <p className="text-sm font-medium mb-1" style={{ color: "var(--text-secondary)" }}>
                  Compliance Rate
                </p>
                <p className="text-3xl font-bold text-green-600 dark:text-green-400">
                  {complianceData?.stats.compliance_rate || 0}%
                </p>
              </div>

              <div className="card rounded-xl p-6">
                <p className="text-sm font-medium mb-1" style={{ color: "var(--text-secondary)" }}>
                  Warnings
                </p>
                <p className="text-3xl font-bold text-yellow-600 dark:text-yellow-400">
                  {complianceData?.stats.warning_count || 0}
                </p>
              </div>

              <div className="card rounded-xl p-6">
                <p className="text-sm font-medium mb-1" style={{ color: "var(--text-secondary)" }}>
                  Violations
                </p>
                <p className="text-3xl font-bold text-red-600 dark:text-red-400">
                  {complianceData?.stats.violation_count || 0}
                </p>
              </div>
            </div>

            {/* Common Issues */}
            <div className="card rounded-xl p-6 mb-8">
              <h2 className="text-xl font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
                Common Compliance Issues
              </h2>
              <div className="space-y-4">
                {complianceData?.common_issues.map((issue, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <p className="font-medium" style={{ color: "var(--text-primary)" }}>
                          {issue.issue_type}
                        </p>
                        <span className={`px-2 py-0.5 text-xs font-semibold rounded-full ${getSeverityBadgeClass(issue.severity)}`}>
                          {issue.severity}
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div
                          className="bg-red-600 h-2 rounded-full"
                          style={{
                            width: `${(issue.count / (complianceData?.stats.total_checks || 1)) * 100}%`,
                          }}
                        />
                      </div>
                    </div>
                    <div className="ml-4 text-right">
                      <p className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
                        {issue.count}
                      </p>
                      <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                        occurrences
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Recent Compliance Checks */}
            <div className="card rounded-xl p-6">
              <h2 className="text-xl font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
                Recent Compliance Checks
              </h2>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr style={{ borderBottom: "1px solid var(--card-border)" }}>
                      <th className="text-left p-3 text-sm font-semibold" style={{ color: "var(--text-secondary)" }}>
                        User
                      </th>
                      <th className="text-left p-3 text-sm font-semibold" style={{ color: "var(--text-secondary)" }}>
                        Campaign
                      </th>
                      <th className="text-left p-3 text-sm font-semibold" style={{ color: "var(--text-secondary)" }}>
                        Content Type
                      </th>
                      <th className="text-left p-3 text-sm font-semibold" style={{ color: "var(--text-secondary)" }}>
                        Status
                      </th>
                      <th className="text-left p-3 text-sm font-semibold" style={{ color: "var(--text-secondary)" }}>
                        Checked At
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {complianceData?.recent_checks.map((check) => (
                      <tr
                        key={check.content_id}
                        style={{ borderBottom: "1px solid var(--card-border)" }}
                      >
                        <td className="p-3">
                          <p className="text-sm" style={{ color: "var(--text-primary)" }}>
                            {check.user_email}
                          </p>
                        </td>
                        <td className="p-3">
                          <p className="text-sm" style={{ color: "var(--text-primary)" }}>
                            {check.campaign_name}
                          </p>
                        </td>
                        <td className="p-3">
                          <span className="px-2 py-1 text-xs rounded bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                            {check.content_type}
                          </span>
                        </td>
                        <td className="p-3">
                          <span className={`px-2 py-1 text-xs font-semibold rounded ${getStatusBadgeClass(check.status)}`}>
                            {check.status}
                          </span>
                        </td>
                        <td className="p-3">
                          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                            {new Date(check.checked_at).toLocaleDateString()}
                          </p>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>
    </AuthGate>
  );
}
