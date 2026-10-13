# Bedroom layout

A CAD model of the room and its final furniture layout, plus a 3D viewer.

- **`viewer/`**: the web page (GitHub Pages). It shows the room in 3D: orbit and zoom, click an object to see its size, and measure between any two points. The floor plan and the measured plan sit underneath.
- **`concepts/concept_D.step`**: the room with all the furniture. Open it in Fusion. The `room_walls_*` parts are walls you can measure to; hide them when you don't need them.
- **`concepts/concept_D.png`**: floor plan and 3D view.
- **`concepts/concept_D_dimensions.png`**: plan with the wall lengths, the door and window positions, and the gaps between items.
- **`concepts/build_concepts.py`**: the script that builds everything above. Positions are plain numbers in `concept_D()`.
- **`Room layout.step`**: the original room model (doors, window, radiator, TV). The script builds on top of it.

## Rebuild

```
pip install cadquery matplotlib
python concepts/build_concepts.py
```

This regenerates the STEP, PNG and GLB files and refreshes `viewer/`.

## Publishing the viewer

`.github/workflows/pages.yml` publishes `viewer/` on every push to `main`. Turn it on under **Settings → Pages → Source: GitHub Actions**.

All sizes are in mm. Assumed: walls 100 mm thick, ceiling 2400 mm, BERGSHULT shelf tops at 1500 mm.
