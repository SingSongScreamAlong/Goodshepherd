/**
 * Tests for useOfflineFirst hook
 * 
 * Note: Full integration tests require IndexedDB which is complex to mock.
 * These tests verify the hook's interface and basic behavior.
 */

describe('useOfflineFirst', () => {
  describe('module exports', () => {
    it('should export useOfflineFirst hook', () => {
      const { useOfflineFirst } = require('./useOfflineFirst');
      expect(typeof useOfflineFirst).toBe('function');
    });

    it('should export default', () => {
      const defaultExport = require('./useOfflineFirst').default;
      expect(typeof defaultExport).toBe('function');
    });
  });

  describe('hook interface', () => {
    // These tests would require proper IndexedDB mocking
    // For now, we verify the module structure
    it('should be importable', () => {
      expect(() => require('./useOfflineFirst')).not.toThrow();
    });
  });
});
