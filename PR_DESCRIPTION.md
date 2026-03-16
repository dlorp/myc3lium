What:
- Add a teletext grid renderer component with CRT shader effects, optional FPS readout, and orthographic projection
- Replace the demo app with a teletext showcase using VT323 styling and an amber palette
- Add a TeletextGrid component test under Vitest

Why:
- Provide a BBC Micro/Ceefax-style 40x25 grid renderer for teletext content
- Establish a polished demo scene that matches the product visual direction
- Enable quick validation of rendering performance via an on-screen FPS meter

How:
- Render teletext characters to a canvas texture and feed it into a custom shader material
- Apply scanlines, phosphor glow, vignette, and curvature in the fragment shader
- Normalize content to 40x25 and wire the component into the demo app with FPS sampling
