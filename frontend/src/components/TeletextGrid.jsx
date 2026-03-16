import { useEffect, useMemo, useRef, useState } from 'react'
import PropTypes from 'prop-types'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { OrthographicCamera } from '@react-three/drei'
import * as THREE from 'three'

const COLUMNS = 40
const ROWS = 25

const COLORS = {
  background: '#0E0B02',
  primary: '#FFB800',
  secondary: '#E88A00',
  tertiary: '#C47A00',
}

const VERTEX_SHADER = `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`

const FRAGMENT_SHADER = `
  uniform sampler2D uTexture;
  uniform vec2 uResolution;
  uniform float uTime;
  uniform float uCurvature;
  varying vec2 vUv;

  vec2 distort(vec2 uv) {
    vec2 centered = uv * 2.0 - 1.0;
    float r2 = dot(centered, centered);
    centered *= 1.0 + uCurvature * r2;
    return centered * 0.5 + 0.5;
  }

  void main() {
    vec2 uv = distort(vUv);
    if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) {
      gl_FragColor = vec4(0.055, 0.043, 0.008, 1.0);
      return;
    }

    vec3 tex = texture2D(uTexture, uv).rgb;
    vec2 texel = 1.0 / uResolution;

    vec3 glow = texture2D(uTexture, uv + vec2(texel.x, 0.0)).rgb;
    glow += texture2D(uTexture, uv - vec2(texel.x, 0.0)).rgb;
    glow += texture2D(uTexture, uv + vec2(0.0, texel.y)).rgb;
    glow += texture2D(uTexture, uv - vec2(0.0, texel.y)).rgb;
    glow *= 0.25;

    float scan = sin((uv.y * uResolution.y + uTime * 20.0) * 3.14159);
    float scanline = mix(0.82, 1.0, scan * 0.5 + 0.5);
    float vignette = smoothstep(0.8, 0.2, length(vUv - 0.5));

    vec3 color = tex + glow * 0.35;
    color *= scanline;
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

const TeletextPlane = ({ content }) => {
  const { viewport } = useThree()
  const canvasRef = useRef(document.createElement('canvas'))
  const materialRef = useRef(null)

  const { texture, resolution, fontSize, charWidth, charHeight } = useMemo(() => {
    const fontSizeValue = 24
    const charWidthValue = Math.ceil(fontSizeValue * 0.62)
    const charHeightValue = Math.ceil(fontSizeValue * 1.18)
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
      fontSize: fontSizeValue,
      charWidth: charWidthValue,
      charHeight: charHeightValue,
    }
  }, [])

  useEffect(() => {
    let active = true
    const draw = async () => {
      if (document.fonts?.load) {
        try {
          await document.fonts.load(`${fontSize}px "VT323"`)
        } catch (error) {
          // Ignore font loading errors and draw with fallback fonts.
        }
      }

      if (!active) return

      const grid = normalizeContent(content)
      const canvas = canvasRef.current
      const ctx = canvas.getContext('2d')
      if (!ctx) return

      ctx.fillStyle = COLORS.background
      ctx.fillRect(0, 0, canvas.width, canvas.height)
      ctx.font = `${fontSize}px "VT323", monospace`
      ctx.textBaseline = 'top'

      for (let row = 0; row < ROWS; row += 1) {
        const rowColor = row % 3 === 0 ? COLORS.primary : row % 3 === 1 ? COLORS.secondary : COLORS.tertiary
        ctx.fillStyle = rowColor
        for (let col = 0; col < COLUMNS; col += 1) {
          const char = grid[row][col]
          if (char && char !== ' ') {
            ctx.fillText(char, col * charWidth, row * charHeight)
          }
        }
      }

      texture.needsUpdate = true
      if (materialRef.current) {
        materialRef.current.uniforms.uResolution.value = resolution
      }
    }

    draw()

    return () => {
      active = false
    }
  }, [content, fontSize, charHeight, charWidth, resolution, texture])

  useFrame((state) => {
    if (materialRef.current) {
      materialRef.current.uniforms.uTime.value = state.clock.elapsedTime
    }
  })

  return (
    <mesh scale={[viewport.width, viewport.height, 1]}>
      <planeGeometry args={[1, 1]} />
      <shaderMaterial
        ref={materialRef}
        uniforms={{
          uTexture: { value: texture },
          uResolution: { value: resolution },
          uTime: { value: 0 },
          uCurvature: { value: 0.08 },
        }}
        vertexShader={VERTEX_SHADER}
        fragmentShader={FRAGMENT_SHADER}
      />
    </mesh>
  )
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
}

FpsMonitor.propTypes = {
  onSample: PropTypes.func,
}

const TeletextGrid = ({ content, showFps = false }) => {
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
        <TeletextPlane content={content} />
        {showFps ? <FpsMonitor onSample={setFps} /> : null}
      </Canvas>
    </div>
  )
}

TeletextGrid.propTypes = {
  content: PropTypes.arrayOf(PropTypes.arrayOf(PropTypes.string)),
  showFps: PropTypes.bool,
}

export default TeletextGrid
export { COLUMNS, ROWS }
