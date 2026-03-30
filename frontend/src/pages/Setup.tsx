/**
 * First-boot Setup Wizard
 *
 * Guides the user through initial system configuration when no config file exists.
 * Steps: hostname -> radio settings -> mesh settings -> backhaul (optional) -> save
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import TeletextPanel from '../components/TeletextPanel';
import TeletextText from '../components/TeletextText';
import TeletextInput from '../components/TeletextInput';
import TeletextSelect from '../components/TeletextSelect';
import TeletextToggle from '../components/TeletextToggle';
import {
  saveConfigDefaults,
  updateConfigSection,
  checkFirstBoot,
  fetchBackhaulAdapters,
} from '../services/api';
import type { BackhaulAdapter } from '../services/api';

const STEPS = ['SYSTEM', 'RADIO', 'MESH', 'BACKHAUL', 'CONFIRM'] as const;
type Step = (typeof STEPS)[number];

const Setup: React.FC = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>('SYSTEM');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [hostname, setHostname] = useState('myc3');
  const [timezone, setTimezone] = useState('UTC');
  const [loraFrequency, setLoraFrequency] = useState('915000000');
  const [loraSf, setLoraSf] = useState('7');
  const [loraTxPower, setLoraTxPower] = useState('22');
  const [meshtasticEnabled, setMeshtasticEnabled] = useState(true);
  const [meshtasticDevice, setMeshtasticDevice] = useState('/dev/ttyUSB1');
  const [batmanSsid, setBatmanSsid] = useState('myc3lium-mesh');
  const [batmanChannel, setBatmanChannel] = useState('6');
  const [reticulumTransport, setReticulumTransport] = useState(true);

  // Backhaul
  const [backhaulAdapters, setBackhaulAdapters] = useState<BackhaulAdapter[]>([]);
  // Auto-AP defaults: AP mode is active on first boot with default creds.
  // Pre-populate so user sees current state and can change the password.
  const [backhaulEnabled, setBackhaulEnabled] = useState(true);
  const [backhaulMode, setBackhaulMode] = useState<'client' | 'ap' | 'disabled'>('ap');
  const [clientSsid, setClientSsid] = useState('');
  const [clientPassword, setClientPassword] = useState('');
  const [apSsid, setApSsid] = useState('myc3_m3sh');
  const [apPassword, setApPassword] = useState('myc3m3sh');

  useEffect(() => {
    fetchBackhaulAdapters().then((r) => setBackhaulAdapters(r.adapters)).catch(() => {});
  }, []);

  useEffect(() => {
    checkFirstBoot().then((result: { first_boot: boolean; setup_complete?: boolean }) => {
      if (result.setup_complete) {
        navigate('/p/100', { replace: true });
      }
    }).catch(() => {
      // If we can't check, stay on setup
    });
  }, [navigate]);

  const stepIndex = STEPS.indexOf(step);

  const DEFAULT_AP_PASSWORD = 'myc3m3sh';

  const nextStep = () => {
    // Block progression past BACKHAUL if AP password hasn't been changed
    if (step === 'BACKHAUL' && backhaulEnabled && backhaulMode === 'ap') {
      if (apPassword === DEFAULT_AP_PASSWORD || apPassword.length < 8) {
        setError('Change the AP password from the default before continuing');
        return;
      }
    }
    setError(null);
    const next = STEPS[stepIndex + 1];
    if (next) setStep(next);
  };

  const prevStep = () => {
    const prev = STEPS[stepIndex - 1];
    if (prev) setStep(prev);
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      await saveConfigDefaults();
      await updateConfigSection('system', { hostname, timezone });
      await updateConfigSection('radio', {
        lora_frequency: parseInt(loraFrequency, 10),
        lora_spreading_factor: parseInt(loraSf, 10),
        lora_tx_power: parseInt(loraTxPower, 10),
        meshtastic_enabled: meshtasticEnabled,
        meshtastic_device: meshtasticDevice,
      });
      await updateConfigSection('mesh', {
        batman_ssid: batmanSsid,
        batman_channel: parseInt(batmanChannel, 10),
        reticulum_transport: reticulumTransport,
      });
      if (backhaulEnabled && backhaulMode !== 'disabled') {
        await updateConfigSection('backhaul', {
          enabled: backhaulEnabled,
          mode: backhaulMode,
          client_ssid: clientSsid,
          client_password: clientPassword,
          ap_ssid: apSsid,
          ap_password: apPassword,
        });
      }
      // Mark setup as complete — must be last so partial saves don't unlock
      await updateConfigSection('system', { setup_complete: true });
      // Full page load (not SPA navigate) so iOS/Android captive portal
      // detection re-probes and closes the portal sheet
      window.location.href = '/p/100';
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to save configuration');
    } finally {
      setSaving(false);
    }
  };

  const buttonStyle: React.CSSProperties = {
    background: 'transparent',
    border: '1px solid #00FFFF',
    color: '#00FFFF',
    fontFamily: 'inherit',
    fontSize: 'inherit',
    padding: '4px 16px',
    cursor: 'pointer',
    marginRight: '8px',
  };

  const disabledButtonStyle: React.CSSProperties = {
    ...buttonStyle,
    color: '#808080',
    borderColor: '#808080',
    cursor: 'default',
  };

  return (
    <div style={{ background: '#000', color: '#fff', minHeight: '100vh', padding: '16px', fontFamily: 'monospace' }}>
      <TeletextPanel title="MYC3LIUM FIRST-BOOT SETUP" color="cyan">
        <TeletextText color="yellow">
          STEP {stepIndex + 1}/{STEPS.length}: {step}
        </TeletextText>
      </TeletextPanel>

      <div style={{ marginTop: '8px' }}>
        {step === 'SYSTEM' && (
          <TeletextPanel title="SYSTEM IDENTITY" color="cyan">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', padding: '4px' }}>
              <TeletextInput
                label="HOSTNAME"
                value={hostname}
                onChange={setHostname}
                placeholder="myc3"
                maxLength={63}
              />
              <TeletextText color="gray">
                System will be accessible at {hostname}.local
              </TeletextText>
              <TeletextInput
                label="TIMEZONE"
                value={timezone}
                onChange={setTimezone}
                placeholder="UTC"
              />
            </div>
          </TeletextPanel>
        )}

        {step === 'RADIO' && (
          <TeletextPanel title="RADIO CONFIGURATION" color="cyan">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', padding: '4px' }}>
              <TeletextSelect
                label="LORA FREQUENCY"
                value={loraFrequency}
                onChange={setLoraFrequency}
                options={[
                  { value: '915000000', label: '915 MHz (US ISM)' },
                  { value: '868000000', label: '868 MHz (EU)' },
                  { value: '923000000', label: '923 MHz (AS)' },
                ]}
              />
              <TeletextSelect
                label="SPREADING FACTOR"
                value={loraSf}
                onChange={setLoraSf}
                options={[
                  { value: '7', label: 'SF7 (fast, short range)' },
                  { value: '8', label: 'SF8' },
                  { value: '9', label: 'SF9' },
                  { value: '10', label: 'SF10' },
                  { value: '11', label: 'SF11' },
                  { value: '12', label: 'SF12 (slow, long range)' },
                ]}
              />
              <TeletextInput
                label="TX POWER (dBm)"
                value={loraTxPower}
                onChange={setLoraTxPower}
                type="number"
              />
              <TeletextToggle
                label="MESHTASTIC"
                value={meshtasticEnabled}
                onChange={setMeshtasticEnabled}
              />
              {meshtasticEnabled && (
                <TeletextInput
                  label="MESHTASTIC DEVICE"
                  value={meshtasticDevice}
                  onChange={setMeshtasticDevice}
                />
              )}
            </div>
          </TeletextPanel>
        )}

        {step === 'MESH' && (
          <TeletextPanel title="MESH NETWORK" color="cyan">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', padding: '4px' }}>
              <TeletextInput
                label="BATMAN MESH SSID"
                value={batmanSsid}
                onChange={setBatmanSsid}
                maxLength={32}
              />
              <TeletextSelect
                label="WIFI CHANNEL"
                value={batmanChannel}
                onChange={setBatmanChannel}
                options={Array.from({ length: 11 }, (_, i) => ({
                  value: String(i + 1),
                  label: `Channel ${i + 1}`,
                }))}
              />
              <TeletextToggle
                label="RETICULUM TRANSPORT"
                value={reticulumTransport}
                onChange={setReticulumTransport}
              />
            </div>
          </TeletextPanel>
        )}

        {step === 'BACKHAUL' && (
          <TeletextPanel title="BACKHAUL / AP MODE (OPTIONAL)" color="cyan">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', padding: '4px' }}>
              {backhaulAdapters.length === 0 ? (
                <>
                  <TeletextText color="yellow">NO USB WIFI ADAPTER DETECTED</TeletextText>
                  <TeletextText color="gray">
                    Skip this step or plug in a USB WiFi adapter and reload.
                  </TeletextText>
                </>
              ) : (
                <>
                  <TeletextText color="green">
                    ADAPTER: {backhaulAdapters[0].name} ({backhaulAdapters[0].driver})
                  </TeletextText>
                  <TeletextText color="yellow">
                    AP mode is active with default password. Change it below.
                  </TeletextText>
                  <TeletextToggle
                    label="ENABLE BACKHAUL"
                    value={backhaulEnabled}
                    onChange={setBackhaulEnabled}
                  />
                  {backhaulEnabled && (
                    <>
                      <TeletextSelect
                        label="MODE"
                        value={backhaulMode}
                        onChange={(v) => setBackhaulMode(v as 'client' | 'ap' | 'disabled')}
                        options={[
                          { value: 'disabled', label: 'DISABLED' },
                          { value: 'client', label: 'CLIENT (join WiFi for internet)' },
                          { value: 'ap', label: 'AP (broadcast myc3_m3sh hotspot)' },
                        ]}
                      />
                      {backhaulMode === 'client' && (
                        <>
                          <TeletextInput label="WIFI SSID" value={clientSsid} onChange={setClientSsid} />
                          <TeletextInput label="WIFI PASSWORD" value={clientPassword} onChange={setClientPassword} />
                        </>
                      )}
                      {backhaulMode === 'ap' && (
                        <>
                          <TeletextInput label="AP SSID" value={apSsid} onChange={setApSsid} placeholder="myc3_m3sh" />
                          <TeletextInput label="AP PASSWORD (min 8)" value={apPassword} onChange={setApPassword} />
                        </>
                      )}
                    </>
                  )}
                </>
              )}
            </div>
          </TeletextPanel>
        )}

        {step === 'CONFIRM' && (
          <TeletextPanel title="REVIEW CONFIGURATION" color="yellow">
            <div style={{ padding: '4px', lineHeight: '1.6' }}>
              <TeletextText color="cyan">SYSTEM</TeletextText>
              <TeletextText color="white">  Hostname: {hostname}.local</TeletextText>
              <TeletextText color="white">  Timezone: {timezone}</TeletextText>
              <TeletextText color="cyan">RADIO</TeletextText>
              <TeletextText color="white">  LoRa: {(parseInt(loraFrequency, 10) / 1e6).toFixed(0)} MHz, SF{loraSf}, {loraTxPower} dBm</TeletextText>
              <TeletextText color="white">  Meshtastic: {meshtasticEnabled ? `ON (${meshtasticDevice})` : 'OFF'}</TeletextText>
              <TeletextText color="cyan">MESH</TeletextText>
              <TeletextText color="white">  SSID: {batmanSsid}</TeletextText>
              <TeletextText color="white">  Channel: {batmanChannel}</TeletextText>
              <TeletextText color="white">  Reticulum: {reticulumTransport ? 'ON' : 'OFF'}</TeletextText>
              <TeletextText color="cyan">BACKHAUL</TeletextText>
              {backhaulEnabled && backhaulMode !== 'disabled' ? (
                <>
                  <TeletextText color="white">  Mode: {backhaulMode.toUpperCase()}</TeletextText>
                  {backhaulMode === 'client' && (
                    <TeletextText color="white">  SSID: {clientSsid}</TeletextText>
                  )}
                  {backhaulMode === 'ap' && (
                    <TeletextText color="white">  SSID: {apSsid}</TeletextText>
                  )}
                </>
              ) : (
                <TeletextText color="gray">  Disabled (configure later in P600)</TeletextText>
              )}
            </div>
          </TeletextPanel>
        )}
      </div>

      {error && (
        <div style={{ marginTop: '8px' }}>
          <TeletextText color="red">ERROR: {error}</TeletextText>
        </div>
      )}

      <div style={{ marginTop: '12px', display: 'flex' }}>
        <button
          onClick={prevStep}
          disabled={stepIndex === 0}
          style={stepIndex === 0 ? disabledButtonStyle : buttonStyle}
        >
          BACK
        </button>
        {step === 'CONFIRM' ? (
          <button
            onClick={handleSave}
            disabled={saving}
            style={{ ...buttonStyle, borderColor: '#00FF00', color: '#00FF00' }}
          >
            {saving ? 'SAVING...' : 'SAVE & START'}
          </button>
        ) : (
          <button onClick={nextStep} style={buttonStyle}>
            NEXT
          </button>
        )}
      </div>
    </div>
  );
};

export default Setup;
