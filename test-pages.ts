/**
 * Test Pages for MYC3LIUM Teletext Renderer
 * 
 * Generates mock content for P100-P800 series pages
 * to test the bitmap font atlas rendering system.
 */

export type PageContent = string[][];

const COLS = 80;
const ROWS = 25;

/**
 * Create empty page grid
 */
function createEmptyPage(): PageContent {
  return Array(ROWS).fill(null).map(() => Array(COLS).fill(' '));
}

/**
 * Write text to page at position
 */
function writeText(page: PageContent, row: number, col: number, text: string) {
  for (let i = 0; i < text.length && col + i < COLS; i++) {
    page[row][col + i] = text[i];
  }
}

/**
 * Draw box border using CP437 box drawing characters
 */
function drawBox(page: PageContent, startRow: number, startCol: number, width: number, height: number) {
  // Top border
  page[startRow][startCol] = '┌';
  for (let i = 1; i < width - 1; i++) {
    page[startRow][startCol + i] = '─';
  }
  page[startRow][startCol + width - 1] = '┐';

  // Sides
  for (let i = 1; i < height - 1; i++) {
    page[startRow + i][startCol] = '│';
    page[startRow + i][startCol + width - 1] = '│';
  }

  // Bottom border
  page[startRow + height - 1][startCol] = '└';
  for (let i = 1; i < width - 1; i++) {
    page[startRow + height - 1][startCol + i] = '─';
  }
  page[startRow + height - 1][startCol + width - 1] = '┘';
}

/**
 * P100: Main Menu
 */
export function generateP100(): PageContent {
  const page = createEmptyPage();
  
  drawBox(page, 0, 0, COLS, ROWS);
  writeText(page, 0, 2, 'MAIN MENU');
  writeText(page, 0, COLS - 23, '19:45');
  writeText(page, 0, COLS - 15, '[SPORE-07]');
  
  writeText(page, 2, 2, 'MYC3LIUM LATTICE CONTROL');
  writeText(page, 3, 2, '═══════════════════════════');
  
  writeText(page, 5, 2, '100 SERIES: SYSTEM & MENU');
  writeText(page, 6, 4, 'P100 - Main Menu');
  writeText(page, 7, 4, 'P101 - System Status');
  writeText(page, 8, 4, 'P102 - Power/Battery');
  writeText(page, 9, 4, 'P103 - Radio Status');
  
  writeText(page, 11, 2, '200 SERIES: MESH NETWORK');
  writeText(page, 12, 4, 'P200 - Lattice Topology');
  writeText(page, 13, 4, 'P201 - Node List');
  writeText(page, 14, 4, 'P202 - Link Quality');
  
  writeText(page, 16, 2, '400 SERIES: MAPS');
  writeText(page, 17, 4, 'P400 - Primary Map View');
  
  writeText(page, 19, 2, '500 SERIES: INTELLIGENCE');
  writeText(page, 20, 4, 'P500 - Satellite Tracker');
  writeText(page, 21, 4, 'P501 - RF Spectrum');
  
  writeText(page, ROWS - 1, 2, '[100]MENU─[200]LATTICE─[400]MAP─[500]INTEL');
  
  return page;
}

/**
 * P200: Lattice Topology Map
 */
export function generateP200(): PageContent {
  const page = createEmptyPage();
  
  drawBox(page, 0, 0, COLS, ROWS);
  writeText(page, 0, 2, 'LATTICE MAP');
  writeText(page, 0, COLS - 23, '19:45');
  writeText(page, 0, COLS - 15, '[5 CELLS]');
  
  writeText(page, 2, 2, 'TOPOLOGY:');
  
  // ASCII art topology
  writeText(page, 4, 4, '┌───HYPHA-03 (2.1km N)');
  writeText(page, 5, 4, '│   LoRa -78dBm GOOD');
  writeText(page, 6, 4, '│');
  writeText(page, 7, 2, '◉─┼───SPORE-07 (5.8km NE)');
  writeText(page, 8, 2, 'SPORE  HaLow -85dBm FAIR');
  writeText(page, 9, 2, '(THIS) │');
  writeText(page, 10, 4, '└───RHIZOME-12 (1.2km W)');
  writeText(page, 11, 8, 'LoRa -82dBm GOOD');
  
  writeText(page, 14, 2, 'THREADS: 8 ACTIVE / 2 DEGRADED');
  writeText(page, 15, 2, 'STORE-FWD QUEUE: 3 msgs (42 KB)');
  
  writeText(page, 17, 2, '[R] REGENERATE  [P] PROPAGATE');
  
  writeText(page, ROWS - 1, 2, '[100]MENU─[201]NODES──────[203]STATS');
  
  return page;
}

/**
 * P300: Messaging Inbox
 */
export function generateP300(): PageContent {
  const page = createEmptyPage();
  
  drawBox(page, 0, 0, COLS, ROWS);
  writeText(page, 0, 2, 'INBOX');
  writeText(page, 0, COLS - 23, '19:45');
  writeText(page, 0, COLS - 15, '[3 UNREAD]');
  
  writeText(page, 2, 2, 'MSG   FROM           TIME    SUBJECT');
  writeText(page, 3, 2, '────────────────────────────────────────────────────');
  
  writeText(page, 4, 2, '[●] HYPHA-03       19:42    THREAD DEGRADED');
  writeText(page, 5, 2, '[●] SPORE-01       19:38    SENSOR DATA BURST');
  writeText(page, 6, 2, '[●] RHIZOME-12     19:21    ALERT: LOW BATTERY');
  writeText(page, 7, 2, '[ ] FROND-05       18:55    CAMERA FEED AVAILABLE');
  writeText(page, 8, 2, '[ ] SPORE-07       18:42    LATTICE REGENERATED');
  
  writeText(page, 11, 2, 'CHANNELS:');
  writeText(page, 12, 4, '#FIELD-OPS    (Meshtastic)');
  writeText(page, 13, 4, '#SIGINT       (LXMF)');
  writeText(page, 14, 4, '#SENSOR-NET   (LXMF)');
  
  writeText(page, ROWS - 1, 2, '[100]MENU─[301]COMPOSE─[302]CHANNELS');
  
  return page;
}

/**
 * P400: Primary Map View
 */
export function generateP400(): PageContent {
  const page = createEmptyPage();
  
  drawBox(page, 0, 0, COLS, ROWS);
  writeText(page, 0, 2, 'PRIMARY MAP VIEW');
  writeText(page, 0, COLS - 30, 'LAT: 47.6062° N');
  writeText(page, 0, COLS - 15, 'LON: 122.3321° W');
  
  // Simplified map placeholder
  for (let row = 2; row < ROWS - 2; row++) {
    for (let col = 2; col < COLS - 2; col++) {
      if (Math.random() < 0.05) {
        page[row][col] = '░';
      } else if (Math.random() < 0.08) {
        page[row][col] = '▒';
      }
    }
  }
  
  // Node markers
  writeText(page, 8, 30, '◉ THIS');
  writeText(page, 5, 35, '● HYPHA-03');
  writeText(page, 12, 25, '● RHIZOME-12');
  
  writeText(page, ROWS - 1, 2, '[100]MENU─[401]WAYPOINTS─[403]LAYERS');
  
  return page;
}

/**
 * P500: Satellite Tracker
 */
export function generateP500(): PageContent {
  const page = createEmptyPage();
  
  drawBox(page, 0, 0, COLS, ROWS);
  writeText(page, 0, 2, 'SATELLITE TRACKER');
  writeText(page, 0, COLS - 23, '19:45');
  writeText(page, 0, COLS - 15, '[3 PASSES]');
  
  writeText(page, 2, 2, 'UPCOMING PASSES:');
  writeText(page, 3, 2, '────────────────────────────────────────────────────');
  
  writeText(page, 4, 2, 'NOAA-18');
  writeText(page, 5, 4, 'AOS: 20:12 UTC  MAX EL: 42°  LOS: 20:23 UTC');
  writeText(page, 6, 4, 'Freq: 137.9125 MHz  Mode: APT');
  
  writeText(page, 8, 2, 'ISS (ZARYA)');
  writeText(page, 9, 4, 'AOS: 21:45 UTC  MAX EL: 67°  LOS: 21:52 UTC');
  writeText(page, 10, 4, 'Freq: 145.800 MHz  Mode: SSTV/Voice');
  
  writeText(page, 12, 2, 'METEOR-M2');
  writeText(page, 13, 4, 'AOS: 22:34 UTC  MAX EL: 28°  LOS: 22:47 UTC');
  writeText(page, 14, 4, 'Freq: 137.1000 MHz  Mode: LRPT');
  
  writeText(page, 17, 2, 'SDR STATUS: ● ACTIVE');
  writeText(page, 18, 2, 'AUTO-RECORD: ENABLED');
  
  writeText(page, ROWS - 1, 2, '[100]MENU─[501]SPECTRUM─[502]LOG');
  
  return page;
}

/**
 * P700: Sensor Grid
 */
export function generateP700(): PageContent {
  const page = createEmptyPage();
  
  drawBox(page, 0, 0, COLS, ROWS);
  writeText(page, 0, 2, 'SENSOR GRID (RHIZOME)');
  writeText(page, 0, COLS - 23, '19:45');
  writeText(page, 0, COLS - 15, '[12 NODES]');
  
  writeText(page, 2, 2, 'NODE         TEMP    RH%   PRESS   BATT   STATUS');
  writeText(page, 3, 2, '────────────────────────────────────────────────────');
  
  writeText(page, 4, 2, 'RHIZOME-01   18.2°C  67%   1013mb  85%    GOOD');
  writeText(page, 5, 2, 'RHIZOME-02   19.1°C  62%   1012mb  78%    GOOD');
  writeText(page, 6, 2, 'RHIZOME-03   17.8°C  71%   1014mb  92%    GOOD');
  writeText(page, 7, 2, 'RHIZOME-12   16.5°C  58%   1015mb  23%    ⚠ LOW BATT');
  writeText(page, 8, 2, 'RHIZOME-15   --.-°C  --%   ----mb  --%    ✗ OFFLINE');
  
  writeText(page, 11, 2, 'AGGREGATE DATA (LAST 1H):');
  writeText(page, 12, 4, 'AVG TEMP:  18.1°C  (±1.2°C)');
  writeText(page, 13, 4, 'AVG RH:    64.2%   (±5.8%)');
  writeText(page, 14, 4, 'PRESSURE:  1013mb  (stable)');
  
  writeText(page, 17, 2, 'SPARKLINE: ▁▂▃▄▅▆▇█▇▆▅▄▃▂▁ (TEMP TREND)');
  
  writeText(page, ROWS - 1, 2, '[100]MENU─[701]DETAIL─[702]TRENDS');
  
  return page;
}

/**
 * P800: LLM Interface
 */
export function generateP800(): PageContent {
  const page = createEmptyPage();
  
  drawBox(page, 0, 0, COLS, ROWS);
  writeText(page, 0, 2, 'LLM AGENT INTERFACE');
  writeText(page, 0, COLS - 23, '19:45');
  writeText(page, 0, COLS - 15, '[ONLINE]');
  
  writeText(page, 2, 2, 'QUERY: lattice status');
  writeText(page, 3, 2, '────────────────────────────────────────────────────');
  
  writeText(page, 5, 2, 'AGENT:');
  writeText(page, 6, 4, 'Current lattice topology shows 5 active cells with');
  writeText(page, 7, 4, '8 established threads. 2 threads are degraded due to');
  writeText(page, 8, 4, 'increased distance. Store-and-forward queue contains');
  writeText(page, 9, 4, '3 pending messages (42 KB). RHIZOME-12 reports low');
  writeText(page, 10, 4, 'battery (23%). Recommend manual retrieval or solar');
  writeText(page, 11, 4, 'charging within 24 hours.');
  
  writeText(page, 14, 2, 'SUGGESTED ACTIONS:');
  writeText(page, 15, 4, '1. Navigate to P200 for detailed thread analysis');
  writeText(page, 16, 4, '2. Check RHIZOME-12 battery status on P700');
  writeText(page, 17, 4, '3. Review pending messages on P300');
  
  writeText(page, 20, 2, '> _');
  
  writeText(page, ROWS - 1, 2, '[100]MENU─[801]QUERY─[802]INSIGHTS');
  
  return page;
}

/**
 * Page registry
 */
export const TEST_PAGES: Record<number, () => PageContent> = {
  100: generateP100,
  200: generateP200,
  300: generateP300,
  400: generateP400,
  500: generateP500,
  700: generateP700,
  800: generateP800
};
