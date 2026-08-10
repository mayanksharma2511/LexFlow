import { useEffect, useState } from "react";
import {
  BriefcaseBusiness,
  ChevronRight,
  Plus,
  Search,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import { getCases, type Case } from "../api/cases";
import { NewCaseModal } from "../components/NewCaseModal";

function Cases() {
  const navigate = useNavigate();

  const [cases, setCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    let isMounted = true;
    getCases()
      .then((data) => {
        if (isMounted) setCases(data);
      })
      .catch(() => {
        if (isMounted) setError("Unable to load your cases.");
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const filteredCases = cases.filter((c) =>
    c.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (c.case_number && c.case_number.toLowerCase().includes(searchQuery.toLowerCase())) ||
    (c.client_name && c.client_name.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="cases-page">
      <NewCaseModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={() => getCases().then(setCases)}
      />

      <div className="page-header">
        <div>
          <div className="eyebrow">Workspace</div>
          <h1>Cases</h1>
          <p>Manage your matters, clients, and legal documents.</p>
        </div>

        <button className="primary-button" onClick={() => setIsModalOpen(true)}>
          <Plus size={17} />
          New case
        </button>
      </div>

      <div className="cases-toolbar">
        <div className="cases-search">
          <Search size={16} />
          <input
            type="text"
            placeholder="Search cases by title, number, or client..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="case-count">
          {filteredCases.length} {filteredCases.length === 1 ? "case" : "cases"}
        </div>
      </div>

      {loading && <div className="cases-state">Loading cases...</div>}

      {!loading && error && <div className="cases-state cases-error">{error}</div>}

      {!loading && !error && filteredCases.length === 0 && (
        <div className="cases-empty">
          <div className="cases-empty-icon">
            <BriefcaseBusiness size={23} />
          </div>
          <h2>No cases found</h2>
          <p>Create your first case or adjust your search to find legal matters.</p>
        </div>
      )}

      {!loading && !error && filteredCases.length > 0 && (
        <div className="cases-grid">
          {filteredCases.map((caseItem) => (
            <button
              key={caseItem.id}
              className="case-card"
              onClick={() => navigate(`/cases/${caseItem.id}`)}
            >
              <div className="case-card-top">
                <div className="case-icon">
                  <BriefcaseBusiness size={18} />
                </div>
                <ChevronRight size={17} />
              </div>

              <div className="case-card-title">{caseItem.title}</div>

              {caseItem.case_number && (
                <div className="case-number">{caseItem.case_number}</div>
              )}

              <div className="case-card-details">
                {caseItem.client_name && (
                  <span>Client: {caseItem.client_name}</span>
                )}
                {caseItem.opposing_party && (
                  <span>Opposing: {caseItem.opposing_party}</span>
                )}
              </div>

              <div className="case-card-footer">
                <span>{caseItem.court || "Court not specified"}</span>

                {caseItem.priority && (
                  <span className="case-priority">{caseItem.priority}</span>
                )}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default Cases;