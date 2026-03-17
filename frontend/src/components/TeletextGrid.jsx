import { useEffect, useMemo, useRef, useState } from 'react'
import PropTypes from 'prop-types'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { OrthographicCamera } from '@react-three/drei'
import * as THREE from 'three'

const COLUMNS = 80
const ROWS = 25

const COLORS = {
  background: '#0E0B02',
  primary: '#FFB800',
  secondary: '#E88A00',
  tertiary: '#C47A00',
}

// IBM VGA 8×16 font atlas parameters
const ATLAS_GLYPH_WIDTH = 8
const ATLAS_GLYPH_HEIGHT = 16
const ATLAS_COLS = 16

const VERTEX_SHADER = `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`

const FRAGMENT_SHADER = `
  uniform sampler2D uTexture;
  uniform sampler2D uPrevFrame;
  uniform vec2 uResolution;
  uniform float uTime;
  uniform float uCurvature;
  uniform float uDeltaTime;
  
  // Effect toggles
  uniform bool uEnableChromatic;
  uniform bool uEnableBloom;
  uniform bool uEnablePhosphor;
  uniform bool uEnableNoise;
  uniform bool uEnableFlicker;
  
  // Effect parameters
  uniform float uChromaticAmount;
  uniform float uBloomStrength;
  uniform float uPhosphorDecay;
  uniform float uNoiseAmount;
  uniform float uFlickerAmount;
  
  varying vec2 vUv;

  // Curvature distortion
  vec2 distort(vec2 uv) {
    vec2 centered = uv * 2.0 - 1.0;
    float r2 = dot(centered, centered);
    centered *= 1.0 + uCurvature * r2;
    return centered * 0.5 + 0.5;
  }

  // High-quality random noise function
  float random(vec3 scale, float seed) {
    return fract(sin(dot(vec3(scale.xy, seed), vec3(12.9898, 78.233, 45.164))) * 43758.5453 + seed);
  }

  // 3D value noise for animated grain
  float noise(vec3 p) {
    vec3 i = floor(p);
    vec3 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    
    float n = i.x + i.y * 57.0 + 113.0 * i.z;
    return mix(
      mix(
        mix(random(i, n), random(i + vec3(1.0, 0.0, 0.0), n), f.x),
        mix(random(i + vec3(0.0, 1.0, 0.0), n), random(i + vec3(1.0, 1.0, 0.0), n), f.x),
        f.y
      ),
      mix(
        mix(random(i + vec3(0.0, 0.0, 1.0), n), random(i + vec3(1.0, 0.0, 1.0), n), f.x),
        mix(random(i + vec3(0.0, 1.0, 1.0), n), random(i + vec3(1.0, 1.0, 1.0), n), f.x),
        f.y
      ),
      f.z
    );
  }

  void main() {
    vec2 uv = distort(vUv);
    
    // Out of bounds check
    if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) {
      gl_FragColor = vec4(0.055, 0.043, 0.008, 1.0);
      return;
    }

    vec2 texel = 1.0 / uResolution;
    vec3 color = vec3(0.0);

    // 1. RGB CHROMATIC ABERRATION (lateral)
    if (uEnableChromatic) {
      // Lateral horizontal misconvergence - RGB electron gun misalignment
      vec2 offset = vec2(uChromaticAmount, 0.0);
      float r = texture2D(uTexture, uv + offset).r;
      float g = texture2D(uTexture, uv).g;
      float b = texture2D(uTexture, uv - offset).b;
      color = vec3(r, g, b);
    } else {
      color = texture2D(uTexture, uv).rgb;
    }

    // 2. WEIGHTED BLOOM (9-tap box blur)
    if (uEnableBloom) {
      vec3 bloom = vec3(0.0);
      
      // 3x3 weighted kernel (box blur approximation)
      bloom += texture2D(uTexture, uv + texel * vec2(-1.0, -1.0)).rgb * 0.0625;
      bloom += texture2D(uTexture, uv + texel * vec2(0.0, -1.0)).rgb * 0.125;
      bloom += texture2D(uTexture, uv + texel * vec2(1.0, -1.0)).rgb * 0.0625;
      
      bloom += texture2D(uTexture, uv + texel * vec2(-1.0, 0.0)).rgb * 0.125;
      bloom += texture2D(uTexture, uv).rgb * 0.25;
      bloom += texture2D(uTexture, uv + texel * vec2(1.0, 0.0)).rgb * 0.125;
      
      bloom += texture2D(uTexture, uv + texel * vec2(-1.0, 1.0)).rgb * 0.0625;
      bloom += texture2D(uTexture, uv + texel * vec2(0.0, 1.0)).rgb * 0.125;
      bloom += texture2D(uTexture, uv + texel * vec2(1.0, 1.0)).rgb * 0.0625;
      
      // Add bloom to base color
      color += bloom * uBloomStrength;
    }

    // 3. PHOSPHOR TRAILS (persistence of vision)
    if (uEnablePhosphor) {
      vec3 prevColor = texture2D(uPrevFrame, uv).rgb;
      // Exponential decay based on actual time delta
      float decay = pow(uPhosphorDecay, uDeltaTime * 60.0); // Normalize to 60fps
      color = max(color, prevColor * decay);
    }

    // 4. SCANLINES (enhanced from original)
    float scan = sin((uv.y * uResolution.y + uTime * 20.0) * 3.14159);
    float scanline = mix(0.82, 1.0, scan * 0.5 + 0.5);
    color *= scanline;

    // 5. STATIC NOISE (animated grain)
    if (uEnableNoise) {
      float noiseVal = noise(vec3(uv * uResolution * 0.5, uTime * 8.0));
      noiseVal = noiseVal * 2.0 - 1.0; // Remap to -1..1
      color += vec3(noiseVal) * uNoiseAmount;
    }

    // 6. SCREEN FLICKER (subtle brightness variation)
    if (uEnableFlicker) {
      // Combine slow sine wave with noise for organic feel
      float flicker = sin(uTime * 12.0) * 0.5 + 0.5; // 12Hz flicker
      flicker += noise(vec3(uTime * 4.0, 0.0, 0.0)) - 0.5;
      flicker = 1.0 - (flicker * uFlickerAmount);
      color *= flicker;
    }

    // 7. VIGNETTE
    float vignette = smoothstep(0.8, 0.2, length(vUv - 0.5));
    color *= mix(0.9, 1.0, vignette);

    gl_FragColor = vec4(color, 1.0);
  }
`

const normalizeContent = (content) => {
  const safeContent = Array.isArray(content) ? content : []
  return Array.from({ length: ROWS }, (_, rowIndex) => {
    const row = safeContent[rowIndex] ?? []
    const chars = Array.isArray(row) ? row : String(row).split('')
    const normalized = chars.slice(0, COLUMNS)
    while (normalized.length < COLUMNS) {
      normalized.push(' ')
    }
    return normalized
  })
}

const TeletextPlane = ({ content, effectsConfig = {} }) => {
  const { viewport } = useThree()
  const canvasRef = useRef(document.createElement('canvas'))
  const fontAtlasRef = useRef(null)
  const materialRef = useRef(null)
  const prevFrameTarget = useRef(null)
  const lastFrameTime = useRef(0)

  const { texture, resolution, charWidth, charHeight } = useMemo(() => {
    const charWidthValue = ATLAS_GLYPH_WIDTH
    const charHeightValue = ATLAS_GLYPH_HEIGHT
    const width = COLUMNS * charWidthValue
    const height = ROWS * charHeightValue

    const canvas = canvasRef.current
    canvas.width = width
    canvas.height = height

    const canvasTexture = new THREE.CanvasTexture(canvas)
    canvasTexture.colorSpace = THREE.SRGBColorSpace
    canvasTexture.minFilter = THREE.LinearFilter
    canvasTexture.magFilter = THREE.LinearFilter
    canvasTexture.generateMipmaps = false

    return {
      texture: canvasTexture,
      resolution: new THREE.Vector2(width, height),
      charWidth: charWidthValue,
      charHeight: charHeightValue,
    }
  }, [])

  // Initialize render target for phosphor trails
  useEffect(() => {
    const width = resolution.x
    const height = resolution.y
    prevFrameTarget.current = new THREE.WebGLRenderTarget(width, height, {
      minFilter: THREE.LinearFilter,
      magFilter: THREE.LinearFilter,
      format: THREE.RGBAFormat,
    })

    return () => {
      prevFrameTarget.current?.dispose()
    }
  }, [resolution])

  // Load font atlas
  useEffect(() => {
    const loader = new THREE.TextureLoader()
    loader.load(
      '/fonts/vga-8x16-atlas.png',
      (atlasTexture) => {
        atlasTexture.minFilter = THREE.NearestFilter
        atlasTexture.magFilter = THREE.NearestFilter
        atlasTexture.generateMipmaps = false
        fontAtlasRef.current = atlasTexture
      },
      undefined,
      (error) => {
        console.error('Failed to load font atlas:', error)
      }
    )
  }, [])

  // Initialize render target for phosphor trails
  useEffect(() => {
    const width = resolution.x
    const height = resolution.y
    prevFrameTarget.current = new THREE.WebGLRenderTarget(width, height, {
      minFilter: THREE.LinearFilter,
      magFilter: THREE.LinearFilter,
      format: THREE.RGBAFormat,
    })

    return () => {
      prevFrameTarget.current?.dispose()
    }
  }, [resolution])

  useEffect(() => {
    if (!fontAtlasRef.current) return

    const draw = () => {
      const grid = normalizeContent(content)
      const canvas = canvasRef.current
      const ctx = canvas.getContext('2d')
      if (!ctx) return

      // Clear canvas with background color
      ctx.fillStyle = COLORS.background
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      // Create temporary canvas for font atlas access
      const atlasCanvas = document.createElement('canvas')
      const atlasTexture = fontAtlasRef.current
      
      // Load atlas image data
      const atlasImage = atlasTexture.image
      if (!atlasImage || !atlasImage.complete) return

      atlasCanvas.width = atlasImage.width
      atlasCanvas.height = atlasImage.height
      const atlasCtx = atlasCanvas.getContext('2d')
      if (!atlasCtx) return

      atlasCtx.drawImage(atlasImage, 0, 0)

      // Render each character using bitmap glyphs
      for (let row = 0; row < ROWS; row += 1) {
        const rowColor = row % 3 === 0 ? COLORS.primary : row % 3 === 1 ? COLORS.secondary : COLORS.tertiary
        
        for (let col = 0; col < COLUMNS; col += 1) {
          const char = grid[row][col]
          if (!char || char === ' ') continue

          const charCode = char.charCodeAt(0)
          
          // Calculate atlas position
          const atlasCol = charCode % ATLAS_COLS
          const atlasRow = Math.floor(charCode / ATLAS_COLS)
          const atlasX = atlasCol * ATLAS_GLYPH_WIDTH
          const atlasY = atlasRow * ATLAS_GLYPH_HEIGHT

          // Get glyph bitmap data
          const glyphData = atlasCtx.getImageData(
            atlasX,
            atlasY,
            ATLAS_GLYPH_WIDTH,
            ATLAS_GLYPH_HEIGHT
          )

          // Create colored glyph
          const coloredGlyph = ctx.createImageData(ATLAS_GLYPH_WIDTH, ATLAS_GLYPH_HEIGHT)
          const rgb = hexToRgb(rowColor)

          for (let i = 0; i < glyphData.data.length; i += 4) {
            const alpha = glyphData.data[i + 3]
            if (alpha > 0) {
              coloredGlyph.data[i] = rgb.r
              coloredGlyph.data[i + 1] = rgb.g
              coloredGlyph.data[i + 2] = rgb.b
              coloredGlyph.data[i + 3] = alpha
            }
          }

          // Draw glyph to target position
          const tempCanvas = document.createElement('canvas')
          tempCanvas.width = ATLAS_GLYPH_WIDTH
          tempCanvas.height = ATLAS_GLYPH_HEIGHT
          const tempCtx = tempCanvas.getContext('2d')
          if (tempCtx) {
            tempCtx.putImageData(coloredGlyph, 0, 0)
            ctx.drawImage(
              tempCanvas,
              col * charWidth,
              row * charHeight
            )
          }
        }
      }

      texture.needsUpdate = true
    }

    draw()
  }, [content, charHeight, charWidth, resolution, texture])

  useFrame((state) => {
    if (!materialRef.current) return

    const now = state.clock.elapsedTime
    const deltaTime = lastFrameTime.current ? now - lastFrameTime.current : 0.016
    lastFrameTime.current = now

    // Update uniforms
    materialRef.current.uniforms.uTime.value = now
    materialRef.current.uniforms.uDeltaTime.value = deltaTime
  }, 1) // Priority 1 - update uniforms first

  // Capture rendered frame for phosphor trails (runs after render)
  useFrame((state) => {
    if (!materialRef.current || !prevFrameTarget.current) return
    
    const gl = state.gl
    
    // Copy the current framebuffer to our previous frame texture
    // This captures the RENDERED output including all shader effects
    gl.copyFramebufferToTexture(
      new THREE.Vector2(0, 0),
      prevFrameTarget.current.texture,
      0
    )
    
    // Update the uniform so next frame can use it
    materialRef.current.uniforms.uPrevFrame.value = prevFrameTarget.current.texture
  }, 2) // Priority 2 - capture after rendering

  // Default effect configuration
  const config = {
    enableChromatic: true,
    enableBloom: true,
    enablePhosphor: true,
    enableNoise: true,
    enableFlicker: true,
    chromaticAmount: 0.001,
    bloomStrength: 0.45,
    phosphorDecay: 0.88,
    noiseAmount: 0.04,
    flickerAmount: 0.012,
    ...effectsConfig,
  }

  return (
    <mesh scale={[viewport.width, viewport.height, 1]}>
      <planeGeometry args={[1, 1]} />
      <shaderMaterial
        ref={materialRef}
        uniforms={{
          uTexture: { value: texture },
          uPrevFrame: { value: null },
          uResolution: { value: resolution },
          uTime: { value: 0 },
          uDeltaTime: { value: 0.016 },
          uCurvature: { value: 0.08 },
          
          // Effect toggles
          uEnableChromatic: { value: config.enableChromatic },
          uEnableBloom: { value: config.enableBloom },
          uEnablePhosphor: { value: config.enablePhosphor },
          uEnableNoise: { value: config.enableNoise },
          uEnableFlicker: { value: config.enableFlicker },
          
          // Effect parameters
          uChromaticAmount: { value: config.chromaticAmount },
          uBloomStrength: { value: config.bloomStrength },
          uPhosphorDecay: { value: config.phosphorDecay },
          uNoiseAmount: { value: config.noiseAmount },
          uFlickerAmount: { value: config.flickerAmount },
        }}
        vertexShader={VERTEX_SHADER}
        fragmentShader={FRAGMENT_SHADER}
      />
    </mesh>
  )
}

const hexToRgb = (hex) => {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  return result
    ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16),
      }
    : { r: 255, g: 255, b: 255 }
}

const FpsMonitor = ({ onSample }) => {
  const frames = useRef(0)
  const lastTime = useRef(0)

  useFrame((state) => {
    frames.current += 1
    const now = state.clock.elapsedTime
    if (lastTime.current === 0) {
      lastTime.current = now
      return
    }
    const delta = now - lastTime.current
    if (delta >= 1) {
      const fps = Math.round(frames.current / delta)
      onSample?.(fps)
      frames.current = 0
      lastTime.current = now
    }
  })

  return null
}

TeletextPlane.propTypes = {
  content: PropTypes.arrayOf(PropTypes.arrayOf(PropTypes.string)),
  effectsConfig: PropTypes.shape({
    enableChromatic: PropTypes.bool,
    enableBloom: PropTypes.bool,
    enablePhosphor: PropTypes.bool,
    enableNoise: PropTypes.bool,
    enableFlicker: PropTypes.bool,
    chromaticAmount: PropTypes.number,
    bloomStrength: PropTypes.number,
    phosphorDecay: PropTypes.number,
    noiseAmount: PropTypes.number,
    flickerAmount: PropTypes.number,
  }),
}

FpsMonitor.propTypes = {
  onSample: PropTypes.func,
}

const TeletextGrid = ({ content, showFps = false, effectsConfig }) => {
  const [fps, setFps] = useState(null)

  return (
    <div
      data-testid="teletext-grid"
      data-cols={COLUMNS}
      data-rows={ROWS}
      style={{
        width: '100%',
        height: '100%',
        background: COLORS.background,
        position: 'relative',
      }}
    >
      {showFps && fps !== null ? (
        <div className="teletext-fps">FPS {fps}</div>
      ) : null}
      <Canvas
        frameloop="always"
        orthographic
        dpr={[1, 1.5]}
        gl={{ antialias: true, powerPreference: 'high-performance' }}
        camera={{ position: [0, 0, 10], zoom: 1 }}
      >
        <OrthographicCamera makeDefault position={[0, 0, 10]} zoom={1} />
        <TeletextPlane content={content} effectsConfig={effectsConfig} />
        {showFps ? <FpsMonitor onSample={setFps} /> : null}
      </Canvas>
    </div>
  )
}

TeletextGrid.propTypes = {
  content: PropTypes.arrayOf(PropTypes.arrayOf(PropTypes.string)),
  showFps: PropTypes.bool,
  effectsConfig: PropTypes.shape({
    enableChromatic: PropTypes.bool,
    enableBloom: PropTypes.bool,
    enablePhosphor: PropTypes.bool,
    enableNoise: PropTypes.bool,
    enableFlicker: PropTypes.bool,
    chromaticAmount: PropTypes.number,
    bloomStrength: PropTypes.number,
    phosphorDecay: PropTypes.number,
    noiseAmount: PropTypes.number,
    flickerAmount: PropTypes.number,
  }),
}

export default TeletextGrid
export { COLUMNS, ROWS }
