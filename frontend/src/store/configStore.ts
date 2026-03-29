import { create } from 'zustand';

import {
  checkFirstBoot as apiCheckFirstBoot,
  fetchConfig,
  restartService as apiRestartService,
  saveConfigDefaults,
  updateConfigSection,
} from '../services/api';

// ============================================================================
// Config Interfaces (mirrors backend Pydantic models)
// ============================================================================

export interface RadioConfig {
  lora_frequency: number;
  lora_bandwidth: number;
  lora_spreading_factor: number;
  lora_tx_power: number;
  meshtastic_device: string;
  meshtastic_enabled: boolean;
}

export interface MeshConfig {
  batman_channel: number;
  batman_ssid: string;
  reticulum_transport: boolean;
  store_forward_enabled: boolean;
  store_forward_max_messages: number;
}

export interface DisplayConfig {
  crt_effects: boolean;
  scanlines: boolean;
  phosphor_glow: boolean;
  brightness: number;
  color_scheme: string;
}

export interface SystemConfig {
  hostname: string;
  timezone: string;
  log_level: string;
  auto_start_meshtastic: boolean;
  api_key: string;
}

export interface Myc3liumConfig {
  radio: RadioConfig;
  mesh: MeshConfig;
  display: DisplayConfig;
  system: SystemConfig;
}

// ============================================================================
// Store State & Actions
// ============================================================================

interface ConfigState {
  config: Myc3liumConfig | null;
  loading: boolean;
  saving: boolean;
  error: string | null;
  saveSuccess: boolean;
  isFirstBoot: boolean;

  loadConfig: () => Promise<void>;
  checkFirstBoot: () => Promise<void>;
  updateSection: (section: string, updates: Record<string, unknown>) => Promise<void>;
  saveDefaults: () => Promise<void>;
  restartService: (name: string) => Promise<void>;
  clearSaveStatus: () => void;
}

const useConfigStore = create<ConfigState>((set) => ({
  config: null,
  loading: false,
  saving: false,
  error: null,
  saveSuccess: false,
  isFirstBoot: false,

  loadConfig: async () => {
    set({ loading: true, error: null });
    try {
      const data = await fetchConfig();
      set({ config: data as unknown as Myc3liumConfig, loading: false });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load config';
      set({ error: message, loading: false });
    }
  },

  checkFirstBoot: async () => {
    try {
      const data = await apiCheckFirstBoot();
      set({ isFirstBoot: data.first_boot });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to check first boot status';
      set({ error: message });
    }
  },

  updateSection: async (section: string, updates: Record<string, unknown>) => {
    set({ saving: true, error: null, saveSuccess: false });
    try {
      const response = await updateConfigSection(section, updates);
      // Backend returns { status, section, config: {...} } — extract the config data
      const sectionData = (response as Record<string, unknown>).config ?? response;
      set((state) => {
        if (!state.config) return { saving: false, saveSuccess: true };
        return {
          config: {
            ...state.config,
            [section]: sectionData,
          },
          saving: false,
          saveSuccess: true,
        };
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : `Failed to update ${section}`;
      set({ error: message, saving: false, saveSuccess: false });
    }
  },

  saveDefaults: async () => {
    set({ saving: true, error: null, saveSuccess: false });
    try {
      await saveConfigDefaults();
      // Reload full config after creating defaults (response is just {status})
      const config = await fetchConfig();
      set({
        config: config as unknown as Myc3liumConfig,
        saving: false,
        saveSuccess: true,
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to save defaults';
      set({ error: message, saving: false, saveSuccess: false });
    }
  },

  restartService: async (name: string) => {
    set({ saving: true, error: null });
    try {
      await apiRestartService(name);
      set({ saving: false, saveSuccess: true });
    } catch (err) {
      const message = err instanceof Error ? err.message : `Failed to restart ${name}`;
      set({ error: message, saving: false });
    }
  },

  clearSaveStatus: () => {
    set({ saveSuccess: false, error: null });
  },
}));

export default useConfigStore;
