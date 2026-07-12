"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Panel } from "@/components/ui";

interface RepoPickerProps {
  token: string;
  onSuccess: () => void;
  onCancel: () => void;
}

export function RepoPicker({ token, onSuccess, onCancel }: RepoPickerProps) {
  const [orgs, setOrgs] = useState<any[]>([]);
  const [selectedOrg, setSelectedOrg] = useState<string>("");
  const [repos, setRepos] = useState<any[]>([]);
  const [loadingOrgs, setLoadingOrgs] = useState(true);
  const [loadingRepos, setLoadingRepos] = useState(false);
  const [selectedRepoIds, setSelectedRepoIds] = useState<Set<number>>(new Set());
  const [search, setSearch] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    // Fetch Orgs on mount
    api.githubOrgs(token)
      .then(res => setOrgs(res))
      .catch(err => console.error(err))
      .finally(() => setLoadingOrgs(false));
  }, [token]);

  useEffect(() => {
    // Fetch Repos when org changes
    setLoadingRepos(true);
    api.githubRepos(token, selectedOrg || undefined)
      .then(res => setRepos(res.items))
      .catch(err => console.error(err))
      .finally(() => setLoadingRepos(false));
  }, [token, selectedOrg]);

  const filteredRepos = repos.filter(r => 
    r.full_name.toLowerCase().includes(search.toLowerCase()) || 
    (r.description && r.description.toLowerCase().includes(search.toLowerCase()))
  );

  const toggleRepo = (id: number) => {
    const next = new Set(selectedRepoIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelectedRepoIds(next);
  };

  const toggleAll = () => {
    if (selectedRepoIds.size === filteredRepos.length) {
      setSelectedRepoIds(new Set());
    } else {
      setSelectedRepoIds(new Set(filteredRepos.map(r => r.id)));
    }
  };

  const handleConnect = async () => {
    if (selectedRepoIds.size === 0) return;
    setSubmitting(true);
    
    // Prepare payload
    const selected = repos.filter(r => selectedRepoIds.has(r.id));
    const payload = selected.map(r => ({
      repo: r.full_name,
      branch: r.default_branch || "main",
      path: "policies/" // Default assumption for the hackathon UX
    }));

    try {
      await api.bulkGitHubConnect(token, payload);
      onSuccess();
    } catch (err: any) {
      alert("Failed to connect repositories: " + err.message);
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <Panel title="Select Repositories">
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <div className="w-full sm:w-1/3">
            <label className="block text-xs font-bold text-black uppercase mb-1">Organization</label>
            <select 
              value={selectedOrg} 
              onChange={e => { setSelectedOrg(e.target.value); setSelectedRepoIds(new Set()); }}
              disabled={loadingOrgs}
              className="w-full rounded-lg border border-neutral-300 bg-white px-3 py-2 text-sm text-black font-medium focus:border-blue-500 focus:outline-none shadow-sm"
            >
              <option value="">Personal Account</option>
              {orgs.map(org => (
                <option key={org.id} value={org.login}>{org.login}</option>
              ))}
            </select>
          </div>
          <div className="w-full sm:w-2/3">
            <label className="block text-xs font-bold text-black uppercase mb-1">Search</label>
            <input 
              value={search} 
              onChange={e => setSearch(e.target.value)}
              placeholder="Find a repository..."
              className="w-full rounded-lg border border-neutral-300 bg-white px-3 py-2 text-sm text-black font-medium focus:border-blue-500 focus:outline-none shadow-sm placeholder:text-neutral-400"
            />
          </div>
        </div>

        <div className="rounded-xl border border-neutral-200 bg-white overflow-hidden shadow-sm">
          <div className="flex items-center px-4 py-3 bg-neutral-50 border-b border-neutral-200">
            <input 
              type="checkbox" 
              className="rounded border-neutral-300 text-blue-600 focus:ring-blue-500 mr-3"
              checked={filteredRepos.length > 0 && selectedRepoIds.size === filteredRepos.length}
              onChange={toggleAll}
            />
            <span className="text-xs font-bold text-black uppercase tracking-wider">
              {selectedRepoIds.size} selected
            </span>
          </div>
          
          <div className="max-h-[400px] overflow-y-auto">
            {loadingRepos ? (
              <div className="p-8 text-center text-sm font-medium text-black animate-pulse">
                Fetching repositories from GitHub...
              </div>
            ) : filteredRepos.length === 0 ? (
              <div className="p-8 text-center text-sm font-medium text-black">
                No repositories found matching your search.
              </div>
            ) : (
              <ul className="divide-y divide-neutral-100">
                {filteredRepos.map(repo => (
                  <li 
                    key={repo.id} 
                    className={`flex items-center px-4 py-3 hover:bg-blue-50 cursor-pointer transition-colors ${selectedRepoIds.has(repo.id) ? "bg-blue-50" : ""}`}
                    onClick={() => toggleRepo(repo.id)}
                  >
                    <input 
                      type="checkbox" 
                      className="rounded border-neutral-300 text-blue-600 focus:ring-blue-500 mr-3"
                      checked={selectedRepoIds.has(repo.id)}
                      readOnly
                    />
                    <img 
                      src={repo.owner.avatar_url} 
                      alt={repo.owner.login} 
                      className="w-8 h-8 rounded border border-neutral-200 mr-3"
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-black truncate">{repo.name}</span>
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-bold border border-neutral-200 bg-white text-black uppercase">
                          {repo.private ? "Private" : "Public"}
                        </span>
                      </div>
                      <div className="text-xs text-black font-medium mt-0.5 truncate">
                        {repo.description || "No description provided."}
                      </div>
                    </div>
                    <div className="text-xs text-black text-right min-w-[100px]">
                      <div className="font-semibold">{repo.default_branch}</div>
                      <div className="font-medium text-[10px] uppercase mt-0.5">
                        {new Date(repo.updated_at).toLocaleDateString()}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        <div className="mt-6 flex items-center justify-between">
          <button 
            onClick={onCancel}
            disabled={submitting}
            className="rounded-lg border border-neutral-200 bg-white px-4 py-2 text-sm font-bold text-black transition hover:bg-neutral-50 disabled:opacity-50"
          >
            Cancel
          </button>
          <button 
            onClick={handleConnect}
            disabled={selectedRepoIds.size === 0 || submitting}
            className="flex items-center gap-2 rounded-lg bg-black px-6 py-2 text-sm font-bold text-white shadow-sm transition hover:bg-neutral-800 disabled:opacity-50 disabled:hover:bg-black"
          >
            {submitting ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Connecting & Registering Webhooks...
              </>
            ) : (
              `Connect ${selectedRepoIds.size} Repositor${selectedRepoIds.size === 1 ? 'y' : 'ies'}`
            )}
          </button>
        </div>
      </Panel>
    </div>
  );
}
