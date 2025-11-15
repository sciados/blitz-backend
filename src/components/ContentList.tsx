"use client";

import { useState, useMemo } from "react";
import { GeneratedContent, ContentType, ComplianceStatus } from "src/lib/types";
import { ContentCard } from "./ContentCard";

interface ContentListProps {
  contents: GeneratedContent[];
  loading?: boolean;
  onEdit?: (content: GeneratedContent) => void;
  onDelete?: (contentId: number) => void;
  onView?: (content: GeneratedContent) => void;
}

type SortOption = "newest" | "oldest" | "compliance_high" | "compliance_low";

export function ContentList({ contents, loading = false, onEdit, onDelete, onView }: ContentListProps) {
  const [filterType, setFilterType] = useState<ContentType | "all">("all");
  const [filterCompliance, setFilterCompliance] = useState<ComplianceStatus | "all">("all");
  const [sortBy, setSortBy] = useState<SortOption>("newest");
  const [searchTerm, setSearchTerm] = useState("");
  const [hoveredSequenceIds, setHoveredSequenceIds] = useState<Set<number>>(new Set());

  // Filter and sort content
  const filteredAndSortedContent = useMemo(() => {
    let filtered = [...contents];

    // Apply content type filter
    if (filterType !== "all") {
      filtered = filtered.filter((c) => c.content_type === filterType);
    }

    // Apply compliance filter
    if (filterCompliance !== "all") {
      filtered = filtered.filter((c) => c.compliance_status === filterCompliance);
    }

    // Apply search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(
        (c) =>
          c.content_data.text.toLowerCase().includes(term) ||
          c.content_type.toLowerCase().includes(term) ||
          c.marketing_angle.toLowerCase().includes(term)
      );
    }

    // Apply sorting
    filtered.sort((a, b) => {
      switch (sortBy) {
        case "newest":
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        case "oldest":
          return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
        case "compliance_high":
          return (b.compliance_score ?? 0) - (a.compliance_score ?? 0);
        case "compliance_low":
          return (a.compliance_score ?? 0) - (b.compliance_score ?? 0);
        default:
          return 0;
      }
    });

    // Secondary sort by email_number for email sequences (keeps emails in order)
    filtered.sort((a, b) => {
      const aIsEmail = a.content_type === "email" && a.content_data.email_number;
      const bIsEmail = b.content_type === "email" && b.content_data.email_number;

      // If both are emails with numbers, sort by email number
      if (aIsEmail && bIsEmail) {
        const aTime = new Date(a.created_at).getTime();
        const bTime = new Date(b.created_at).getTime();
        const timeDiff = Math.abs(aTime - bTime);

        // If created within 10 seconds of each other, they're likely from same sequence
        if (timeDiff < 10000) {
          return (a.content_data.email_number || 0) - (b.content_data.email_number || 0);
        }
      }

      return 0;
    });

    return filtered;
  }, [contents, filterType, filterCompliance, sortBy, searchTerm]);

  // Detect emails in same sequence based on creation time proximity
  const getSequenceEmails = (content: GeneratedContent): GeneratedContent[] => {
    if (!content.content_data.email_number) return [content];

    return filteredAndSortedContent.filter((c) => {
      if (!c.content_data.email_number) return false;
      if (c.campaign_id !== content.campaign_id) return false;

      // Check if created within 30 seconds of each other (same sequence)
      const timeDiff = Math.abs(
        new Date(c.created_at).getTime() - new Date(content.created_at).getTime()
      );
      return timeDiff < 30000; // 30 seconds
    });
  };

  const handleCardHover = (content: GeneratedContent, isHovering: boolean) => {
    if (isHovering) {
      const sequenceEmails = getSequenceEmails(content);
      const ids = new Set(sequenceEmails.map(e => e.id));
      setHoveredSequenceIds(ids);
    } else {
      setHoveredSequenceIds(new Set());
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2" style={{ borderColor: "var(--primary-color)" }} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Filters and Search */}
      <div className="card rounded-lg p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Search */}
          <div>
            <label className="block text-xs font-medium mb-1" style={{ color: "var(--text-secondary)" }}>
              Search
            </label>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search content..."
              className="w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              style={{
                borderColor: "var(--border-color)",
                backgroundColor: "var(--card-bg)",
                color: "var(--text-primary)",
              }}
            />
          </div>

          {/* Content Type Filter */}
          <div>
            <label className="block text-xs font-medium mb-1" style={{ color: "var(--text-secondary)" }}>
              Content Type
            </label>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value as ContentType | "all")}
              className="w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              style={{
                borderColor: "var(--border-color)",
                backgroundColor: "var(--card-bg)",
                color: "var(--text-primary)",
              }}
            >
              <option value="all">All Types</option>
              <option value="article">Article</option>
              <option value="email">Email</option>
              <option value="video_script">Video Script</option>
              <option value="social_post">Social Post</option>
              <option value="landing_page">Landing Page</option>
              <option value="ad_copy">Ad Copy</option>
            </select>
          </div>

          {/* Compliance Filter */}
          <div>
            <label className="block text-xs font-medium mb-1" style={{ color: "var(--text-secondary)" }}>
              Compliance Status
            </label>
            <select
              value={filterCompliance}
              onChange={(e) => setFilterCompliance(e.target.value as ComplianceStatus | "all")}
              className="w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              style={{
                borderColor: "var(--border-color)",
                backgroundColor: "var(--card-bg)",
                color: "var(--text-primary)",
              }}
            >
              <option value="all">All Status</option>
              <option value="compliant">Compliant</option>
              <option value="warning">Warning</option>
              <option value="violation">Violation</option>
            </select>
          </div>

          {/* Sort By */}
          <div>
            <label className="block text-xs font-medium mb-1" style={{ color: "var(--text-secondary)" }}>
              Sort By
            </label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortOption)}
              className="w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              style={{
                borderColor: "var(--border-color)",
                backgroundColor: "var(--card-bg)",
                color: "var(--text-primary)",
              }}
            >
              <option value="newest">Newest First</option>
              <option value="oldest">Oldest First</option>
              <option value="compliance_high">Compliance: High to Low</option>
              <option value="compliance_low">Compliance: Low to High</option>
            </select>
          </div>
        </div>

        {/* Results count */}
        <div className="mt-4 pt-4 border-t" style={{ borderColor: "var(--border-color)" }}>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            Showing {filteredAndSortedContent.length} of {contents.length} content pieces
          </p>
        </div>
      </div>

      {/* Content Grid */}
      {filteredAndSortedContent.length === 0 ? (
        <div className="card rounded-lg p-12 text-center">
          <svg
            className="w-20 h-20 mx-auto mb-4 opacity-30"
            style={{ color: "var(--text-secondary)" }}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <h3 className="text-xl font-medium mb-2" style={{ color: "var(--text-primary)" }}>
            {searchTerm || filterType !== "all" || filterCompliance !== "all" ? "No Matching Content" : "No Content Yet"}
          </h3>
          <p className="text-sm max-w-md mx-auto" style={{ color: "var(--text-secondary)" }}>
            {searchTerm || filterType !== "all" || filterCompliance !== "all"
              ? "Try adjusting your filters or search terms to find what you're looking for."
              : "Start by generating your first piece of marketing content using the form above."}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {filteredAndSortedContent.map((content) => (
            <ContentCard
              key={content.id}
              content={content}
              onEdit={onEdit}
              onDelete={onDelete}
              onView={onView}
              onHover={(isHovering) => handleCardHover(content, isHovering)}
              isHighlighted={hoveredSequenceIds.has(content.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
