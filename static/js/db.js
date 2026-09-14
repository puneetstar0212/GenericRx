/**
 * GenericRx - IndexedDB Offline Layer & Client-side Fuzzy Search Engine
 */

// Initialize Dexie IndexedDB
const db = new Dexie('GenericRxDB');

db.version(2).stores({
  medicines: 'id, name, saltName, category, isGeneric, schedule, pricePerUnit, strength, dosageForm',
  pharmacies: 'id, name, type, city, isOpen24h'
});

const OfflineStorage = {
  /**
   * Syncs dataset from Python API into local IndexedDB
   */
  async syncDataset(medicines) {
    try {
      if (!medicines || medicines.length === 0) return;
      await db.medicines.clear();
      await db.medicines.bulkPut(medicines);
      console.log(`[IndexedDB] Synced ${medicines.length} medicines into client-side database.`);
      localStorage.setItem('genericrx_last_sync', new Date().toISOString());
      localStorage.setItem('genericrx_count', medicines.length);
    } catch (err) {
      console.error('[IndexedDB] Sync error:', err);
    }
  },

  /**
   * Syncs pharmacy locations into local IndexedDB
   */
  async syncPharmacies(pharmacies) {
    try {
      if (!pharmacies || pharmacies.length === 0) return;
      await db.pharmacies.clear();
      await db.pharmacies.bulkPut(pharmacies);
      console.log(`[IndexedDB] Synced ${pharmacies.length} pharmacy locations.`);
    } catch (err) {
      console.error('[IndexedDB] Sync pharmacies error:', err);
    }
  },

  /**
   * Get cached pharmacies
   */
  async getPharmaciesOffline() {
    try {
      return await db.pharmacies.toArray();
    } catch (e) {
      return [];
    }
  },

  /**
   * Returns count of cached medicines
   */
  async getCachedCount() {
    try {
      return await db.medicines.count();
    } catch (e) {
      return 0;
    }
  },

  /**
   * Offline Client-Side Search Engine using Fuse.js fuzzy matching
   */
  async searchOffline(query) {
    const allMeds = await db.medicines.toArray();
    if (!query || !query.trim()) {
      return allMeds.slice(0, 50);
    }

    const fuse = new Fuse(allMeds, {
      keys: [
        { name: 'name', weight: 0.5 },
        { name: 'saltName', weight: 0.3 },
        { name: 'therapeuticCategory', weight: 0.1 },
        { name: 'manufacturer', weight: 0.1 }
      ],
      threshold: 0.4,
      ignoreLocation: true
    });

    const results = fuse.search(query.trim());
    return results.map(r => r.item).slice(0, 50);
  },

  /**
   * Offline Alternative Lookup & Savings calculation
   */
  async getAlternativesOffline(medicineId) {
    const target = await db.medicines.get(Number(medicineId));
    if (!target) return null;

    const baseSaltKey = target.saltName.split('+')[0].trim().toLowerCase();
    const allMeds = await db.medicines.toArray();

    const matchedAlts = allMeds.filter(m => {
      if (m.id === target.id) return false;
      return m.saltName.toLowerCase().includes(baseSaltKey);
    });

    const refPrice = target.pricePerUnit;
    const processed = matchedAlts.map(alt => {
      const savingsPct = refPrice > 0 ? ((refPrice - alt.pricePerUnit) / refPrice) * 100 : 0;

      let badgeColor = 'gray';
      let badgeText = 'Same Price';
      if (savingsPct >= 50) { badgeColor = 'green'; badgeText = `High Savings (${savingsPct.toFixed(1)}%)`; }
      else if (savingsPct >= 20) { badgeColor = 'amber'; badgeText = `Moderate Savings (${savingsPct.toFixed(1)}%)`; }
      else if (savingsPct > 0) { badgeColor = 'blue'; badgeText = `Low Savings (${savingsPct.toFixed(1)}%)`; }

      const strengthMismatch = alt.strength.trim().toLowerCase() !== target.strength.trim().toLowerCase();
      const formMismatch = alt.dosageForm.trim().toLowerCase() !== target.dosageForm.trim().toLowerCase();
      const hasMismatch = strengthMismatch || formMismatch;

      const mismatchReasons = [];
      if (strengthMismatch) mismatchReasons.push(`Strength diff (${alt.strength} vs ${target.strength})`);
      if (formMismatch) mismatchReasons.push(`Form diff (${alt.dosageForm} vs ${target.dosageForm})`);

      return {
        ...alt,
        savingsPercentage: Number(savingsPct.toFixed(1)),
        savingsBadgeColor: badgeColor,
        savingsBadgeText: badgeText,
        hasMismatch: hasMismatch,
        mismatchWarning: hasMismatch ? mismatchReasons.join('; ') : null
      };
    });

    // Sort: Generics first, then highest savings
    processed.sort((a, b) => {
      if (a.isGeneric !== b.isGeneric) return b.isGeneric ? 1 : -1;
      return b.savingsPercentage - a.savingsPercentage;
    });

    return {
      targetMedicine: target,
      saltName: target.saltName,
      alternatives: processed,
      count: processed.length
    };
  }
};
