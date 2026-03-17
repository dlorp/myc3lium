import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import P600 from './P600'
import { getMockRadioConfig, renderRadioConfig } from './P600.utils'
import useNavigationStore from '../store/navigationStore'
import { COLUMNS, ROWS } from '../components/TeletextGrid'

describe('P600 - Radio Configuration Page', () => {
  beforeEach(() => {
    useNavigationStore.setState({
      currentPage: 600,
      history: [600],
      breadcrumbs: [],
    })
  })

  it('renders without crashing', () => {
    render(<P600 />)
    expect(screen.getByText(/P600 - RADIO CONFIG/i)).toBeTruthy()
  })

  it('displays radio configuration interface', () => {
    const { container } = render(<P600 />)
    expect(container.querySelector('.teletext-demo')).toBeTruthy()
  })
  
  it('sets breadcrumbs to RADIO, P600', () => {
    render(<P600 />)
    
    const state = useNavigationStore.getState()
    expect(state.breadcrumbs).toEqual(['RADIO', 'P600'])
  })
})

describe('P600.utils - Radio Configuration Logic', () => {
  describe('getMockRadioConfig', () => {
    it('returns complete radio config structure', () => {
      const config = getMockRadioConfig()
      
      expect(config).toBeDefined()
      expect(config.lora).toBeDefined()
      expect(config.halow).toBeDefined()
      expect(config.sdr).toBeDefined()
      expect(config.mesh).toBeDefined()
    })

    it('includes LoRa configuration parameters', () => {
      const config = getMockRadioConfig()
      
      expect(config.lora.freq).toBe('915.000 MHz')
      expect(config.lora.sf).toBe('7 / 9 (long range)')
      expect(config.lora.bw).toBe('125 kHz')
      expect(config.lora.cr).toBe('4/5')
      expect(config.lora.txPower).toBe('20 dBm (1W EIRP)')
      expect(config.lora.preamble).toBe('8 symbols')
      expect(config.lora.sync).toBe('0x12 private')
      expect(config.lora.status).toBe('TX/RX ACTIVE')
    })

    it('includes HaLow configuration parameters', () => {
      const config = getMockRadioConfig()
      
      expect(config.halow.ssid).toBe('MYC3LIUM_HALOW')
      expect(config.halow.freq).toBe('2339.1 MHz')
      expect(config.halow.mode).toBe('802.11ah STA')
      expect(config.halow.txPower).toBe('20 dBm')
      expect(config.halow.status).toBe('ASSOCIATED')
    })

    it('includes SDR configuration parameters', () => {
      const config = getMockRadioConfig()
      
      expect(config.sdr.center).toBe('915.000 MHz')
      expect(config.sdr.bw).toBe('2.4 MHz')
      expect(config.sdr.gain).toBe('32.8 dB AGC')
      expect(config.sdr.driver).toBe('SoapySDR')
      expect(config.sdr.status).toBe('STANDBY')
    })

    it('includes mesh network status', () => {
      const config = getMockRadioConfig()
      
      expect(config.mesh.batmanAdv).toBe('MESH OK')
      expect(config.mesh.rns).toBe('E2E ENCRYPTED')
      expect(config.mesh.meshtastic).toBe('BRIDGE ACTIVE')
      expect(config.mesh.fccCompliance).toBe('FCC Part 15.247')
    })
  })

  describe('renderRadioConfig', () => {
    it('renders valid teletext grid', () => {
      const config = getMockRadioConfig()
      const grid = renderRadioConfig(config, 'lora')
      
      expect(grid).toHaveLength(ROWS)
      grid.forEach(row => {
        expect(row).toHaveLength(COLUMNS)
      })
    })

    it('includes all three radio interface sections', () => {
      const config = getMockRadioConfig()
      const grid = renderRadioConfig(config, 'lora')
      
      const gridText = grid.map(row => row.join('')).join('')
      
      // Check for interface labels
      expect(gridText).toContain('LoRa')
      expect(gridText).toContain('HaLow')
      expect(gridText).toContain('SDR')
    })

    it('displays LoRa parameters correctly', () => {
      const config = getMockRadioConfig()
      const grid = renderRadioConfig(config, 'lora')
      
      const gridText = grid.map(row => row.join('')).join('')
      
      expect(gridText).toContain('LoRa')
      expect(gridText).toContain('915')
      expect(gridText).toContain('TX/RX ACTIVE')
    })

    it('displays HaLow parameters correctly', () => {
      const config = getMockRadioConfig()
      const grid = renderRadioConfig(config, 'halow')
      
      const gridText = grid.map(row => row.join('')).join('')
      
      expect(gridText).toContain('HaLow')
      expect(gridText).toContain('MYC3LIUM_HALOW')
      expect(gridText).toContain('ASSOCIATED')
    })

    it('displays SDR parameters correctly', () => {
      const config = getMockRadioConfig()
      const grid = renderRadioConfig(config, 'sdr')
      
      const gridText = grid.map(row => row.join('')).join('')
      
      expect(gridText).toContain('SDR')
      expect(gridText).toContain('SoapySDR')
      expect(gridText).toContain('STANDBY')
    })

    it('displays mesh network status in footer', () => {
      const config = getMockRadioConfig()
      const grid = renderRadioConfig(config, 'lora')
      
      const gridText = grid.map(row => row.join('')).join('')
      
      expect(gridText).toContain('BATMAN')
      expect(gridText).toContain('RNS')
      expect(gridText).toContain('MESHTASTIC')
      expect(gridText).toContain('FCC')
    })

    it('includes keyboard hints in footer', () => {
      const config = getMockRadioConfig()
      const grid = renderRadioConfig(config, 'lora')
      
      const gridText = grid.map(row => row.join('')).join('')
      
      expect(gridText).toContain('[L]')
      expect(gridText).toContain('[H]')
      expect(gridText).toContain('[S]')
      expect(gridText).toContain('[A]')
    })

    it('renders title and page identifier', () => {
      const config = getMockRadioConfig()
      const grid = renderRadioConfig(config, 'lora')
      
      const gridText = grid.map(row => row.join('')).join('')
      
      expect(gridText).toContain('RADIO CONFIG')
      expect(gridText).toContain('P600')
    })
  })
})
