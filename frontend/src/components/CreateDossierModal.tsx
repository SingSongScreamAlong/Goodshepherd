/**
 * CreateDossierModal component - modal for creating new dossiers.
 */
import { useState } from 'react';
import { DossierCreate, DossierType } from '../types';
import { getDossierTypeLabel } from '../utils/dossierFormatting';

interface CreateDossierModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreate: (data: DossierCreate) => Promise<void>;
}

const dossierTypes: DossierType[] = ['location', 'organization', 'group', 'topic', 'person'];

export default function CreateDossierModal({ isOpen, onClose, onCreate }: CreateDossierModalProps) {
  const [formData, setFormData] = useState<DossierCreate>({
    name: '',
    dossier_type: 'location',
    description: '',
    aliases: [],
    location_name: '',
    tags: [],
    notes: '',
  });
  const [aliasInput, setAliasInput] = useState('');
  const [tagInput, setTagInput] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      // Clean up data
      const submitData: DossierCreate = {
        ...formData,
        aliases: formData.aliases?.filter(a => a.trim()) || [],
        tags: formData.tags?.filter(t => t.trim()) || [],
        description: formData.description || undefined,
        location_name: formData.location_name || undefined,
        notes: formData.notes || undefined,
      };

      await onCreate(submitData);

      // Reset form
      setFormData({
        name: '',
        dossier_type: 'location',
        description: '',
        aliases: [],
        location_name: '',
        tags: [],
        notes: '',
      });
      setAliasInput('');
      setTagInput('');
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create dossier');
    } finally {
      setIsSubmitting(false);
    }
  };

  const addAlias = () => {
    if (aliasInput.trim() && !formData.aliases?.includes(aliasInput.trim())) {
      setFormData({
        ...formData,
        aliases: [...(formData.aliases || []), aliasInput.trim()],
      });
      setAliasInput('');
    }
  };

  const removeAlias = (alias: string) => {
    setFormData({
      ...formData,
      aliases: formData.aliases?.filter(a => a !== alias) || [],
    });
  };

  const addTag = () => {
    if (tagInput.trim() && !formData.tags?.includes(tagInput.trim())) {
      setFormData({
        ...formData,
        tags: [...(formData.tags || []), tagInput.trim()],
      });
      setTagInput('');
    }
  };

  const removeTag = (tag: string) => {
    setFormData({
      ...formData,
      tags: formData.tags?.filter(t => t !== tag) || [],
    });
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        {/* Backdrop */}
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={onClose}></div>

        {/* Modal */}
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full">
          <form onSubmit={handleSubmit}>
            <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Create New Dossier</h3>

              {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                  {error}
                </div>
              )}

              <div className="space-y-4">
                {/* Name */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    placeholder="e.g., Berlin, Refugee Council, Migration Policy"
                  />
                </div>

                {/* Type */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Type <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={formData.dossier_type}
                    onChange={(e) => setFormData({ ...formData, dossier_type: e.target.value as DossierType })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  >
                    {dossierTypes.map((type) => (
                      <option key={type} value={type}>
                        {getDossierTypeLabel(type)}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Description */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    placeholder="Brief description of this entity/location..."
                  />
                </div>

                {/* Location Name (for location type) */}
                {formData.dossier_type === 'location' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Location Name</label>
                    <input
                      type="text"
                      value={formData.location_name}
                      onChange={(e) => setFormData({ ...formData, location_name: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      placeholder="e.g., Berlin, Germany"
                    />
                  </div>
                )}

                {/* Aliases */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Aliases</label>
                  <div className="flex gap-2 mb-2">
                    <input
                      type="text"
                      value={aliasInput}
                      onChange={(e) => setAliasInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          addAlias();
                        }
                      }}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      placeholder="Alternative names..."
                    />
                    <button
                      type="button"
                      onClick={addAlias}
                      className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
                    >
                      Add
                    </button>
                  </div>
                  {formData.aliases && formData.aliases.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {formData.aliases.map((alias, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-1 text-sm bg-gray-100 text-gray-700 rounded flex items-center gap-1"
                        >
                          {alias}
                          <button
                            type="button"
                            onClick={() => removeAlias(alias)}
                            className="text-gray-500 hover:text-gray-700"
                          >
                            ×
                          </button>
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Tags */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tags</label>
                  <div className="flex gap-2 mb-2">
                    <input
                      type="text"
                      value={tagInput}
                      onChange={(e) => setTagInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          addTag();
                        }
                      }}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      placeholder="Add tags..."
                    />
                    <button
                      type="button"
                      onClick={addTag}
                      className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
                    >
                      Add
                    </button>
                  </div>
                  {formData.tags && formData.tags.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {formData.tags.map((tag, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-1 text-sm bg-blue-50 text-blue-700 rounded flex items-center gap-1"
                        >
                          #{tag}
                          <button
                            type="button"
                            onClick={() => removeTag(tag)}
                            className="text-blue-500 hover:text-blue-700"
                          >
                            ×
                          </button>
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Notes */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                  <textarea
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    placeholder="Internal notes..."
                  />
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse gap-3">
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full sm:w-auto px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Creating...' : 'Create Dossier'}
              </button>
              <button
                type="button"
                onClick={onClose}
                disabled={isSubmitting}
                className="mt-3 sm:mt-0 w-full sm:w-auto px-4 py-2 bg-white text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
