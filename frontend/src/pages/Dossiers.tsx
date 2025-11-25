/**
 * Dossiers page - manage entity and location profiles.
 */
import { useState } from 'react';
import { useDossiers } from '../hooks/useDossiers';
import DossierCard from '../components/DossierCard';
import CreateDossierModal from '../components/CreateDossierModal';
import EmptyState, { EmptyIcons } from '../components/EmptyState';
import { Dossier, DossierType } from '../types';
import { getDossierTypeLabel } from '../utils/dossierFormatting';

const dossierTypes: (DossierType | '')[] = ['', 'location', 'organization', 'group', 'topic', 'person'];

export default function Dossiers() {
  const [selectedType, setSelectedType] = useState<DossierType | ''>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  const {
    dossiers,
    isLoading,
    error,
    createDossier,
    deleteDossier,
    refreshDossierStats,
  } = useDossiers(selectedType || undefined, searchQuery || undefined);

  const handleCreate = async (data: any) => {
    await createDossier(data);
  };

  const handleRefresh = async (dossier: Dossier) => {
    try {
      await refreshDossierStats(dossier.id);
    } catch (err) {
      console.error('Failed to refresh dossier stats:', err);
    }
  };

  const handleDelete = async (dossier: Dossier) => {
    try {
      await deleteDossier(dossier.id);
    } catch (err) {
      console.error('Failed to delete dossier:', err);
    }
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Dossiers</h1>
        <p className="text-gray-600">
          Entity and location profiles for focused intelligence tracking
        </p>
      </div>

      {/* Info banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg
              className="h-5 w-5 text-blue-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">About Dossiers</h3>
            <div className="mt-2 text-sm text-blue-700">
              <p>
                Dossiers automatically aggregate events related to specific entities, locations, or topics.
                Create dossiers to monitor organizations, track locations, or follow specific themes.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search dossiers..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          {/* Type filter */}
          <div className="w-full md:w-48">
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value as DossierType | '')}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="">All Types</option>
              {dossierTypes.slice(1).map((type) => (
                <option key={type} value={type}>
                  {getDossierTypeLabel(type as DossierType)}
                </option>
              ))}
            </select>
          </div>

          {/* Create button */}
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="px-6 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 whitespace-nowrap"
          >
            + Create Dossier
          </button>
        </div>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex items-center">
            <svg
              className="w-5 h-5 text-red-600 mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !error && dossiers.length === 0 && (
        <EmptyState
          icon={EmptyIcons.Dossiers}
          title="No dossiers found"
          description={
            searchQuery || selectedType
              ? 'Try adjusting your filters to see more dossiers, or create a new one to get started.'
              : 'Dossiers automatically aggregate events related to specific entities, locations, or topics. Create your first dossier to start tracking intelligence on a specific subject.'
          }
          action={
            !searchQuery && !selectedType
              ? {
                  label: 'Create Dossier',
                  onClick: () => setIsCreateModalOpen(true),
                }
              : undefined
          }
        />
      )}

      {/* Dossiers grid */}
      {!isLoading && !error && dossiers.length > 0 && (
        <>
          <div className="mb-4 text-sm text-gray-600">
            Showing {dossiers.length} {dossiers.length === 1 ? 'dossier' : 'dossiers'}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {dossiers.map((dossier) => (
              <DossierCard
                key={dossier.id}
                dossier={dossier}
                onRefresh={handleRefresh}
                onDelete={handleDelete}
              />
            ))}
          </div>
        </>
      )}

      {/* Create modal */}
      <CreateDossierModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onCreate={handleCreate}
      />
    </div>
  );
}
