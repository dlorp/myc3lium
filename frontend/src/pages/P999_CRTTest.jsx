/**
 * P999 - CRT Shader Test Page
 * 
 * Manual verification of enhanced shader effects
 * Preset switcher, real-time parameter adjustment
 */

import { useState } from 'react'
import TeletextGrid from '../components/TeletextGrid'
import { CRT_PRESETS, listPresets } from '../components/crtPresets'
import '../styles/index.css'

// Test content with varied density
const TEST_CONTENT = [
  '░▒▓█ CHROMATIC ABERRATION TEST █▓▒░'.split(''),
  'RGB color separation at edges'.split(''),
  '                                        '.split(''),
  '▓▓▓ BLOOM / GLOW TEST ▓▓▓'.split(''),
  'Bright text should have amber halo'.split(''),
  '                                        '.split(''),
  '>>> PHOSPHOR TRAILS TEST <<<'.split(''),
  'Scroll this line to see persistence'.split(''),
  '                                        '.split(''),
  '░░░░ STATIC NOISE TEST ░░░░'.split(''),
  'Fine animated grain across surface'.split(''),
  '                                        '.split(''),
  '⚡⚡⚡ SCREEN FLICKER TEST ⚡⚡⚡'.split(''),
  'Subtle brightness variation 12Hz'.split(''),
  '                                        '.split(''),
  '╔════════════════════════════════════╗'.split(''),
  '║  ALL EFFECTS COMBINED RENDERING   ║'.split(''),
  '║  Underground polish demoscene vibe║'.split(''),
  '║  Basement hacker 3am aesthetic    ║'.split(''),
  '╚════════════════════════════════════╝'.split(''),
  '                                        '.split(''),
  'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'.split(''),
  'abcdefghijklmnopqrstuvwxyz!@#$%^&*()'.split(''),
  '                                        '.split(''),
  'FPS monitor enabled for performance'.split(''),
]

const P999_CRTTest = () => {
  const presetNames = listPresets()
  const [currentPreset, setCurrentPreset] = useState('default')
  const [customConfig, setCustomConfig] = useState(CRT_PRESETS.default)
  const [useCustom, setUseCustom] = useState(false)

  const handlePresetChange = (e) => {
    const name = e.target.value
    setCurrentPreset(name)
    setCustomConfig(CRT_PRESETS[name])
    setUseCustom(false)
  }

  const handleParamChange = (param, value) => {
    setCustomConfig(prev => ({
      ...prev,
      [param]: value,
    }))
    setUseCustom(true)
  }

  const handleToggleChange = (param) => {
    setCustomConfig(prev => ({
      ...prev,
      [param]: !prev[param],
    }))
    setUseCustom(true)
  }

  const activeConfig = customConfig

  return (
    <div className="page-container" style={{ 
      display: 'flex', 
      flexDirection: 'row',
      width: '100vw',
      height: '100vh',
      background: '#0E0B02',
    }}>
      {/* Control Panel */}
      <div style={{
        width: '300px',
        padding: '20px',
        background: '#1a1a1a',
        color: '#FFB800',
        fontFamily: 'monospace',
        fontSize: '12px',
        overflowY: 'auto',
        borderRight: '2px solid #FFB800',
      }}>
        <h2 style={{ color: '#FFB800', marginBottom: '20px' }}>CRT SHADER TEST</h2>
        
        {/* Preset Selector */}
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', marginBottom: '8px' }}>
            PRESET:
          </label>
          <select 
            value={currentPreset} 
            onChange={handlePresetChange}
            style={{
              width: '100%',
              padding: '8px',
              background: '#0E0B02',
              color: '#FFB800',
              border: '1px solid #FFB800',
              fontFamily: 'monospace',
            }}
          >
            {presetNames.map(name => (
              <option key={name} value={name}>
                {name.toUpperCase()}
              </option>
            ))}
          </select>
        </div>

        {useCustom && (
          <div style={{ 
            padding: '8px', 
            background: '#2a2a2a', 
            marginBottom: '12px',
            border: '1px solid #E88A00',
          }}>
            ⚠ CUSTOM CONFIG
          </div>
        )}

        {/* Effect Toggles */}
        <div style={{ marginBottom: '20px' }}>
          <h3 style={{ color: '#E88A00', marginBottom: '12px' }}>TOGGLES:</h3>
          
          {['enableChromatic', 'enableBloom', 'enablePhosphor', 'enableNoise', 'enableFlicker'].map(param => (
            <label key={param} style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
              <input
                type="checkbox"
                checked={activeConfig[param]}
                onChange={() => handleToggleChange(param)}
                style={{ marginRight: '8px' }}
              />
              {param.replace('enable', '').toUpperCase()}
            </label>
          ))}
        </div>

        {/* Parameter Sliders */}
        <div>
          <h3 style={{ color: '#E88A00', marginBottom: '12px' }}>PARAMETERS:</h3>
          
          {/* Chromatic Amount */}
          <div style={{ marginBottom: '12px' }}>
            <label style={{ display: 'block', marginBottom: '4px' }}>
              CHROMATIC: {activeConfig.chromaticAmount.toFixed(4)}
            </label>
            <input
              type="range"
              min="0"
              max="0.003"
              step="0.0001"
              value={activeConfig.chromaticAmount}
              onChange={(e) => handleParamChange('chromaticAmount', parseFloat(e.target.value))}
              style={{ width: '100%' }}
            />
          </div>

          {/* Bloom Strength */}
          <div style={{ marginBottom: '12px' }}>
            <label style={{ display: 'block', marginBottom: '4px' }}>
              BLOOM: {activeConfig.bloomStrength.toFixed(2)}
            </label>
            <input
              type="range"
              min="0"
              max="1.0"
              step="0.01"
              value={activeConfig.bloomStrength}
              onChange={(e) => handleParamChange('bloomStrength', parseFloat(e.target.value))}
              style={{ width: '100%' }}
            />
          </div>

          {/* Phosphor Decay */}
          <div style={{ marginBottom: '12px' }}>
            <label style={{ display: 'block', marginBottom: '4px' }}>
              PHOSPHOR: {activeConfig.phosphorDecay.toFixed(2)}
            </label>
            <input
              type="range"
              min="0"
              max="0.99"
              step="0.01"
              value={activeConfig.phosphorDecay}
              onChange={(e) => handleParamChange('phosphorDecay', parseFloat(e.target.value))}
              style={{ width: '100%' }}
            />
          </div>

          {/* Noise Amount */}
          <div style={{ marginBottom: '12px' }}>
            <label style={{ display: 'block', marginBottom: '4px' }}>
              NOISE: {activeConfig.noiseAmount.toFixed(3)}
            </label>
            <input
              type="range"
              min="0"
              max="0.15"
              step="0.001"
              value={activeConfig.noiseAmount}
              onChange={(e) => handleParamChange('noiseAmount', parseFloat(e.target.value))}
              style={{ width: '100%' }}
            />
          </div>

          {/* Flicker Amount */}
          <div style={{ marginBottom: '12px' }}>
            <label style={{ display: 'block', marginBottom: '4px' }}>
              FLICKER: {activeConfig.flickerAmount.toFixed(3)}
            </label>
            <input
              type="range"
              min="0"
              max="0.03"
              step="0.001"
              value={activeConfig.flickerAmount}
              onChange={(e) => handleParamChange('flickerAmount', parseFloat(e.target.value))}
              style={{ width: '100%' }}
            />
          </div>
        </div>

        <div style={{ marginTop: '20px', padding: '12px', background: '#2a2a2a', fontSize: '10px' }}>
          <strong>TESTING NOTES:</strong><br/>
          • Check chromatic RGB split at edges<br/>
          • Verify bloom glow on bright text<br/>
          • Scroll to test phosphor trails<br/>
          • Observe animated grain noise<br/>
          • Flicker subtle (1-2% variation)<br/>
          • Monitor FPS (target 60fps)<br/>
        </div>
      </div>

      {/* Shader Display */}
      <div style={{ flex: 1, position: 'relative' }}>
        <TeletextGrid 
          content={TEST_CONTENT}
          showFps={true}
          effectsConfig={activeConfig}
        />
      </div>
    </div>
  )
}

export default P999_CRTTest
