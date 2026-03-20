# ⚠️ Legal & Regulatory Compliance

**CRITICAL:** MYC3LIUM operates radio equipment on licensed frequency bands. **YOU are responsible for compliance with local regulations.**

---

## United States (FCC)

### Part 15.247 - ISM Band Operation

**Frequency Bands Used:**
- **915 MHz ISM** - LoRa (SX1262) + HaLow (802.11ah)
- **2.4 GHz ISM** - WiFi mesh (Pi built-in)

**Power Limits:**
- **Max EIRP:** 1 Watt (30 dBm) for 915 MHz
- **Calculation:** EIRP = TX Power + Antenna Gain - Cable Loss
- **Example:** 17 dBm TX + 3 dBi antenna = 20 dBm EIRP ✅ (compliant)

**Antenna Requirements:**
- Must use FCC-approved antennas or calculate EIRP correctly
- Fixed antennas: 1W EIRP
- Point-to-point: up to 4W EIRP with directional antennas

**Identification:**
- No operator license required (Part 15 unlicensed)
- Optional: Use callsign in LoRa beacon for traceability

**Prohibited:**
- **DO NOT** exceed 30 dBm EIRP on 915 MHz
- **DO NOT** cause harmful interference to licensed services
- **DO NOT** operate near airports without coordination (RFI risk)

**Penalties:**
- Fines: Up to **$10,000 per day** per violation
- Equipment confiscation
- Criminal charges for intentional interference

---

## Verify Your Configuration

**Check LoRa TX Power:**
```bash
grep "txpower" ~/.reticulum/config
# Should show: txpower = 17  (or lower)
```

**Check Antenna Gain:**
- Waveshare SX1262 includes magnetic CB antenna (~3 dBi)
- EIRP = 17 dBm + 3 dBi = 20 dBm ✅ **COMPLIANT**

**If using external antenna:**
```
TX Power (dBm) + Antenna Gain (dBi) - Cable Loss (dB) ≤ 30 dBm
```

**Example with high-gain antenna:**
- 8 dBi antenna → Max TX power = 22 dBm
- 10 dBi antenna → Max TX power = 20 dBm

---

## International Regulations

### Europe (ETSI)
**Standard:** EN 300 220  
**Frequency:** 868 MHz (EU SRD band)  
**Max Power:** 25 mW ERP (14 dBm)  
**Duty Cycle:** 1% (36 seconds per hour)

**Configuration for EU:**
```ini
# ~/.reticulum/config
frequency = 868000000
txpower = 14
```

### Japan
**Standard:** ARIB STD-T108  
**Frequency:** 920 MHz  
**Max Power:** 20 mW (13 dBm)  
**License:** Required for some applications

### Australia
**Standard:** LIPD Class License  
**Frequency:** 915-928 MHz  
**Max Power:** 1W EIRP  
**Similar to FCC Part 15**

### Canada
**Standard:** RSS-247  
**Frequency:** 902-928 MHz  
**Max Power:** 1W EIRP (same as FCC)

---

## WiFi HaLow (802.11ah)

**FCC:** Part 15.407  
**Frequency:** 902-928 MHz (S1G band)  
**Max Power:** Varies by channel bandwidth
- 1 MHz: 30 dBm EIRP
- 2 MHz: 27 dBm EIRP
- 4 MHz: 24 dBm EIRP

**HT-HC01P Default:** Typically compliant out-of-box

---

## GNSS/GPS

**Waveshare SX1262 HAT includes GNSS receiver**

**FCC:** Receive-only, no transmission → **No restrictions**  
**ITAR:** GPS receivers with encryption may have export restrictions (basic receivers exempt)

**MYC3LIUM GPS:** Civilian-grade receiver, no ITAR concerns

---

## Bluetooth

**Pi 4 Bluetooth 5.0:** FCC Part 15.247  
**Max Power:** 100 mW (20 dBm)  
**Class 1 Devices:** Compliant as shipped

---

## Export Controls (ITAR/EAR)

**Software:**
- Encryption: Reticulum uses AES-256
- **ECCN:** 5D002 (publicly available encryption)
- **Export:** Generally allowed under License Exception TSU

**Hardware:**
- Commercial off-the-shelf (COTS) components
- No ITAR-controlled items in BOM
- **Export:** Verify destination country (some restrictions for embargoed nations)

**Deployment Abroad:**
- Check local frequency allocations
- Verify power limits
- Obtain licenses if required (some countries require amateur radio license)

---

## Amateur Radio Alternative

**If you have an amateur radio license:**

**Benefits:**
- Higher power allowed (up to 1500W in some bands)
- Access to dedicated amateur allocations (e.g., 33 cm band)
- Legal protection for experimentation

**Requirements:**
- Must use amateur callsign in transmissions
- **No encryption** on amateur bands (Reticulum encryption prohibited)
- Must operate only on amateur-allocated frequencies

**MYC3LIUM Compatibility:**
- LoRa can operate on 70cm (420-450 MHz) or 33cm (902-928 MHz) amateur bands
- Remove encryption or use separate amateur-only node

---

## Compliance Checklist

Before deploying MYC3LIUM:

- [ ] Verified frequency matches your region (915 MHz US, 868 MHz EU, etc.)
- [ ] Calculated EIRP (TX power + antenna gain ≤ 30 dBm)
- [ ] Checked local regulations (consult national spectrum authority)
- [ ] Configured TX power in Reticulum config
- [ ] Using approved/documented antennas
- [ ] Not operating near sensitive sites (airports, military bases)
- [ ] Aware of penalties for non-compliance

**If unsure, consult a local RF compliance expert or amateur radio community.**

---

## Spectrum Authority Contacts

| Country | Authority | Website |
|---------|-----------|---------|
| USA | FCC | fcc.gov |
| Canada | ISED | ised-isde.canada.ca |
| UK | Ofcom | ofcom.org.uk |
| EU | ETSI | etsi.org |
| Australia | ACMA | acma.gov.au |
| Japan | MIC | soumu.go.jp |

---

## Disclaimer

**This document provides general guidance only. It is NOT legal advice.**

**You are solely responsible for:**
- Compliance with all applicable laws and regulations
- Obtaining necessary licenses or permits
- Ensuring your configuration meets local power limits
- Liability for interference or violations

**When in doubt, consult a qualified RF engineer or legal counsel.**

**Failure to comply may result in:**
- Equipment confiscation
- Monetary fines (potentially thousands of dollars per day)
- Criminal prosecution (for intentional interference)
- Civil liability (for damages caused by interference)

---

**Deploy responsibly. Respect the spectrum. 📡**
