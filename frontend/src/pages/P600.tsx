import React, { useState, useEffect, useCallback } from 'react';
import { TeletextPanel } from '../components/TeletextPanel';
import { TeletextText } from '../components/TeletextText';
import { TeletextInput } from '../components/TeletextInput';
import { TeletextSelect } from '../components/TeletextSelect';
import { TeletextToggle } from '../components/TeletextToggle';
import useConfigStore from '../store/configStore';

interface RadioConfig {
  lora_frequency: number;
  lora_bandwidth: number;
  lora_spreading_factor: number;
  lora_tx_power: number;
  meshtastic_device: string;
  meshtastic_enabled: boolean;
}

interface MeshConfig {
  batman_channel: number;
  batman_band: '2.4GHz' | '5GHz';
  batman_ssid: string;
  reticulum_transport: boolean;
  store_forward_enabled: boolean;
  store_forward_max_messages: number;
}

interface BackhaulConfig {
  enabled: boolean;
  interface: string;
  mode: 'client' | 'ap' | 'disabled';
  client_ssid: string;
  client_password: string;
  ap_ssid: string;
  ap_password: string;
  ap_channel: number;
  ap_band: '2.4GHz' | '5GHz';
  ap_hidden: boolean;
  nat_enabled: boolean;
}

interface DisplayConfig {
  crt_effects: boolean;
  scanlines: boolean;
  phosphor_glow: boolean;
  brightness: number;
  color_scheme: string;
}

interface SystemConfig {
  hostname: string;
  timezone: string;
  log_level: string;
  auto_start_meshtastic: boolean;
}

const RADIO_DEFAULTS: RadioConfig = {
  lora_frequency: 915000000,
  lora_bandwidth: 125000,
  lora_spreading_factor: 7,
  lora_tx_power: 22,
  meshtastic_device: '/dev/ttyUSB1',
  meshtastic_enabled: true,
};

const MESH_DEFAULTS: MeshConfig = {
  batman_channel: 6,
  batman_band: '2.4GHz',
  batman_ssid: 'myc3lium-mesh',
  reticulum_transport: true,
  store_forward_enabled: true,
  store_forward_max_messages: 1000,
};

const BACKHAUL_DEFAULTS: BackhaulConfig = {
  enabled: false,
  interface: '',
  mode: 'disabled',
  client_ssid: '',
  client_password: '',
  ap_ssid: 'myc3_m3sh',
  ap_password: '',
  ap_channel: 1,
  ap_band: '2.4GHz',
  ap_hidden: false,
  nat_enabled: true,
};

const DISPLAY_DEFAULTS: DisplayConfig = {
  crt_effects: true,
  scanlines: true,
  phosphor_glow: true,
  brightness: 100,
  color_scheme: 'classic',
};

const SYSTEM_DEFAULTS: SystemConfig = {
  hostname: 'myc3',
  timezone: 'UTC',
  log_level: 'INFO',
  auto_start_meshtastic: true,
};

const ActionButton: React.FC<{
  onClick: () => void;
  saving: boolean;
  label: string;
  activeLabel: string;
  color?: string;
}> = ({ onClick, saving, label, activeLabel, color = '#00FF00' }) => (
  <button
    onClick={onClick}
    disabled={saving}
    style={{
      backgroundColor: '#000',
      color: saving ? '#808080' : color,
      border: `1px solid ${color}`,
      fontFamily: 'IBM VGA, monospace',
      fontSize: '14px',
      padding: '4px 16px',
      cursor: saving ? 'not-allowed' : 'pointer',
      marginTop: '8px',
      marginRight: '8px',
    }}
  >
    {saving ? activeLabel : label}
  </button>
);

const SaveButton: React.FC<{ onClick: () => void; saving: boolean }> = ({ onClick, saving }) => (
  <ActionButton onClick={onClick} saving={saving} label="[ SAVE ]" activeLabel="SAVING..." />
);

const P600: React.FC = () => {
  const {
    config, loading, saving, error, saveSuccess,
    loadConfig, updateSection, clearSaveStatus,
    backhaulAdapters, loadBackhaulAdapters, applyBackhaul, applyNetwork,
  } = useConfigStore();

  const [radio, setRadio] = useState<RadioConfig>(RADIO_DEFAULTS);
  const [mesh, setMesh] = useState<MeshConfig>(MESH_DEFAULTS);
  const [backhaul, setBackhaul] = useState<BackhaulConfig>(BACKHAUL_DEFAULTS);
  const [display, setDisplay] = useState<DisplayConfig>(DISPLAY_DEFAULTS);
  const [system, setSystem] = useState<SystemConfig>(SYSTEM_DEFAULTS);

  useEffect(() => {
    loadConfig();
    loadBackhaulAdapters();
  }, [loadConfig, loadBackhaulAdapters]);

  // Sync local state when config loads
  useEffect(() => {
    if (!config) return;
    if (config.radio) setRadio((prev) => ({ ...prev, ...config.radio }));
    if (config.mesh) setMesh((prev) => ({ ...prev, ...config.mesh }));
    if (config.backhaul) setBackhaul((prev) => ({ ...prev, ...config.backhaul }));
    if (config.display) setDisplay((prev) => ({ ...prev, ...config.display }));
    if (config.system) setSystem((prev) => ({ ...prev, ...config.system }));
  }, [config]);

  // Clear save status after 3 seconds
  useEffect(() => {
    if (!saveSuccess) return;
    const timer = setTimeout(() => clearSaveStatus(), 3000);
    return () => clearTimeout(timer);
  }, [saveSuccess, clearSaveStatus]);

  const handleSave = useCallback(
    (section: string, data: Record<string, unknown>) => {
      return updateSection(section, data);
    },
    [updateSection]
  );

  const timestamp = new Date().toLocaleString('en-US', { hour12: false });

  if (loading) {
    return (
      <div style={{ backgroundColor: '#000', minHeight: '100vh', padding: '20px' }}>
        <TeletextText color="yellow" blink>LOADING CONFIGURATION...</TeletextText>
      </div>
    );
  }

  return (
    <div style={{ backgroundColor: '#000', minHeight: '100vh', padding: '20px', overflowY: 'auto' }}>
      <TeletextText color="cyan">P600 -- SYSTEM CONFIGURATION</TeletextText>
      <br />
      <TeletextText color="gray">{timestamp}</TeletextText>

      {saveSuccess && (
        <div style={{ marginTop: '8px' }}>
          <TeletextText color="green">CONFIG SAVED</TeletextText>
        </div>
      )}
      {error && (
        <div style={{ marginTop: '8px' }}>
          <TeletextText color="red">ERROR: {error}</TeletextText>
        </div>
      )}

      {/* Radio Section */}
      <div style={{ marginTop: '16px' }}>
        <TeletextPanel title="RADIO CONFIGURATION" color="cyan">
          <TeletextInput
            label="LoRa Frequency (Hz)"
            value={radio.lora_frequency}
            onChange={(v) => setRadio((p) => ({ ...p, lora_frequency: Number(v) || 0 }))}
            type="number"
          />
          <TeletextSelect
            label="LoRa Bandwidth"
            value={String(radio.lora_bandwidth)}
            onChange={(v) => setRadio((p) => ({ ...p, lora_bandwidth: Number(v) }))}
            options={[
              { label: '125 kHz', value: '125000' },
              { label: '250 kHz', value: '250000' },
              { label: '500 kHz', value: '500000' },
            ]}
          />
          <TeletextSelect
            label="LoRa Spreading Factor"
            value={String(radio.lora_spreading_factor)}
            onChange={(v) => setRadio((p) => ({ ...p, lora_spreading_factor: Number(v) }))}
            options={[7, 8, 9, 10, 11, 12].map((n) => ({ label: `SF${n}`, value: String(n) }))}
          />
          <TeletextInput
            label="LoRa TX Power (dBm, 0-22)"
            value={radio.lora_tx_power}
            onChange={(v) => {
              const n = Math.max(0, Math.min(22, Number(v) || 0));
              setRadio((p) => ({ ...p, lora_tx_power: n }));
            }}
            type="number"
          />
          <TeletextInput
            label="Meshtastic Device"
            value={radio.meshtastic_device}
            onChange={(v) => setRadio((p) => ({ ...p, meshtastic_device: v }))}
            placeholder="/dev/ttyUSB0"
          />
          <TeletextToggle
            label="Meshtastic Enabled"
            value={radio.meshtastic_enabled}
            onChange={(v) => setRadio((p) => ({ ...p, meshtastic_enabled: v }))}
          />
          <div style={{ display: 'flex', gap: '8px' }}>
            <SaveButton onClick={() => handleSave('radio', radio)} saving={saving} />
            <ActionButton
              onClick={applyNetwork}
              saving={saving}
              label="[ APPLY TO SYSTEM ]"
              activeLabel="APPLYING..."
              color="#FF9500"
            />
          </div>
        </TeletextPanel>
      </div>

      {/* Mesh Section */}
      <div style={{ marginTop: '16px' }}>
        <TeletextPanel title="MESH CONFIGURATION" color="magenta">
          <TeletextSelect
            label="BATMAN WiFi Band"
            value={mesh.batman_band}
            onChange={(v) => setMesh((p) => ({
              ...p,
              batman_band: v as '2.4GHz' | '5GHz',
              batman_channel: v === '5GHz' ? 36 : 6,
            }))}
            options={[
              { label: '2.4 GHz', value: '2.4GHz' },
              { label: '5 GHz', value: '5GHz' },
            ]}
          />
          <TeletextInput
            label={mesh.batman_band === '5GHz' ? 'BATMAN Channel (36-165)' : 'BATMAN Channel (1-11)'}
            value={mesh.batman_channel}
            onChange={(v) => {
              const max = mesh.batman_band === '5GHz' ? 165 : 11;
              const min = mesh.batman_band === '5GHz' ? 36 : 1;
              const n = Math.max(min, Math.min(max, Number(v) || min));
              setMesh((p) => ({ ...p, batman_channel: n }));
            }}
            type="number"
          />
          <TeletextInput
            label="BATMAN SSID"
            value={mesh.batman_ssid}
            onChange={(v) => setMesh((p) => ({ ...p, batman_ssid: v }))}
          />
          <TeletextToggle
            label="Reticulum Transport"
            value={mesh.reticulum_transport}
            onChange={(v) => setMesh((p) => ({ ...p, reticulum_transport: v }))}
          />
          <TeletextToggle
            label="Store & Forward"
            value={mesh.store_forward_enabled}
            onChange={(v) => setMesh((p) => ({ ...p, store_forward_enabled: v }))}
          />
          <TeletextInput
            label="Max Messages (100-10000)"
            value={mesh.store_forward_max_messages}
            onChange={(v) => {
              const n = Math.max(100, Math.min(10000, Number(v) || 100));
              setMesh((p) => ({ ...p, store_forward_max_messages: n }));
            }}
            type="number"
          />
          <div style={{ display: 'flex', gap: '8px' }}>
            <SaveButton onClick={() => handleSave('mesh', mesh)} saving={saving} />
            <ActionButton
              onClick={applyNetwork}
              saving={saving}
              label="[ APPLY TO SYSTEM ]"
              activeLabel="APPLYING..."
              color="#FF9500"
            />
          </div>
        </TeletextPanel>
      </div>

      {/* Backhaul Section */}
      <div style={{ marginTop: '16px' }}>
        <TeletextPanel title="BACKHAUL / AP MODE" color="cyan">
          {backhaulAdapters.length === 0 ? (
            <TeletextText color="red">NO USB WIFI ADAPTER DETECTED</TeletextText>
          ) : (
            <TeletextText color="green">
              ADAPTER: {backhaulAdapters[0].name} ({backhaulAdapters[0].driver})
            </TeletextText>
          )}

          <TeletextToggle
            label="Backhaul Enabled"
            value={backhaul.enabled}
            onChange={(v) => setBackhaul((p) => ({ ...p, enabled: v }))}
          />

          {backhaul.enabled && (
            <>
              {backhaulAdapters.length > 1 && (
                <TeletextSelect
                  label="Interface"
                  value={backhaul.interface || backhaulAdapters[0]?.name || ''}
                  onChange={(v) => setBackhaul((p) => ({ ...p, interface: v }))}
                  options={backhaulAdapters.map((a) => ({
                    label: `${a.name} (${a.driver})`,
                    value: a.name,
                  }))}
                />
              )}

              <TeletextSelect
                label="Mode"
                value={backhaul.mode}
                onChange={(v) => setBackhaul((p) => ({
                  ...p,
                  mode: v as 'client' | 'ap' | 'disabled',
                }))}
                options={[
                  { label: 'DISABLED', value: 'disabled' },
                  { label: 'CLIENT (join WiFi)', value: 'client' },
                  { label: 'AP (broadcast hotspot)', value: 'ap' },
                ]}
              />

              {backhaul.mode === 'client' && (
                <>
                  <TeletextInput
                    label="WiFi SSID"
                    value={backhaul.client_ssid}
                    onChange={(v) => setBackhaul((p) => ({ ...p, client_ssid: v }))}
                    placeholder="Network name"
                  />
                  <TeletextInput
                    label="WiFi Password"
                    value={backhaul.client_password === '***' ? '' : backhaul.client_password}
                    onChange={(v) => setBackhaul((p) => ({ ...p, client_password: v }))}
                    placeholder="Network password"
                  />
                </>
              )}

              {backhaul.mode === 'ap' && (
                <>
                  <TeletextInput
                    label="AP SSID"
                    value={backhaul.ap_ssid}
                    onChange={(v) => setBackhaul((p) => ({ ...p, ap_ssid: v }))}
                    placeholder="myc3_m3sh"
                  />
                  <TeletextInput
                    label="AP Password (min 8 chars)"
                    value={backhaul.ap_password === '***' ? '' : backhaul.ap_password}
                    onChange={(v) => setBackhaul((p) => ({ ...p, ap_password: v }))}
                    placeholder="WPA2 password"
                  />
                  <TeletextSelect
                    label="AP Band"
                    value={backhaul.ap_band}
                    onChange={(v) => setBackhaul((p) => ({
                      ...p,
                      ap_band: v as '2.4GHz' | '5GHz',
                      ap_channel: v === '5GHz' ? 36 : 6,
                    }))}
                    options={[
                      { label: '2.4 GHz', value: '2.4GHz' },
                      { label: '5 GHz (recommended)', value: '5GHz' },
                    ]}
                  />
                  <TeletextInput
                    label={backhaul.ap_band === '5GHz' ? 'AP Channel (36-165)' : 'AP Channel (1-11)'}
                    value={backhaul.ap_channel}
                    onChange={(v) => {
                      const max = backhaul.ap_band === '5GHz' ? 165 : 11;
                      const min = backhaul.ap_band === '5GHz' ? 36 : 1;
                      const n = Math.max(min, Math.min(max, Number(v) || min));
                      setBackhaul((p) => ({ ...p, ap_channel: n }));
                    }}
                    type="number"
                  />
                  <TeletextToggle
                    label="Hidden SSID"
                    value={backhaul.ap_hidden}
                    onChange={(v) => setBackhaul((p) => ({ ...p, ap_hidden: v }))}
                  />
                </>
              )}

              {backhaul.mode !== 'disabled' && (
                <TeletextToggle
                  label="NAT (Internet Sharing)"
                  value={backhaul.nat_enabled}
                  onChange={(v) => setBackhaul((p) => ({ ...p, nat_enabled: v }))}
                />
              )}
            </>
          )}

          <div style={{ display: 'flex', gap: '8px' }}>
            <SaveButton onClick={() => {
              // Strip masked passwords so we don't overwrite stored values
              const payload = { ...backhaul };
              if (payload.client_password === '***' || payload.client_password === '') {
                delete (payload as Record<string, unknown>).client_password;
              }
              if (payload.ap_password === '***' || payload.ap_password === '') {
                delete (payload as Record<string, unknown>).ap_password;
              }
              handleSave('backhaul', payload);
            }} saving={saving} />
            {backhaul.enabled && backhaul.mode !== 'disabled' && (
              <ActionButton
                onClick={async () => {
                  const payload = { ...backhaul };
                  if (payload.client_password === '***' || payload.client_password === '') {
                    delete (payload as Record<string, unknown>).client_password;
                  }
                  if (payload.ap_password === '***' || payload.ap_password === '') {
                    delete (payload as Record<string, unknown>).ap_password;
                  }
                  await handleSave('backhaul', payload);
                  await applyBackhaul();
                }}
                saving={saving}
                label="[ APPLY BACKHAUL ]"
                activeLabel="APPLYING..."
                color="#FF9500"
              />
            )}
          </div>
        </TeletextPanel>
      </div>

      {/* Display Section */}
      <div style={{ marginTop: '16px' }}>
        <TeletextPanel title="DISPLAY CONFIGURATION" color="yellow">
          <TeletextToggle
            label="CRT Effects"
            value={display.crt_effects}
            onChange={(v) => setDisplay((p) => ({ ...p, crt_effects: v }))}
          />
          <TeletextToggle
            label="Scanlines"
            value={display.scanlines}
            onChange={(v) => setDisplay((p) => ({ ...p, scanlines: v }))}
          />
          <TeletextToggle
            label="Phosphor Glow"
            value={display.phosphor_glow}
            onChange={(v) => setDisplay((p) => ({ ...p, phosphor_glow: v }))}
          />
          <TeletextInput
            label="Brightness (10-100)"
            value={display.brightness}
            onChange={(v) => {
              const n = Math.max(10, Math.min(100, Number(v) || 10));
              setDisplay((p) => ({ ...p, brightness: n }));
            }}
            type="number"
          />
          <TeletextSelect
            label="Color Scheme"
            value={display.color_scheme}
            onChange={(v) => setDisplay((p) => ({ ...p, color_scheme: v }))}
            options={[
              { label: 'CLASSIC', value: 'classic' },
              { label: 'AMBER', value: 'amber' },
              { label: 'GREEN', value: 'green' },
            ]}
          />
          <SaveButton onClick={() => handleSave('display', display)} saving={saving} />
        </TeletextPanel>
      </div>

      {/* System Section */}
      <div style={{ marginTop: '16px' }}>
        <TeletextPanel title="SYSTEM CONFIGURATION" color="green">
          <TeletextInput
            label="Hostname"
            value={system.hostname}
            onChange={(v) => setSystem((p) => ({ ...p, hostname: v }))}
          />
          <TeletextInput
            label="Timezone"
            value={system.timezone}
            onChange={(v) => setSystem((p) => ({ ...p, timezone: v }))}
          />
          <TeletextSelect
            label="Log Level"
            value={system.log_level}
            onChange={(v) => setSystem((p) => ({ ...p, log_level: v }))}
            options={['DEBUG', 'INFO', 'WARNING', 'ERROR'].map((l) => ({ label: l, value: l }))}
          />
          <TeletextToggle
            label="Auto Start Meshtastic"
            value={system.auto_start_meshtastic}
            onChange={(v) => setSystem((p) => ({ ...p, auto_start_meshtastic: v }))}
          />
          <SaveButton onClick={() => handleSave('system', system)} saving={saving} />
        </TeletextPanel>
      </div>

      <div style={{ marginTop: '16px', paddingBottom: '20px' }}>
        <TeletextText color="gray">
          Press ESC to return | Changes are applied per-section
        </TeletextText>
      </div>
    </div>
  );
};

export default P600;
