import { useEffect, useRef, useState, useCallback } from 'react'
import PropTypes from 'prop-types'

const COLUMNS = 80
const ROWS = 25

const COLORS = {
  background: '#0E0B02',
  primary: '#FFB800',
  secondary: '#E88A00',
  tertiary: '#C47A00',
  dim: '#7A5800',
  dimmer: '#3D2C00',
  green: '#7EC850',
  red: '#E05030',
  white: '#EED888',
  cyan: '#50C8D8',
}

// ─── CRT post-process shader (matches mockup) ───────────────────────────────
// Security: Shaders are static - never interpolate user input
const CRT_VERT = `
  attribute vec2 aPos;
  varying vec2 vUv;
  void main() {
    vUv = aPos * 0.5 + 0.5;
    vUv.y = 1.0 - vUv.y;  // Flip Y to match Canvas2D texture orientation
    gl_Position = vec4(aPos, 0.0, 1.0);
  }
`

// Security: Shaders are static - never interpolate user input
const CRT_FRAG = `
  precision mediump float;
  uniform sampler2D tD;
  uniform float uT;
  uniform vec2 uR;
  varying vec2 vUv;

  float rr(vec2 c) {
    return fract(sin(dot(c, vec2(127.1, 311.7))) * 43758.5453);
  }

  void main() {
    vec2 uv = vUv;
    vec2 d = uv - 0.5;

    // Subtle barrel distortion (CRT curvature) - 0.045 controls curvature strength
    d *= 1.0 + dot(d, d) * 0.045;
    uv = d + 0.5;

    // Out-of-bounds → black
    if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) {
      gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);
      return;
    }

    // Chromatic aberration
    float ca = 0.0006;
    vec4 c;
    c.r = texture2D(tD, uv + vec2(ca, 0.0)).r;
    c.g = texture2D(tD, uv).g;
    c.b = texture2D(tD, uv - vec2(ca, 0.0)).b;
    c.a = 1.0;

    // Scanline - 0.98/0.02 controls scanline intensity (98% base + 2% oscillation)
    c.rgb *= 0.98 + 0.02 * sin(uv.y * uR.y * 1.4 + uT * 0.35);

    // Horizontal sweep
    c.rgb += smoothstep(0.08, 0.0, abs(fract(uv.y - uT * 0.065) - 0.5)) * 0.028;

    // Amber color grading
    c.rgb *= vec3(1.05, 0.80, 0.24);

    // Vignette
    c.rgb *= max(1.0 - dot(d * 0.9, d * 0.9), 0.0);

    // Film grain
    c.rgb += (rr(uv + uT * 0.006) - 0.5) * 0.014;

    gl_FragColor = c;
  }
`

/**
 * Normalize content to ROWS × COLUMNS grid of single characters.
 * Security: validates depth, filters control chars, limits string conversion.
 */
const normalizeContent = (content) => {
  const MAX_DEPTH = 3
  const MAX_STRING_LENGTH = 200
  
  // Validate max depth to prevent DoS
  const checkDepth = (obj, depth = 0) => {
    if (depth > MAX_DEPTH) return false
    if (Array.isArray(obj)) {
      return obj.every(item => checkDepth(item, depth + 1))
    }
    return true
  }
  
  if (!checkDepth(content)) {
    console.warn('TeletextGrid: content exceeds max depth, rejecting')
    return Array.from({ length: ROWS }, () => Array(COLUMNS).fill(' '))
  }
  
  const safeContent = Array.isArray(content) ? content : []
  return Array.from({ length: ROWS }, (_, rowIndex) => {
    const row = safeContent[rowIndex] ?? []
    const chars = Array.isArray(row) 
      ? row 
      : String(row).slice(0, MAX_STRING_LENGTH).split('')
    
    const normalized = chars.slice(0, COLUMNS).map(char => {
      const str = String(char).slice(0, 1)
      const code = str.charCodeAt(0)
      // Filter control characters (codes < 32 except space)
      if (code < 32 && code !== 32) return ' '
      return str
    })
    
    while (normalized.length < COLUMNS) normalized.push(' ')
    return normalized
  })
}

/**
 * Try to create a WebGL CRT post-process pipeline.
 * Returns { gl, program, tex, uT, uR } or null on failure.
 */
const initCRT = (outputCanvas, width, height) => {
  let gl
  try {
    gl = outputCanvas.getContext('webgl', { antialias: false, alpha: false })
  } catch {
    return null
  }
  if (!gl || typeof gl.createShader !== 'function') return null

  const compile = (type, src) => {
    const s = gl.createShader(type)
    gl.shaderSource(s, src)
    gl.compileShader(s)
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
      console.warn('CRT shader compile failed:', gl.getShaderInfoLog(s))
      gl.deleteShader(s)
      return null
    }
    return s
  }

  const vs = compile(gl.VERTEX_SHADER, CRT_VERT)
  const fs = compile(gl.FRAGMENT_SHADER, CRT_FRAG)
  if (!vs || !fs) return null

  const prog = gl.createProgram()
  gl.attachShader(prog, vs)
  gl.attachShader(prog, fs)
  gl.linkProgram(prog)
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) {
    console.warn('CRT program link failed:', gl.getProgramInfoLog(prog))
    return null
  }

  gl.useProgram(prog)

  // Full-screen quad
  const buf = gl.createBuffer()
  gl.bindBuffer(gl.ARRAY_BUFFER, buf)
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 1,-1, -1,1, 1,1]), gl.STATIC_DRAW)
  const aPos = gl.getAttribLocation(prog, 'aPos')
  gl.enableVertexAttribArray(aPos)
  gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0)

  // Texture
  const tex = gl.createTexture()
  gl.bindTexture(gl.TEXTURE_2D, tex)
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR)
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR)
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE)
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE)

  const uT = gl.getUniformLocation(prog, 'uT')
  const uR = gl.getUniformLocation(prog, 'uR')
  const tD = gl.getUniformLocation(prog, 'tD')
  gl.uniform1i(tD, 0)
  gl.uniform2f(uR, width, height)

  return { gl, program: prog, tex, uT, uR }
}

/**
 * TeletextGrid – Canvas2D text renderer with optional CRT shader post-process.
 *
 * Architecture (matches the working HTML mockup):
 *   1. Off-screen canvas renders text via Canvas2D fillText (fast, reliable)
 *   2. WebGL shader applies CRT effects (curvature, scanlines, chromatic aberration)
 *   3. Falls back to CSS filter if WebGL unavailable (Pi safety net)
 */
const TeletextGrid = ({ content, showFps = false, onTextureError }) => {
  const containerRef = useRef(null)
  const outputCanvasRef = useRef(null)
  const bufferCanvasRef = useRef(null)
  const crtRef = useRef(null)
  const rafRef = useRef(null)
  const fpsRef = useRef({ frames: 0, lastTime: 0, value: 0 })
  const [fps, setFps] = useState(null)
  const [crtActive, setCrtActive] = useState(false)
  const [resizeKey, setResizeKey] = useState(0)
  const contentRef = useRef(content)
  const lastContentRef = useRef(null)
  const needsRedrawRef = useRef(true)
  contentRef.current = content

  // Trigger redraw when content prop changes
  useEffect(() => {
    needsRedrawRef.current = true
  }, [content])

  // Determine canvas dimensions
  const getSize = useCallback(() => {
    const el = containerRef.current
    if (!el) return { w: 640, h: 400 }
    const w = Math.max(480, Math.min(960, el.offsetWidth || 640))
    const h = Math.round(w * 0.52)
    return { w, h }
  }, [])

  // Draw text content to the off-screen buffer canvas
  // Note: Not using useCallback because it's only used within the useEffect below,
  // and we want it to always use the latest contentRef.current value
  const drawContent = (ctx, w, h) => {
    const grid = normalizeContent(contentRef.current)
    const F = Math.max(11, Math.round(w / 58))

    ctx.fillStyle = COLORS.background
    ctx.fillRect(0, 0, w, h)
    ctx.font = `${F}px 'Courier New', monospace`
    ctx.textBaseline = 'top'

    const lineHeight = F + 2
    const padX = 8
    const padY = 6

    for (let row = 0; row < ROWS; row++) {
      // Cycle through amber palette per row (like mockup)
      const rowColors = [COLORS.primary, COLORS.secondary, COLORS.tertiary]
      const color = rowColors[row % 3]

      let lineStr = ''
      for (let col = 0; col < COLUMNS; col++) {
        lineStr += grid[row][col]
      }

      // Skip completely empty lines
      const trimmed = lineStr.trim()
      if (!trimmed) continue

      ctx.fillStyle = color
      ctx.fillText(lineStr, padX, padY + row * lineHeight)
    }
  }

  // Initialize and run the render loop
  useEffect(() => {
    const { w, h } = getSize()

    // Create off-screen buffer
    const bufCanvas = document.createElement('canvas')
    bufCanvas.width = w
    bufCanvas.height = h
    bufferCanvasRef.current = bufCanvas
    const bufCtx = bufCanvas.getContext('2d')

    // Set up output canvas
    const outCanvas = outputCanvasRef.current
    if (!outCanvas) return
    outCanvas.width = w
    outCanvas.height = h

    // Try WebGL CRT
    const crt = initCRT(outCanvas, w, h)
    crtRef.current = crt
    setCrtActive(!!crt)

    if (!crt) {
      // Fallback: CSS-based CRT effects
      outCanvas.style.filter = 'contrast(1.1) brightness(0.95)'
      console.info('TeletextGrid: WebGL unavailable, using CSS fallback')
      if (onTextureError) {
        onTextureError(new Error('WebGL not available, using CSS fallback'))
      }
    }

    // Handle container resize
    const resizeObserver = new ResizeObserver(() => {
      const newSize = getSize()
      if (newSize.w !== w || newSize.h !== h) {
        // Force re-initialization by incrementing resizeKey
        setResizeKey(k => k + 1)
      }
    })

    if (containerRef.current) {
      resizeObserver.observe(containerRef.current)
    }

    // Animation loop
    const loop = (t) => {
      rafRef.current = requestAnimationFrame(loop)

      // Check if content has changed
      const contentStr = JSON.stringify(contentRef.current)
      if (contentStr !== lastContentRef.current) {
        lastContentRef.current = contentStr
        needsRedrawRef.current = true
      }

      // Only redraw content when it changes
      if (needsRedrawRef.current) {
        drawContent(bufCtx, w, h)
        needsRedrawRef.current = false
      }

      if (crt) {
        // Upload buffer to WebGL texture and render with CRT shader (runs every frame for animations)
        const { gl, tex, uT } = crt
        gl.bindTexture(gl.TEXTURE_2D, tex)
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, bufCanvas)
        gl.uniform1f(uT, t * 0.001)
        gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4)
      } else {
        // Direct Canvas2D copy (fallback)
        const ctx2d = outCanvas.getContext('2d')
        if (ctx2d) {
          ctx2d.clearRect(0, 0, w, h)
          ctx2d.drawImage(bufCanvas, 0, 0)
        }
      }

      // FPS counter
      if (showFps) {
        fpsRef.current.frames++
        if (t - fpsRef.current.lastTime >= 1000) {
          fpsRef.current.value = fpsRef.current.frames
          fpsRef.current.frames = 0
          fpsRef.current.lastTime = t
          setFps(fpsRef.current.value)
        }
      }
    }

    rafRef.current = requestAnimationFrame(loop)

    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
      resizeObserver.disconnect()
      
      // Clean up WebGL resources
      if (crt) {
        const { gl, tex, program } = crt
        if (tex) gl.deleteTexture(tex)
        if (program) gl.deleteProgram(program)
        // Optional: force context loss for complete cleanup
        const loseCtx = gl.getExtension('WEBGL_lose_context')
        if (loseCtx) loseCtx.loseContext()
      }
    }
  }, [getSize, showFps, onTextureError, resizeKey])

  return (
    <div
      key={resizeKey}
      ref={containerRef}
      data-testid="teletext-grid"
      data-cols={COLUMNS}
      data-rows={ROWS}
      style={{
        width: '100%',
        height: '100%',
        background: COLORS.background,
        position: 'relative',
        lineHeight: 0,
      }}
    >
      <canvas
        ref={outputCanvasRef}
        style={{
          display: 'block',
          width: '100%',
          height: 'auto',
        }}
      />
      {showFps && fps !== null && (
        <div
          style={{
            position: 'absolute',
            top: '8px',
            right: '8px',
            background: 'rgba(6, 4, 0, 0.85)',
            color: COLORS.secondary,
            fontFamily: "'Courier New', monospace",
            fontSize: '11px',
            padding: '4px 8px',
            border: `1px solid ${COLORS.tertiary}`,
            borderRadius: '2px',
            pointerEvents: 'none',
          }}
        >
          FPS {fps}
        </div>
      )}
    </div>
  )
}

TeletextGrid.propTypes = {
  content: PropTypes.arrayOf(PropTypes.arrayOf(PropTypes.string)),
  showFps: PropTypes.bool,
  onTextureError: PropTypes.func,
}

export default TeletextGrid
export { COLUMNS, ROWS }
