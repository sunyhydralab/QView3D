// gcodeRenderer.ts
import * as THREE from 'three';

interface Position {
    x: number;
    y: number;
    z: number;
    e?: number;
}

interface CenterOffset {
    i: number;
    j: number;
}

interface GCodeRendererOptions {
    extrusionColor?: number;
    travelColor?: number;
    arcSegments?: number;
    renderTravel?: boolean;
    renderExtrusion?: boolean;

}

export class GCodeRenderer {
    private container: HTMLElement;
    private scene: THREE.Scene;
    private camera: THREE.PerspectiveCamera;
    private renderer: THREE.WebGLRenderer;
    private extrusionColor: number;
    private travelColor: number;
    private arcSegments: number;

    constructor(container: HTMLElement, options: GCodeRendererOptions = {}) {
        this.container = container;
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(75, container.offsetWidth / container.offsetHeight, 0.1, 1000);
        this.renderer = new THREE.WebGLRenderer({antialias: true});
        this.extrusionColor = options.extrusionColor || 0xff0000; // Default red for extrusion
        this.travelColor = options.travelColor || 0x00ff00; // Default green for travel
        this.arcSegments = options.arcSegments || 50; // Default arc smoothness (segments per arc)

        this.renderer.setSize(container.offsetWidth, container.offsetHeight);
        container.appendChild(this.renderer.domElement);

        //this.camera.position.set(-200, 232, 200);
        this.camera.position.set(1, 0, 200);
        this.animate();
    }

    /**
     * Animate and render the scene.
     */
    private animate(): void {
        requestAnimationFrame(this.animate.bind(this));
        this.renderer.render(this.scene, this.camera);
    }

    /**
     * Clears the current scene.
     */
    public clearScene(): void {
        while (this.scene.children.length) {
            this.scene.remove(this.scene.children[0]);
        }
    }

    /**
     * Parses GCode commands and adds them to the scene.
     * @param {string[]} gcodeLines - Array of GCode lines.
     */
    public parseGCode(gcodeLines: string[]): void {
        this.clearScene();

        const travelMaterial = new THREE.LineBasicMaterial({color: this.travelColor});
        const extrusionMaterial = new THREE.LineBasicMaterial({color: this.extrusionColor});

        let currentPosition: Position = {x: 0, y: 0, z: 0, e: 0};
        let lastPosition: Position = {...currentPosition};

        const travelGeometry = new THREE.BufferGeometry();
        const extrusionGeometry = new THREE.BufferGeometry();

        const travelVertices: number[] = [];
        const extrusionVertices: number[] = [];

        gcodeLines.forEach((line) => {
            const parsed = this.parseGCodeLine(line);
            if (!parsed) return;

            const {x, y, z, i, j, e, command} = parsed;
            const isExtrusion = e !== undefined && e > (lastPosition.e || 0);

            lastPosition = {...currentPosition};
            currentPosition = {
                x: x !== undefined ? x : currentPosition.x,
                y: y !== undefined ? y : currentPosition.y,
                z: z !== undefined ? z : currentPosition.z,
                e: e !== undefined ? e : currentPosition.e,
            };

            if (command === 'G2' || command === 'G3') {
                const arcVertices = this.computeArcVertices(
                    lastPosition,
                    currentPosition,
                    {i: i || 0, j: j || 0},
                    command === 'G2' // Clockwise for G2
                );

                if (isExtrusion) {
                    extrusionVertices.push(...arcVertices);
                } else {
                    travelVertices.push(...arcVertices);
                }
            } else {
                // Straight moves (G0/G1)
                if (isExtrusion) {
                    extrusionVertices.push(lastPosition.x, lastPosition.y, lastPosition.z);
                    extrusionVertices.push(currentPosition.x, currentPosition.y, currentPosition.z);
                } else {
                    travelVertices.push(lastPosition.x, lastPosition.y, lastPosition.z);
                    travelVertices.push(currentPosition.x, currentPosition.y, currentPosition.z);
                }
            }
        });

        travelGeometry.setAttribute('position', new THREE.Float32BufferAttribute(travelVertices, 3));
        extrusionGeometry.setAttribute('position', new THREE.Float32BufferAttribute(extrusionVertices, 3));

        const travelLine = new THREE.LineSegments(travelGeometry, travelMaterial);
        const extrusionLine = new THREE.LineSegments(extrusionGeometry, extrusionMaterial);

        this.scene.add(travelLine);
        this.scene.add(extrusionLine);
    }

    /**
     * Parses a single line of GCode.
     * @param {string} line - The GCode line to parse.
     * @returns {Object|null} Parsed GCode data or null for unsupported commands.
     */
    private parseGCodeLine(line: string): (Position & CenterOffset & { command: string }) | null {
        const match = line.match(/([XYZEFIJ])([+-]?\d+(\.\d+)?)/g);
        if (!match) return null;

        const parsed: Partial<Position & CenterOffset & { command: string }> = {
            command: line.split(' ')[0]?.toUpperCase() || '', // Extract command (e.g., G0, G1, G2, etc.)
        };

        match.forEach((token) => {
            const axis = token[0].toLowerCase() as keyof (Position & CenterOffset);
            parsed[axis] = parseFloat(token.substring(1));
        });

        // Ensure parsed command is non-empty and valid
        if (!parsed.command) return null;

        return parsed as Position & CenterOffset & { command: string };
    }


    /**
     * Computes arc vertices for G2/G3 commands.
     * @param {Position} start - Starting position {x, y, z}.
     * @param {Position} end - Ending position {x, y, z}.
     * @param {CenterOffset} centerOffset - Arc center offsets {i, j}.
     * @param {boolean} clockwise - True for G2 (clockwise), false for G3 (counterclockwise).
     * @returns {number[]} Array of vertices for the arc.
     */
    private computeArcVertices(
        start: Position,
        end: Position,
        centerOffset: CenterOffset,
        clockwise: boolean
    ): number[] {
        const centerX = start.x + centerOffset.i;
        const centerY = start.y + centerOffset.j;

        const startAngle = Math.atan2(start.y - centerY, start.x - centerX);
        const endAngle = Math.atan2(end.y - centerY, end.x - centerX);

        const radius = Math.sqrt(centerOffset.i ** 2 + centerOffset.j ** 2);
        const angleDelta = clockwise
            ? endAngle - startAngle - 2 * Math.PI * (endAngle > startAngle ? 0 : 1)
            : endAngle - startAngle + 2 * Math.PI * (endAngle < startAngle ? 0 : 1);

        const vertices: number[] = [];

        for (let i = 0; i <= this.arcSegments; i++) {
            const t = i / this.arcSegments;
            const angle = startAngle + t * angleDelta;
            const x = centerX + Math.cos(angle) * radius;
            const y = centerY + Math.sin(angle) * radius;

            vertices.push(x, y, start.z); // Assuming constant Z
        }

        return vertices;
    }

    /**
     * Dynamically updates the arc smoothness.
     * @param {number} segments - Number of segments per arc.
     */
    public setArcSegments(segments: number): void {
        this.arcSegments = segments;
    }
}
