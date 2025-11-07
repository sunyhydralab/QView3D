import * as GCodePreview from 'gcode-preview';

/**
 * Composable for shared GCode viewer functionality
 * Provides consistent configuration and processing methods across all GCode viewer components
 */
export function useGCodeViewer() {
  /**
   * Default configuration for all GCode viewers
   * Ensures consistency across different viewer implementations
   */
  const defaultConfig = {
    extrusionColor: 'turquoise',
    backgroundColor: 'black',
    // Critical: Always define buildVolume to prevent floating models
    buildVolume: { x: 250, y: 210, z: 220 },
    travelColor: 'limegreen',
    lineWidth: 0.4,          // Realistic nozzle diameter (0.4mm)
    lineHeight: 0.2,         // Realistic layer height (0.2mm)
    extrusionWidth: 0.4,     // Realistic extrusion width (0.4mm)
    renderExtrusion: true,
    renderTravel: true,
    renderTubes: true,       // Keep tubes for better visual appearance
    // Add layer threshold to handle minor Z variations
    minLayerThreshold: 0.05, // Ignore Z changes smaller than 0.05mm
    // Set consistent initial camera position
    initialCameraPosition: [-200, 232, 200]
  };

  /**
   * Preprocess GCode to fix Z-axis offset issues
   * This ensures the model sits on the bed instead of floating
   * @param gcode - Raw GCode string
   * @returns GCode string with corrected Z values
   */
  function preprocessGCodeForZOffset(gcode: string): string {
    const lines = gcode.split('\n');
    let minZ = Infinity;

    // First pass: find the minimum Z value in the entire file
    lines.forEach((line: string) => {
      const zMatch = line.match(/Z(-?\d*\.?\d+)/);
      if (zMatch) {
        const zValue = parseFloat(zMatch[1]);
        if (!isNaN(zValue) && zValue < minZ) {
          minZ = zValue;
        }
      }
    });

    // If we found a minimum Z value and it's positive, adjust all Z values
    if (minZ !== Infinity && minZ > 0) {
      console.log(`[GCode Viewer] Adjusting Z-axis offset: shifting all Z values down by ${minZ}mm`);

      return lines.map(line => {
        // Only adjust lines with Z values
        const zMatch = line.match(/Z(-?\d*\.?\d+)/);
        if (zMatch) {
          const originalZ = parseFloat(zMatch[1]);
          const adjustedZ = (originalZ - minZ).toFixed(3);
          return line.replace(/Z(-?\d*\.?\d+)/, `Z${adjustedZ}`);
        }
        return line;
      }).join('\n');
    }

    return gcode; // Return original if no adjustment needed
  }

  /**
   * Extract layers from GCode for progressive rendering
   * Detects common layer change markers used by different slicers
   * @param gcode - GCode string to analyze
   * @returns Array of layer arrays containing GCode lines
   */
  function extractLayers(gcode: string): string[][] {
    const lines = gcode.split('\n');
    const layers: string[][] = [];
    let currentLayer: string[] = [];

    lines.forEach(line => {
      // Check for common layer change indicators
      if (line.includes(';LAYER_CHANGE') ||
          line.includes(';LAYER:') ||
          line.includes(';Z:')) {
        if (currentLayer.length > 0) {
          layers.push(currentLayer);
          currentLayer = [];
        }
      }
      currentLayer.push(line);
    });

    // Don't forget the last layer
    if (currentLayer.length > 0) {
      layers.push(currentLayer);
    }

    // If no layers detected, treat entire file as one layer
    if (layers.length === 0 && lines.length > 0) {
      layers.push(lines);
    }

    return layers;
  }

  /**
   * Initialize a GCode preview instance with consistent configuration
   * @param canvas - HTML canvas element for rendering
   * @param customConfig - Optional configuration overrides
   * @returns Initialized GCodePreview instance
   */
  function initPreview(
    canvas: HTMLCanvasElement,
    customConfig?: Partial<typeof defaultConfig>
  ): ReturnType<typeof GCodePreview.init> | null {
    try {
      // Ensure canvas has dimensions
      const canvasWidth = canvas.clientWidth || 800;
      const canvasHeight = canvas.clientHeight || 600;
      canvas.width = canvasWidth;
      canvas.height = canvasHeight;

      console.log(`[GCode Viewer] Initializing with canvas dimensions: ${canvasWidth}x${canvasHeight}`);

      const config = {
        canvas,
        ...defaultConfig,
        ...customConfig
      };

      const preview = GCodePreview.init(config);
      console.log('[GCode Viewer] Preview initialized successfully');
      return preview;
    } catch (error) {
      console.error('[GCode Viewer] Failed to initialize preview:', error);
      return null;
    }
  }

  /**
   * Process static GCode - renders entire file at once
   * @param preview - GCodePreview instance
   * @param gcode - Raw GCode string
   * @param applyZOffset - Whether to apply Z-offset correction (default: true)
   */
  function processStaticGCode(
    preview: ReturnType<typeof GCodePreview.init>,
    gcode: string,
    applyZOffset = true
  ): void {
    if (!preview) {
      console.error('[GCode Viewer] Preview not initialized');
      return;
    }

    console.log(`[GCode Viewer] Processing static GCode with ${gcode.split('\n').length} lines`);

    try {
      preview.clear();

      // Ensure camera looks at origin (position already set via initialCameraPosition)
      if (preview.camera) {
        preview.camera.lookAt(0, 0, 0);
      }

      // Apply Z-offset correction if enabled
      const processedGCode = applyZOffset ? preprocessGCodeForZOffset(gcode) : gcode;

      // Process the entire gcode at once
      preview.processGCode(processedGCode);
      console.log('[GCode Viewer] Static rendering complete');
    } catch (error) {
      console.error('[GCode Viewer] Error rendering static GCode:', error);

      // Try fallback render without travel moves
      try {
        preview.renderTravel = false;
        preview.processGCode(gcode);
        preview.renderTravel = true;
        console.warn('[GCode Viewer] Rendered without travel moves due to error');
      } catch (fallbackError) {
        console.error('[GCode Viewer] Fallback rendering also failed:', fallbackError);
      }
    }
  }

  /**
   * Process GCode progressively - useful for large files or animations
   * @param preview - GCodePreview instance
   * @param gcode - Raw GCode string
   * @param applyZOffset - Whether to apply Z-offset correction (default: true)
   * @param layerDelay - Delay between layers in ms (default: 50)
   */
  async function processProgressiveGCode(
    preview: ReturnType<typeof GCodePreview.init>,
    gcode: string,
    applyZOffset = true,
    layerDelay = 50
  ): Promise<void> {
    if (!preview) {
      console.error('[GCode Viewer] Preview not initialized');
      return;
    }

    preview.clear();

    // Ensure camera looks at origin
    if (preview.camera) {
      preview.camera.lookAt(0, 0, 0);
    }

    // Apply Z-offset correction if enabled
    const processedGCode = applyZOffset ? preprocessGCodeForZOffset(gcode) : gcode;
    const layers = extractLayers(processedGCode);

    console.log(`[GCode Viewer] Processing ${layers.length} layers progressively`);

    // First, render a quick preview without travel moves
    preview.renderTravel = false;
    preview.processGCode(processedGCode);
    preview.renderTravel = true;
    await new Promise(resolve => setTimeout(resolve, 300));

    // Then process layer by layer for visual effect
    preview.clear();
    for (let i = 0; i < layers.length; i++) {
      const layerGcode = layers[i].join('\n');
      preview.processGCode(layerGcode);

      // Pause between layers for visual effect
      if (i % 5 === 0) {
        await new Promise(resolve => setTimeout(resolve, layerDelay));
      }
    }

    console.log('[GCode Viewer] Progressive rendering complete');
  }

  /**
   * Strip comments from GCode for cleaner processing
   * @param gcode - Raw GCode string
   * @returns GCode with comments removed
   */
  function stripGCodeComments(gcode: string): string {
    return gcode
      .split('\n')
      .map(line => {
        const commentIndex = line.indexOf(';');
        return commentIndex >= 0 ? line.substring(0, commentIndex).trim() : line.trim();
      })
      .filter(line => line.length > 0)
      .join('\n');
  }

  return {
    defaultConfig,
    preprocessGCodeForZOffset,
    extractLayers,
    initPreview,
    processStaticGCode,
    processProgressiveGCode,
    stripGCodeComments
  };
}