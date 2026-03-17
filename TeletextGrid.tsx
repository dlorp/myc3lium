/**
 * TeletextGrid Component
 * 
 * Three.js-based teletext renderer using IBM VGA 8×16 bitmap font atlas.
 * Renders 80×25 character grid with CRT shader effects.
 * 
 * Usage:
 *   <TeletextGrid content={pageData} />
 */

import { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface TeletextGridProps {
  content: string[][]; // 25 rows × 80 columns
  width?: number;
  height?: number;
}

const CHAR_WIDTH = 8;
const CHAR_HEIGHT = 16;
const GRID_COLS = 80;
const GRID_ROWS = 25;
const ATLAS_SIZE = 128;

export const TeletextGrid: React.FC<TeletextGridProps> = ({
  content,
  width = 640,
  height = 400
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.OrthographicCamera | null>(null);
  const fontAtlasRef = useRef<THREE.Texture | null>(null);
  const meshRef = useRef<THREE.Mesh | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Scene setup
    const scene = new THREE.Scene();
    sceneRef.current = scene;

    // Orthographic camera for 2D grid
    const camera = new THREE.OrthographicCamera(
      0, GRID_COLS * CHAR_WIDTH,
      0, GRID_ROWS * CHAR_HEIGHT,
      0.1, 1000
    );
    camera.position.z = 1;
    cameraRef.current = camera;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: false });
    renderer.setSize(width, height);
    renderer.setClearColor(0x0B0F14); // Deep black background
    containerRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Load font atlas texture
    const textureLoader = new THREE.TextureLoader();
    textureLoader.load('/assets/ibm-vga-8x16.png', (texture) => {
      texture.magFilter = THREE.NearestFilter; // Pixel-perfect rendering
      texture.minFilter = THREE.NearestFilter;
      fontAtlasRef.current = texture;

      // Create grid geometry and material
      const geometry = createGridGeometry();
      const material = createGridMaterial(texture);
      const mesh = new THREE.Mesh(geometry, material);
      scene.add(mesh);
      meshRef.current = mesh;

      // Initial render
      updateGridContent(content, geometry);
      renderer.render(scene, camera);
    });

    // Animation loop (for future CRT effects)
    const animate = () => {
      requestAnimationFrame(animate);
      if (sceneRef.current && cameraRef.current) {
        renderer.render(sceneRef.current, cameraRef.current);
      }
    };
    animate();

    // Cleanup
    return () => {
      if (rendererRef.current) {
        containerRef.current?.removeChild(rendererRef.current.domElement);
        rendererRef.current.dispose();
      }
    };
  }, [width, height]);

  // Update content when it changes
  useEffect(() => {
    if (meshRef.current) {
      const geometry = meshRef.current.geometry as THREE.BufferGeometry;
      updateGridContent(content, geometry);
    }
  }, [content]);

  return <div ref={containerRef} />;
};

/**
 * Create geometry for character grid (80×25 quads)
 */
function createGridGeometry(): THREE.BufferGeometry {
  const geometry = new THREE.BufferGeometry();
  const totalChars = GRID_COLS * GRID_ROWS;
  
  // Each character is 2 triangles (6 vertices)
  const positions = new Float32Array(totalChars * 6 * 3);
  const uvs = new Float32Array(totalChars * 6 * 2);

  let posIdx = 0;
  let uvIdx = 0;

  for (let row = 0; row < GRID_ROWS; row++) {
    for (let col = 0; col < GRID_COLS; col++) {
      const x = col * CHAR_WIDTH;
      const y = (GRID_ROWS - row - 1) * CHAR_HEIGHT; // Flip Y

      // Quad vertices (2 triangles)
      // Triangle 1
      positions[posIdx++] = x;
      positions[posIdx++] = y;
      positions[posIdx++] = 0;

      positions[posIdx++] = x + CHAR_WIDTH;
      positions[posIdx++] = y;
      positions[posIdx++] = 0;

      positions[posIdx++] = x;
      positions[posIdx++] = y + CHAR_HEIGHT;
      positions[posIdx++] = 0;

      // Triangle 2
      positions[posIdx++] = x;
      positions[posIdx++] = y + CHAR_HEIGHT;
      positions[posIdx++] = 0;

      positions[posIdx++] = x + CHAR_WIDTH;
      positions[posIdx++] = y;
      positions[posIdx++] = 0;

      positions[posIdx++] = x + CHAR_WIDTH;
      positions[posIdx++] = y + CHAR_HEIGHT;
      positions[posIdx++] = 0;

      // Initial UV coordinates (space character = 0x20)
      const charCode = 0x20;
      const u = (charCode % 16) * CHAR_WIDTH / ATLAS_SIZE;
      const v = Math.floor(charCode / 16) * CHAR_HEIGHT / ATLAS_SIZE;
      const uWidth = CHAR_WIDTH / ATLAS_SIZE;
      const vHeight = CHAR_HEIGHT / ATLAS_SIZE;

      // Triangle 1
      uvs[uvIdx++] = u;
      uvs[uvIdx++] = v;

      uvs[uvIdx++] = u + uWidth;
      uvs[uvIdx++] = v;

      uvs[uvIdx++] = u;
      uvs[uvIdx++] = v + vHeight;

      // Triangle 2
      uvs[uvIdx++] = u;
      uvs[uvIdx++] = v + vHeight;

      uvs[uvIdx++] = u + uWidth;
      uvs[uvIdx++] = v;

      uvs[uvIdx++] = u + uWidth;
      uvs[uvIdx++] = v + vHeight;
    }
  }

  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute('uv', new THREE.BufferAttribute(uvs, 2));

  return geometry;
}

/**
 * Create shader material with font atlas texture
 */
function createGridMaterial(fontAtlas: THREE.Texture): THREE.ShaderMaterial {
  return new THREE.ShaderMaterial({
    uniforms: {
      fontAtlas: { value: fontAtlas },
      time: { value: 0 }
    },
    vertexShader: `
      varying vec2 vUv;
      
      void main() {
        vUv = uv;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `,
    fragmentShader: `
      uniform sampler2D fontAtlas;
      uniform float time;
      varying vec2 vUv;
      
      void main() {
        vec4 texColor = texture2D(fontAtlas, vUv);
        
        // Teletext color: signal green
        vec3 teletextColor = vec3(0.64, 0.85, 0.79); // #A3D9C9
        
        // Apply color to white font atlas
        vec3 finalColor = texColor.rgb * teletextColor;
        
        gl_FragColor = vec4(finalColor, texColor.a);
      }
    `,
    transparent: true
  });
}

/**
 * Update grid UV coordinates based on content
 */
function updateGridContent(content: string[][], geometry: THREE.BufferGeometry) {
  const uvAttribute = geometry.getAttribute('uv') as THREE.BufferAttribute;
  const uvs = uvAttribute.array as Float32Array;

  let uvIdx = 0;

  for (let row = 0; row < GRID_ROWS; row++) {
    for (let col = 0; col < GRID_COLS; col++) {
      // Get character code from content (default to space)
      let charCode = 0x20;
      if (content[row] && content[row][col]) {
        charCode = content[row][col].charCodeAt(0);
      }

      // Calculate UV coordinates for this character
      const u = (charCode % 16) * CHAR_WIDTH / ATLAS_SIZE;
      const v = Math.floor(charCode / 16) * CHAR_HEIGHT / ATLAS_SIZE;
      const uWidth = CHAR_WIDTH / ATLAS_SIZE;
      const vHeight = CHAR_HEIGHT / ATLAS_SIZE;

      // Triangle 1
      uvs[uvIdx++] = u;
      uvs[uvIdx++] = v;

      uvs[uvIdx++] = u + uWidth;
      uvs[uvIdx++] = v;

      uvs[uvIdx++] = u;
      uvs[uvIdx++] = v + vHeight;

      // Triangle 2
      uvs[uvIdx++] = u;
      uvs[uvIdx++] = v + vHeight;

      uvs[uvIdx++] = u + uWidth;
      uvs[uvIdx++] = v;

      uvs[uvIdx++] = u + uWidth;
      uvs[uvIdx++] = v + vHeight;
    }
  }

  uvAttribute.needsUpdate = true;
}
