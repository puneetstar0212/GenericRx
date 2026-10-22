/**
 * GenericRx - Main PWA Application Controller
 * Handles Online/Offline sync, Intelligent Search, Savings Audit, Safety Warnings, Leaflet.js Map, and JS Micro-Animations
 */

// Application State
const AppState = {
  isOnline: navigator.onLine,
  deferredInstallPrompt: null,
  currentQuery: '',
  activeFilter: 'all',
  activeView: 'search', // 'search' or 'map'
  selectedMedicine: null,
  basket: [], // List of { medicine, selectedAlternative, units }
  searchResults: [],
  pharmacies: [],
  leafletMap: null,
  mapMarkers: []
};

// DOM Elements
const elements = {
  connectionStatus: document.getElementById('connectionStatus'),
  installPwaBtn: document.getElementById('installPwaBtn'),
  searchInput: document.getElementById('searchInput'),
  searchCount: document.getElementById('searchCount'),
  searchResultsList: document.getElementById('searchResultsList'),
  alternativesContainer: document.getElementById('alternativesContainer'),
  targetMedicineDetail: document.getElementById('targetMedicineDetail'),
  basketList: document.getElementById('basketList'),
  totalSavedMonthly: document.getElementById('totalSavedMonthly'),
  totalSavedYearly: document.getElementById('totalSavedYearly'),
  overallSavingsBadge: document.getElementById('overallSavingsBadge'),
  exportReportBtn: document.getElementById('exportReportBtn'),
  reportModal: document.getElementById('reportModal'),
  closeReportModal: document.getElementById('closeReportModal'),
  reportModalContent: document.getElementById('reportModalContent'),
  dbCountBadge: document.getElementById('dbCountBadge'),
  filterButtons: document.querySelectorAll('.filter-btn'),
  tabSearchBtn: document.getElementById('tabSearchBtn'),
  tabMapBtn: document.getElementById('tabMapBtn'),
  viewSearchDashboard: document.getElementById('viewSearchDashboard'),
  viewMapDashboard: document.getElementById('viewMapDashboard'),
  pharmacyListContainer: document.getElementById('pharmacyListContainer'),
  pharmacyCountBadge: document.getElementById('pharmacyCountBadge'),
  btnGpsFind: document.getElementById('btnGpsFind'),
  citySelect: document.getElementById('citySelect')
};

// Initialize Application
document.addEventListener('DOMContentLoaded', async () => {
  initPwaServiceWorker();
  initNetworkStatusListener();
  initEventListeners();
  animateStatCounters();
  await checkConnectionAndSync();
  await performSearch('Crocin'); // Initial seed search
  await loadPharmacies();
});

/**
 * Animated Stat Rollup Counter
 */
function animateStatCounters() {
  const statElements = [
    { id: 'statMedCount', end: 567, suffix: '+' },
    { id: 'statSavingsPct', end: 85, suffix: '%' },
    { id: 'statReliablePct', end: 100, suffix: '%' },
    { id: 'statPharmCount', end: 8, suffix: '+' }
  ];

  statElements.forEach(item => {
    const el = document.getElementById(item.id);
    if (!el) return;

    let current = 0;
    const duration = 1500;
    const stepTime = 30;
    const steps = duration / stepTime;
    const increment = item.end / steps;

    const timer = setInterval(() => {
      current += increment;
      if (current >= item.end) {
        current = item.end;
        clearInterval(timer);
      }
      el.textContent = `${Math.floor(current)}${item.suffix}`;
    }, stepTime);
  });
}

/**
 * 1. PWA Service Worker & Install Prompt Setup
 */
function initPwaServiceWorker() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/sw.js')
      .then(reg => console.log('[PWA] Service Worker registered with scope:', reg.scope))
      .catch(err => console.error('[PWA] Service Worker registration failed:', err));
  }

  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    AppState.deferredInstallPrompt = e;
    if (elements.installPwaBtn) {
      elements.installPwaBtn.style.display = 'inline-flex';
    }
  });

  if (elements.installPwaBtn) {
    elements.installPwaBtn.addEventListener('click', async () => {
      if (AppState.deferredInstallPrompt) {
        AppState.deferredInstallPrompt.prompt();
        const { outcome } = await AppState.deferredInstallPrompt.userChoice;
        console.log(`[PWA] Install prompt outcome: ${outcome}`);
        AppState.deferredInstallPrompt = null;
        elements.installPwaBtn.style.display = 'none';
      }
    });
  }
}

/**
 * 2. Network Status Listener (Online vs Offline Mode)
 */
function initNetworkStatusListener() {
  const updateStatus = () => {
    AppState.isOnline = navigator.onLine;
    if (AppState.isOnline) {
      elements.connectionStatus.className = 'status-pill online';
      elements.connectionStatus.innerHTML = '<span class="dot online"></span> 🟢 Python Server Connected';
    } else {
      elements.connectionStatus.className = 'status-pill offline';
      elements.connectionStatus.innerHTML = '<span class="dot offline"></span> 🟠 Offline Mode (IndexedDB Active)';
    }
  };

  window.addEventListener('online', async () => {
    updateStatus();
    await checkConnectionAndSync();
  });

  window.addEventListener('offline', () => {
    updateStatus();
  });

  updateStatus();
}

/**
 * 3. Sync Server Dataset with IndexedDB
 */
async function checkConnectionAndSync() {
  if (AppState.isOnline) {
    try {
      const response = await fetch('/api/medicines');
      if (response.ok) {
        const medicines = await response.json();
        await OfflineStorage.syncDataset(medicines);
        const cachedCount = medicines.length;
        elements.dbCountBadge.textContent = `${cachedCount} Meds Cached`;
      }
    } catch (e) {
      console.warn('[Sync] Server unreachable. Operating in offline mode.');
      AppState.isOnline = false;
      const count = await OfflineStorage.getCachedCount();
      elements.dbCountBadge.textContent = `${count} Meds (Offline)`;
    }
  } else {
    const count = await OfflineStorage.getCachedCount();
    elements.dbCountBadge.textContent = `${count} Meds (Offline)`;
  }
}

/**
 * 4. Intelligent Search Engine Execution
 */
async function performSearch(query) {
  AppState.currentQuery = query;
  let results = [];

  if (AppState.isOnline) {
    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
      if (res.ok) {
        const data = await res.json();
        results = data.results;
      } else {
        results = await OfflineStorage.searchOffline(query);
      }
    } catch (e) {
      results = await OfflineStorage.searchOffline(query);
    }
  } else {
    results = await OfflineStorage.searchOffline(query);
  }

  // Apply Filter Pills if selected
  if (AppState.activeFilter === 'generic') {
    results = results.filter(m => m.isGeneric);
  } else if (AppState.activeFilter === 'otc') {
    results = results.filter(m => m.schedule === 'OTC');
  } else if (AppState.activeFilter === 'prescription') {
    results = results.filter(m => m.schedule.includes('Schedule'));
  }

  AppState.searchResults = results;
  renderSearchResults(results);
}

/**
 * Format a price for display. Returns 'Price unavailable' when price is null
 * or undefined, so the UI never shows NaN, ₹0, or crashes.
 */
function formatPrice(price) {
  if (price === null || price === undefined) {
    return '<span class="price-unavailable">Price unavailable</span>';
  }
  return `₹${price.toFixed(2)}`;
}

function renderSearchResults(results) {
  elements.searchCount.textContent = `${results.length} results found`;
  elements.searchResultsList.innerHTML = '';

  if (results.length === 0) {
    elements.searchResultsList.innerHTML = `
      <div style="text-align: center; padding: 2rem; color: var(--text-muted);">
        <i data-lucide="search-x" style="width: 48px; height: 48px; margin-bottom: 0.5rem; opacity: 0.5;"></i>
        <p>No medicines or chemical salts found matching your query.</p>
        <p style="font-size: 0.85rem; margin-top: 0.25rem;">Try searching for "Paracetamol", "Augmentin", or "Glycomet".</p>
      </div>
    `;
    lucide.createIcons();
    return;
  }

  results.forEach((med, index) => {
    const isGenericTag = med.isGeneric 
      ? `<span class="badge-tag badge-generic">Jan Aushadhi / Generic</span>`
      : `<span class="badge-tag badge-brand">Brand Medicine</span>`;

    let scheduleClass = 'schedule-otc';
    if (med.schedule === 'Schedule H' || med.schedule === 'Schedule H1') scheduleClass = 'schedule-h';
    if (med.schedule === 'Schedule X') scheduleClass = 'schedule-x';

    const card = document.createElement('div');
    card.className = 'med-card';
    card.style.animationDelay = `${Math.min(index * 0.04, 0.4)}s`;

    card.innerHTML = `
      <div class="med-header">
        <div>
          <div class="med-title">${med.name}</div>
          <div class="med-manufacturer">${med.manufacturer} • ${med.therapeuticCategory}</div>
        </div>
        <div style="text-align: right;">
          <div class="price-tag">${formatPrice(med.pricePerUnit)}</div>
          <div class="price-unit">per ${med.unitCount} units (${med.dosageForm})</div>
        </div>
      </div>

      <div style="display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap;">
        <div class="salt-badge">
          <i data-lucide="flask-conical" style="width: 14px; height: 14px;"></i>
          ${med.saltName}
        </div>
        ${isGenericTag}
        <span class="schedule-tag ${scheduleClass}">
          <i data-lucide="shield-alert" style="width: 12px; height: 12px;"></i>
          ${med.schedule}
        </span>
      </div>

      <div style="display: flex; gap: 0.5rem; margin-top: 0.5rem;">
        <button class="btn-primary" style="flex: 1;" onclick="loadAlternatives(${med.id})">
          <i data-lucide="arrow-right-left" style="width: 16px; height: 16px;"></i>
          Find Generic Alternatives & Savings
        </button>
        <button class="btn-outline" onclick="addToBasket(${med.id})">
          <i data-lucide="plus-circle" style="width: 16px; height: 16px;"></i>
          Audit Basket
        </button>
      </div>
    `;
    elements.searchResultsList.appendChild(card);
  });

  lucide.createIcons();
}

/**
 * 5. Load Generic Alternatives & Cost Audit Calculation (Module 2)
 */
async function loadAlternatives(medicineId) {
  let altData = null;

  if (AppState.isOnline) {
    try {
      const res = await fetch(`/api/medicine/${medicineId}/alternatives`);
      if (res.ok) {
        altData = await res.json();
      } else {
        altData = await OfflineStorage.getAlternativesOffline(medicineId);
      }
    } catch (e) {
      altData = await OfflineStorage.getAlternativesOffline(medicineId);
    }
  } else {
    altData = await OfflineStorage.getAlternativesOffline(medicineId);
  }

  if (!altData) return;

  AppState.selectedMedicine = altData.targetMedicine;
  renderAlternativesView(altData);
}

function renderAlternativesView(altData) {
  const target = altData.targetMedicine;

  elements.targetMedicineDetail.innerHTML = `
    <div style="border-bottom: 1px solid var(--border-color); padding-bottom: 1rem; margin-bottom: 1rem; animation: cardSlideUp 0.3s ease-out;">
      <div style="font-size: 0.85rem; color: var(--accent-teal); font-weight: 700; text-transform: uppercase;">Prescribed Brand Drug</div>
      <div style="font-size: 1.4rem; font-weight: 800; margin: 0.2rem 0;">${target.name}</div>
      <div style="display: flex; gap: 0.5rem; align-items: center; margin-bottom: 0.5rem;">
        <span class="salt-badge"><i data-lucide="flask-conical" style="width: 14px; height: 14px;"></i> ${target.saltName}</span>
        <span class="schedule-tag ${target.schedule.includes('H') || target.schedule.includes('X') ? 'schedule-h' : 'schedule-otc'}">${target.schedule}</span>
      </div>
      <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.75rem;">
        <div>Price: <strong style="font-size: 1.2rem; color: #ffffff;">${formatPrice(target.pricePerUnit)}</strong> (${target.unitCount} ${target.dosageForm})</div>
        <button class="btn-outline" onclick="addToBasket(${target.id})"><i data-lucide="shopping-bag" style="width: 14px; height: 14px;"></i> Add to Prescription Audit</button>
      </div>
    </div>
  `;

  elements.alternativesContainer.innerHTML = '';

  if (!altData.alternatives || altData.alternatives.length === 0) {
    elements.alternativesContainer.innerHTML = `
      <div style="padding: 1.5rem; text-align: center; color: var(--text-muted);">
        <p>No generic or brand alternatives found for this active salt formulation in local database.</p>
      </div>
    `;
    return;
  }

  altData.alternatives.forEach((alt, index) => {
    let badgeClass = 'savings-gray';
    if (alt.savingsBadgeColor === 'green') badgeClass = 'savings-green';
    if (alt.savingsBadgeColor === 'amber') badgeClass = 'savings-amber';
    if (alt.savingsBadgeColor === 'blue') badgeClass = 'savings-blue';

    const isGenericTag = alt.isGeneric 
      ? `<span class="badge-tag badge-generic">Jan Aushadhi Equivalent</span>`
      : `<span class="badge-tag badge-brand">Brand Alternative</span>`;

    const mismatchHTML = alt.hasMismatch ? `
      <div class="mismatch-alert">
        <i data-lucide="alert-triangle" style="width: 16px; height: 16px;"></i>
        <div>
          <div>DOSAGE / FORM MISMATCH WARNING</div>
          <div style="font-weight: 400; opacity: 0.9;">${alt.mismatchWarning}</div>
        </div>
      </div>
    ` : '';

    const card = document.createElement('div');
    card.className = 'med-card';
    card.style.animationDelay = `${Math.min(index * 0.05, 0.4)}s`;

    card.innerHTML = `
      <div class="med-header">
        <div>
          <div class="med-title">${alt.name}</div>
          <div class="med-manufacturer">${alt.manufacturer}</div>
        </div>
        <div style="text-align: right;">
          <div class="price-tag">${formatPrice(alt.pricePerUnit)}</div>
          <div class="savings-badge ${badgeClass}" style="margin-top: 0.2rem;">
            <i data-lucide="trending-down" style="width: 12px; height: 12px;"></i>
            ${alt.savingsBadgeText}
          </div>
        </div>
      </div>

      <div style="display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap;">
        ${isGenericTag}
        <span style="font-size: 0.8rem; color: var(--text-muted);">${alt.strength} • ${alt.dosageForm}</span>
      </div>

      ${mismatchHTML}

      <div style="margin-top: 0.5rem; display: flex; justify-content: flex-end;">
        <button class="btn-outline" onclick="selectAlternativeForBasket(${target.id}, ${alt.id})">
          <i data-lucide="check-circle" style="width: 14px; height: 14px;"></i> Select as Generic Replacement
        </button>
      </div>
    `;

    elements.alternativesContainer.appendChild(card);
  });

  lucide.createIcons();
}

/**
 * 6. Prescription Audit Basket
 */
async function addToBasket(medicineId) {
  const existing = AppState.searchResults.find(m => m.id === medicineId) || AppState.selectedMedicine;
  if (!existing) return;

  if (AppState.basket.some(item => item.medicine.id === medicineId)) {
    alert(`${existing.name} is already in your prescription basket.`);
    return;
  }

  // Find best generic alternative automatically
  let altRes = null;
  if (AppState.isOnline) {
    try {
      const res = await fetch(`/api/medicine/${medicineId}/alternatives`);
      if (res.ok) altRes = await res.json();
      else altRes = await OfflineStorage.getAlternativesOffline(medicineId);
    } catch (e) {
      altRes = await OfflineStorage.getAlternativesOffline(medicineId);
    }
  } else {
    altRes = await OfflineStorage.getAlternativesOffline(medicineId);
  }

  const bestGeneric = (altRes && altRes.alternatives && altRes.alternatives.length > 0)
    ? altRes.alternatives[0]
    : null;

  AppState.basket.push({
    medicine: existing,
    selectedAlternative: bestGeneric,
    units: 30 // Default 1 month supply
  });

  updateBasketUI();
}

function selectAlternativeForBasket(targetId, altId) {
  const itemIndex = AppState.basket.findIndex(i => i.medicine.id === targetId);
  if (itemIndex >= 0) {
    OfflineStorage.getAlternativesOffline(targetId).then(data => {
      const selectedAlt = data.alternatives.find(a => a.id === altId);
      if (selectedAlt) {
        AppState.basket[itemIndex].selectedAlternative = selectedAlt;
        updateBasketUI();
      }
    });
  } else {
    addToBasket(targetId).then(() => {
      selectAlternativeForBasket(targetId, altId);
    });
  }
}

function updateBasketUI() {
  elements.basketList.innerHTML = '';

  if (AppState.basket.length === 0) {
    elements.basketList.innerHTML = `
      <div style="text-align: center; color: var(--text-muted); padding: 1.5rem 0;">
        <i data-lucide="shopping-cart" style="width: 40px; height: 40px; opacity: 0.4; margin-bottom: 0.5rem;"></i>
        <p style="font-size: 0.9rem;">Your prescription basket is empty.</p>
        <p style="font-size: 0.8rem;">Search and add prescribed brand drugs to compute cost audit savings.</p>
      </div>
    `;
    elements.totalSavedMonthly.textContent = '₹0.00';
    elements.totalSavedYearly.textContent = '₹0.00';
    elements.overallSavingsBadge.textContent = '0% Total Savings';
    lucide.createIcons();
    return;
  }

  // Only sum items where both brand and generic prices are known.
  // Items with unknown prices are shown clearly but excluded from totals
  // to avoid fabricating savings from null values.
  let totalOrigMonthly = 0;
  let totalGenericMonthly = 0;

  AppState.basket.forEach((item, index) => {
    const brand = item.medicine;
    const generic = item.selectedAlternative;
    const units = item.units;

    const brandPriceKnown = brand.pricePerUnit !== null && brand.pricePerUnit !== undefined;
    const genericPriceKnown = generic && generic.pricePerUnit !== null && generic.pricePerUnit !== undefined;

    // Safe per-unit cost — only computed when price is known.
    const brandMonthly = brandPriceKnown
      ? (brand.pricePerUnit / Math.max(1, brand.unitCount)) * units
      : null;
    const genericMonthly = genericPriceKnown
      ? (generic.pricePerUnit / Math.max(1, generic.unitCount)) * units
      : null;

    // Build display values — fall back to "Price unavailable" text when null.
    let savingsLine = '';
    if (brandMonthly !== null && genericMonthly !== null) {
      const monthlySaved = brandMonthly - genericMonthly;
      const savingsPct = brandMonthly > 0 ? ((brandMonthly - genericMonthly) / brandMonthly) * 100 : 0;
      savingsLine = `<div style="font-weight: 700; color: #34d399;">Saved ₹${monthlySaved.toFixed(2)}/mo</div>
        <div style="font-size: 0.75rem; color: var(--text-muted);">${savingsPct.toFixed(1)}% cheaper</div>`;
      totalOrigMonthly += brandMonthly;
      totalGenericMonthly += genericMonthly;
    } else if (brandMonthly !== null) {
      // Brand price known but generic price unknown — include brand in totals,
      // treat generic as same cost so no artificial savings are claimed.
      savingsLine = `<div style="font-size: 0.75rem; color: var(--accent-amber); font-style: italic;">Generic price unavailable — savings unknown</div>`;
      totalOrigMonthly += brandMonthly;
      totalGenericMonthly += brandMonthly;
    } else {
      savingsLine = `<div style="font-size: 0.75rem; color: var(--accent-amber); font-style: italic;">Price unavailable — excluded from savings total</div>`;
    }

    const altPriceDisplay = generic
      ? (genericPriceKnown ? `₹${generic.pricePerUnit.toFixed(2)}` : 'Price unavailable')
      : 'No generic selected';

    const basketItem = document.createElement('div');
    basketItem.className = 'basket-item';
    basketItem.innerHTML = `
      <div style="flex: 1;">
        <div style="font-weight: 700; color: #ffffff;">${brand.name}</div>
        <div style="font-size: 0.75rem; color: var(--text-muted);">${brand.saltName}</div>
        <div style="font-size: 0.8rem; color: #34d399; margin-top: 0.25rem;">
          Alt: ${generic ? generic.name : 'No generic selected'} (${altPriceDisplay})
        </div>
      </div>
      <div style="text-align: right; margin-left: 1rem;">
        ${savingsLine}
        <button style="background: transparent; border: none; color: #f43f5e; font-size: 0.75rem; cursor: pointer; margin-top: 0.2rem;" onclick="removeFromBasket(${index})">
          Remove
        </button>
      </div>
    `;
    elements.basketList.appendChild(basketItem);
  });

  const totalSavedMonthly = totalOrigMonthly - totalGenericMonthly;
  const totalSavedYearly = totalSavedMonthly * 12;
  const overallPct = totalOrigMonthly > 0 ? (totalSavedMonthly / totalOrigMonthly) * 100 : 0;

  elements.totalSavedMonthly.textContent = `₹${totalSavedMonthly.toFixed(2)}`;
  elements.totalSavedYearly.textContent = `₹${totalSavedYearly.toFixed(2)}`;
  elements.overallSavingsBadge.textContent = `${overallPct.toFixed(1)}% Overall Cost Savings`;

  lucide.createIcons();
}

function removeFromBasket(index) {
  AppState.basket.splice(index, 1);
  updateBasketUI();
}

/**
 * 7. Leaflet.js 100% Free OpenStreetMap Pharmacy Locator Engine
 */
async function loadPharmacies(city = '') {
  let list = [];
  if (AppState.isOnline) {
    try {
      const res = await fetch(`/api/pharmacies/nearby${city ? '?city=' + city : ''}`);
      if (res.ok) {
        list = await res.json();
        await OfflineStorage.syncPharmacies(list);
      } else {
        list = await OfflineStorage.getPharmaciesOffline();
      }
    } catch (e) {
      list = await OfflineStorage.getPharmaciesOffline();
    }
  } else {
    list = await OfflineStorage.getPharmaciesOffline();
  }

  AppState.pharmacies = list;
  elements.pharmacyCountBadge.textContent = `${list.length} Stores`;
  renderPharmacyList(list);
  if (AppState.leafletMap) {
    updateMapMarkers(list);
  }
}

function initLeafletMap() {
  if (AppState.leafletMap) return;

  AppState.leafletMap = L.map('leafletMap').setView([19.0760, 72.8777], 11);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(AppState.leafletMap);

  updateMapMarkers(AppState.pharmacies);
}

function updateMapMarkers(list) {
  if (!AppState.leafletMap) return;

  AppState.mapMarkers.forEach(m => AppState.leafletMap.removeLayer(m));
  AppState.mapMarkers = [];

  if (list.length === 0) return;

  const bounds = [];

  list.forEach(p => {
    const isJanAushadhi = p.type.includes('Jan Aushadhi');
    
    const markerColor = isJanAushadhi ? '#10b981' : '#3b82f6';
    const svgIcon = L.divIcon({
      className: 'custom-map-pin',
      html: `<div style="background-color: ${markerColor}; width: 24px; height: 24px; border-radius: 50%; border: 3px solid #ffffff; box-shadow: 0 4px 10px rgba(0,0,0,0.5); animation: pulseLogo 3s infinite;"></div>`,
      iconSize: [24, 24],
      iconAnchor: [12, 12]
    });

    const marker = L.marker([p.lat, p.lng], { icon: svgIcon }).addTo(AppState.leafletMap);

    const popupContent = `
      <div style="font-family: inherit; max-width: 220px;">
        <strong style="color: #0f172a; font-size: 0.95rem;">${p.name}</strong><br>
        <span style="font-size: 0.75rem; color: ${isJanAushadhi ? '#047857' : '#1d4ed8'}; font-weight: bold;">${p.type}</span><br>
        <small style="color: #475569;">${p.address}</small><br>
        <small style="color: #0284c7;">📞 ${p.phone}</small><br>
        <a href="https://www.google.com/maps/dir/?api=1&destination=${p.lat},${p.lng}" target="_blank" style="display: inline-block; margin-top: 6px; font-size: 0.8rem; background: #0d9488; color: white; padding: 4px 8px; border-radius: 6px; text-decoration: none;">Get Directions</a>
      </div>
    `;

    marker.bindPopup(popupContent);
    AppState.mapMarkers.push(marker);
    bounds.push([p.lat, p.lng]);
  });

  if (bounds.length > 0) {
    AppState.leafletMap.fitBounds(bounds, { padding: [30, 30] });
  }
}

function renderPharmacyList(list) {
  elements.pharmacyListContainer.innerHTML = '';

  if (list.length === 0) {
    elements.pharmacyListContainer.innerHTML = `
      <div style="text-align: center; color: var(--text-muted); padding: 1.5rem;">
        <p>No pharmacies found for selected location.</p>
      </div>
    `;
    return;
  }

  list.forEach((p, index) => {
    const isJanAushadhi = p.type.includes('Jan Aushadhi');
    const badgeClass = isJanAushadhi ? 'badge-generic' : 'badge-brand';

    const card = document.createElement('div');
    card.className = 'med-card';
    card.style.padding = '0.9rem';
    card.style.cursor = 'pointer';
    card.style.animationDelay = `${index * 0.05}s`;

    card.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: flex-start;">
        <div>
          <div style="font-weight: 700; color: #ffffff; font-size: 0.95rem;">${p.name}</div>
          <span class="badge-tag ${badgeClass}" style="margin: 0.2rem 0;">${p.type}</span>
        </div>
        ${p.isOpen24h ? `<span style="font-size: 0.7rem; background: rgba(16, 185, 129, 0.2); color: #34d399; padding: 0.2rem 0.4rem; border-radius: 4px; font-weight: 700;">24/7 OPEN</span>` : ''}
      </div>

      <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.2rem;">${p.address}, ${p.city}</div>
      <div style="font-size: 0.8rem; color: var(--accent-cyan); font-weight: 600; margin-top: 0.2rem;">📞 ${p.phone}</div>
      <div style="font-size: 0.75rem; color: #34d399; margin-top: 0.25rem;">📦 ${p.stockStatus}</div>

      <div style="margin-top: 0.5rem; display: flex; gap: 0.5rem;">
        <button class="btn-outline" style="flex: 1; padding: 0.35rem; font-size: 0.75rem;" onclick="focusOnMap(${p.lat}, ${p.lng})">
          <i data-lucide="map-pin" style="width: 12px; height: 12px;"></i> View on Map
        </button>
        <a href="https://www.google.com/maps/dir/?api=1&destination=${p.lat},${p.lng}" target="_blank" class="btn-primary" style="padding: 0.35rem 0.6rem; font-size: 0.75rem; text-decoration: none;">
          <i data-lucide="navigation" style="width: 12px; height: 12px;"></i> Directions
        </a>
      </div>
    `;

    elements.pharmacyListContainer.appendChild(card);
  });

  lucide.createIcons();
}

function focusOnMap(lat, lng) {
  if (AppState.leafletMap) {
    AppState.leafletMap.setView([lat, lng], 15);
    AppState.mapMarkers.forEach(m => {
      const pos = m.getLatLng();
      if (Math.abs(pos.lat - lat) < 0.001 && Math.abs(pos.lng - lng) < 0.001) {
        m.openPopup();
      }
    });
  }
}

/**
 * 8. Export Printable Cost Audit Report Modal
 */
function openReportModal() {
  if (AppState.basket.length === 0) {
    alert('Please add at least one prescribed medicine to your audit basket before generating a report.');
    return;
  }

  let tableRows = '';
  let totalOrig = 0;
  let totalGen = 0;
  let hasUnknownPrices = false;

  AppState.basket.forEach(item => {
    const b = item.medicine;
    const g = item.selectedAlternative;
    const units = item.units;

    const brandPriceKnown = b.pricePerUnit !== null && b.pricePerUnit !== undefined;
    const genericPriceKnown = g && g.pricePerUnit !== null && g.pricePerUnit !== undefined;

    // Only compute monetary values when the price is known — never fabricate from null.
    const origMonthly = brandPriceKnown ? (b.pricePerUnit / Math.max(1, b.unitCount)) * units : null;
    const genMonthly  = genericPriceKnown ? (g.pricePerUnit / Math.max(1, g.unitCount)) * units : null;

    const brandDisplay   = brandPriceKnown   ? `₹${b.pricePerUnit.toFixed(2)} (${b.dosageForm})` : `<span class="price-unavailable">Price unavailable</span>`;
    const genericDisplay = genericPriceKnown ? `₹${g.pricePerUnit.toFixed(2)}`                   : (g ? `<span class="price-unavailable">Price unavailable</span>` : '—');

    let savedDisplay = '—';
    if (origMonthly !== null && genMonthly !== null) {
      const saved = origMonthly - genMonthly;
      savedDisplay = `₹${saved.toFixed(2)}`;
      totalOrig += origMonthly;
      totalGen  += genMonthly;
    } else if (origMonthly !== null) {
      // Brand price known, generic unknown — include brand in total, no artificial savings.
      totalOrig += origMonthly;
      totalGen  += origMonthly;
      hasUnknownPrices = true;
      savedDisplay = '<span class="price-unavailable">Unknown</span>';
    } else {
      hasUnknownPrices = true;
    }

    tableRows += `
      <tr>
        <td style="padding: 8px; border-bottom: 1px solid #334155;">
          <strong>${b.name}</strong><br><small style="color: #94a3b8;">${b.saltName}</small>
        </td>
        <td style="padding: 8px; border-bottom: 1px solid #334155;">${brandDisplay}</td>
        <td style="padding: 8px; border-bottom: 1px solid #334155; color: #34d399;">
          <strong>${g ? g.name : 'N/A'}</strong><br><small style="color: #94a3b8;">${g ? g.manufacturer : ''}</small>
        </td>
        <td style="padding: 8px; border-bottom: 1px solid #334155; color: #34d399;">${genericDisplay}</td>
        <td style="padding: 8px; border-bottom: 1px solid #334155; text-align: right; color: #34d399; font-weight: bold;">${savedDisplay}</td>
      </tr>
    `;
  });

  const totalSavedMonthly = totalOrig - totalGen;
  const totalSavedYearly = totalSavedMonthly * 12;

  elements.reportModalContent.innerHTML = `
    <div style="text-align: center; border-bottom: 2px solid var(--accent-teal); padding-bottom: 1rem; margin-bottom: 1.5rem;">
      <h2 style="font-size: 1.8rem; color: var(--accent-teal); font-weight: 800;">GenericRx Prescription Cost Audit Report</h2>
      <p style="font-size: 0.9rem; color: var(--text-muted);">Generated on: ${new Date().toLocaleDateString()} • Offline-First PWA Audit System</p>
    </div>

    <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 0.9rem; margin-bottom: 1.5rem;">
      <thead>
        <tr style="background: rgba(30, 41, 59, 0.8); color: var(--accent-teal);">
          <th style="padding: 10px; border-bottom: 2px solid #334155;">Prescribed Brand Drug</th>
          <th style="padding: 10px; border-bottom: 2px solid #334155;">Brand Price</th>
          <th style="padding: 10px; border-bottom: 2px solid #334155;">Jan Aushadhi / Generic Equivalent</th>
          <th style="padding: 10px; border-bottom: 2px solid #334155;">Generic Price</th>
          <th style="padding: 10px; border-bottom: 2px solid #334155; text-align: right;">Monthly Savings</th>
        </tr>
      </thead>
      <tbody>
        ${tableRows}
      </tbody>
    </table>

    <div style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 12px; padding: 1.25rem; display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
      <div>
        <div style="font-size: 0.9rem; color: var(--text-muted);">Total Monthly Prescription Cost:</div>
        <div style="font-size: 1.1rem; text-decoration: line-through; color: #f43f5e;">₹${totalOrig.toFixed(2)} (Brand)</div>
        <div style="font-size: 1.3rem; font-weight: 800; color: #34d399;">₹${totalGen.toFixed(2)} (Generic)</div>
      </div>
      <div style="text-align: right;">
        <div style="font-size: 0.9rem; color: var(--text-muted);">Net Annual Patient Savings:</div>
        <div style="font-size: 1.8rem; font-weight: 800; color: #34d399;">₹${totalSavedYearly.toFixed(2)} / yr</div>
      </div>
    </div>

    ${hasUnknownPrices ? `<div style="border: 1px solid rgba(245,158,11,0.4); background: rgba(245,158,11,0.1); border-radius: 8px; padding: 0.75rem 1rem; margin-bottom: 1rem; font-size: 0.82rem; color: var(--accent-amber);">
      ⚠️ <strong>Price Unavailable Notice:</strong> One or more medicines in this report have unverified prices. Those items are excluded from savings totals — do not assume the savings figure covers all prescribed medications.
    </div>` : ''}

    <div style="border-top: 1px dashed var(--border-color); padding-top: 1rem; font-size: 0.8rem; color: var(--text-muted); text-align: center;">
      ⚠️ <strong>Medical Regulatory Disclaimer:</strong> This audit report is produced for financial optimization and therapeutic awareness. Patients must consult a qualified medical practitioner or pharmacist before modifying any active medication or dosage strength.
    </div>

    <div style="display: flex; gap: 1rem; margin-top: 1.5rem; justify-content: flex-end;">
      <button class="btn-outline" onclick="window.print()"><i data-lucide="printer" style="width: 16px; height: 16px;"></i> Print / Save PDF</button>
    </div>
  `;

  elements.reportModal.style.display = 'flex';
  lucide.createIcons();
}

/**
 * Event Listeners Initialization
 */
function initEventListeners() {
  // Search input debounced
  let timeout = null;
  elements.searchInput.addEventListener('input', (e) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => {
      performSearch(e.target.value);
    }, 250);
  });

  // Filter Buttons
  elements.filterButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      elements.filterButtons.forEach(b => b.classList.remove('active'));
      e.target.classList.add('active');
      AppState.activeFilter = e.target.dataset.filter;
      performSearch(AppState.currentQuery);
    });
  });

  // View Switcher Tabs
  elements.tabSearchBtn.addEventListener('click', () => {
    elements.tabSearchBtn.className = 'tab-btn active';
    elements.tabMapBtn.className = 'tab-btn';
    elements.viewSearchDashboard.style.display = 'grid';
    elements.viewMapDashboard.style.display = 'none';
    AppState.activeView = 'search';
  });

  elements.tabMapBtn.addEventListener('click', () => {
    elements.tabSearchBtn.className = 'tab-btn';
    elements.tabMapBtn.className = 'tab-btn active';
    elements.viewSearchDashboard.style.display = 'none';
    elements.viewMapDashboard.style.display = 'grid';
    AppState.activeView = 'map';
    setTimeout(() => {
      initLeafletMap();
      if (AppState.leafletMap) AppState.leafletMap.invalidateSize();
    }, 100);
  });

  // City Selector
  elements.citySelect.addEventListener('change', (e) => {
    loadPharmacies(e.target.value);
  });

  // Find Near Me GPS
  elements.btnGpsFind.addEventListener('click', () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const lat = pos.coords.latitude;
          const lng = pos.coords.longitude;
          initLeafletMap();
          AppState.leafletMap.setView([lat, lng], 14);

          L.marker([lat, lng], {
            icon: L.divIcon({
              className: 'user-gps-pin',
              html: `<div style="background-color: #ef4444; width: 22px; height: 22px; border-radius: 50%; border: 3px solid #ffffff; box-shadow: 0 0 14px #ef4444; animation: blink 1s infinite;"></div>`,
              iconSize: [22, 22]
            })
          }).addTo(AppState.leafletMap).bindPopup('<strong>📍 You Are Here</strong>').openPopup();
        },
        () => {
          alert('Could not retrieve your GPS location. Please select a city manually.');
        }
      );
    } else {
      alert('Geolocation is not supported by your browser.');
    }
  });

  // Modal handlers
  elements.exportReportBtn.addEventListener('click', openReportModal);
  elements.closeReportModal.addEventListener('click', () => {
    elements.reportModal.style.display = 'none';
  });
}
