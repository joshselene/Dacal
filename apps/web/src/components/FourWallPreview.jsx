import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { ArrowDown, ArrowLeft, ArrowRight, ArrowUp, Hand, Pause, RotateCcw } from "../m3/icons.jsx";

const CUE_ICONS = { forward: ArrowUp, right: ArrowRight, around: ArrowDown, left: ArrowLeft, here: Hand };
import "./FourWallPreview.css";

const DIRECTIONS = { N: [0, -1], E: [1, 0], S: [0, 1], W: [-1, 0] };
const WALLS = Object.keys(DIRECTIONS);
const ARROW_YAW = { N: 0, W: Math.PI / 2, S: Math.PI, E: -Math.PI / 2 };
const GUIDE_COLOR = "#14b8b0";
const MAX_ARROWS = 6;

// Pathway guidance meshes: built once per scene, then shown, moved and pulsed each frame.
function buildGuide(scene, spec) {
  const glow = new THREE.MeshBasicMaterial({ color: GUIDE_COLOR, transparent: true, opacity: .22, depthWrite: false });
  const pad = new THREE.MeshBasicMaterial({ color: GUIDE_COLOR, transparent: true, opacity: .45, depthWrite: false });
  const solid = new THREE.MeshBasicMaterial({ color: "#0a7f7a" });
  const shell = new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1), glow);
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), pad);
  floor.rotation.x = -Math.PI / 2;
  const marker = new THREE.Mesh(new THREE.ConeGeometry(.2, .42, 18), solid);
  marker.rotation.x = Math.PI;
  const shape = new THREE.Shape();
  [[0, .34], [.28, -.02], [.11, -.02], [.11, -.32], [-.11, -.32], [-.11, -.02], [-.28, -.02]]
    .forEach(([x, y], index) => (index ? shape.lineTo(x, y) : shape.moveTo(x, y)));
  const arrowGeometry = new THREE.ShapeGeometry(shape);
  const arrows = Array.from({ length: MAX_ARROWS }, () => {
    const holder = new THREE.Group();
    const mesh = new THREE.Mesh(arrowGeometry, solid);
    mesh.rotation.x = -Math.PI / 2;
    holder.add(mesh); holder.visible = false; scene.add(holder);
    return holder;
  });
  [shell, floor, marker].forEach((mesh) => { mesh.visible = false; mesh.renderOrder = 2; scene.add(mesh); });
  const boxes = new Map(spec.layout.map((object) => [object.id, {
    x: object.cell[0] + object.size[0] / 2, z: object.cell[1] + object.size[1] / 2,
    w: object.size[0], d: object.size[1], h: ["shelf", "fridge"].includes(object.asset) ? 2.1 : 1.3,
  }]));
  return { glow, shell, floor, marker, arrows, boxes };
}

function updateGuide(guide, guidance, clock, still) {
  const target = guidance?.targetId ? guide.boxes.get(guidance.targetId) : null;
  const showTarget = Boolean(target) && guidance.level !== "none";
  [guide.shell, guide.floor, guide.marker].forEach((mesh) => { mesh.visible = showTarget; });
  if (showTarget) {
    guide.shell.scale.set(target.w + .14, target.h, target.d + .14);
    guide.shell.position.set(target.x, target.h / 2, target.z);
    guide.floor.scale.set(target.w + .5, target.d + .5, 1);
    guide.floor.position.set(target.x, .035, target.z);
    guide.marker.position.set(target.x, target.h + .45 + (still ? 0 : Math.sin(clock * 2.2) * .08), target.z);
    guide.glow.opacity = still ? .22 : .16 + (Math.sin(clock * 2.2) + 1) * .06;
  }
  const steps = guidance?.level === "full" ? guidance.arrows || [] : [];
  guide.arrows.forEach((holder, index) => {
    const step = steps[index];
    holder.visible = Boolean(step);
    if (!step) return;
    holder.position.set(step.x + .5, .045, step.y + .5);
    holder.rotation.y = ARROW_YAW[step.dir] ?? 0;
  });
}

function buildScene(spec) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color("#dfe9ee");
  scene.add(new THREE.HemisphereLight(0xffffff, 0xa5b5ba, 1.8));
  const light = new THREE.DirectionalLight(0xfff4e4, 1.1);
  light.position.set(4, 12, 8);
  scene.add(light);
  const { w: width, h: depth } = spec.room;
  const selectable = [];
  const rearWalls = [];
  const shoppers = [];
  const materials = new Map();
  function material(color) {
    if (!materials.has(color)) materials.set(color, new THREE.MeshStandardMaterial({ color, roughness: .72 }));
    return materials.get(color);
  }
  function box(parent, size, position, color) {
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(...size), material(color));
    mesh.position.set(...position);
    parent.add(mesh);
    return mesh;
  }
  function label(parent, text, position, scale = 1.5) {
    const canvas = document.createElement("canvas");
    canvas.width = 512; canvas.height = 128;
    const context = canvas.getContext("2d");
    context.fillStyle = "#f7fbff";
    context.fillRect(0, 0, 512, 128);
    context.fillStyle = "#24444e";
    context.textAlign = "center";
    context.textBaseline = "middle";
    context.font = "600 36px sans-serif";
    context.fillText(text, 256, 64, 484);
    const texture = new THREE.CanvasTexture(canvas);
    texture.colorSpace = THREE.SRGBColorSpace;
    const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: texture }));
    sprite.scale.set(scale, scale / 4, 1);
    sprite.position.set(...position);
    parent.add(sprite);
  }
  box(scene, [width, .12, depth], [width / 2, -.08, depth / 2], "#edf3f4");
  for (let column = 0; column < width; column += 1) {
    for (let row = 0; row < depth; row += 1) {
      if ((column + row) % 2 === 0) box(scene, [.98, .01, .98], [column + .5, 0, row + .5], "#dce7e9");
    }
  }
  box(scene, [width + .2, 2.8, .15], [width / 2, 1.4, -.1], "#f4f7f7");
  box(scene, [.15, 2.8, depth], [-.1, 1.4, depth / 2], "#edf3f4");
  box(scene, [.15, 2.8, depth], [width + .1, 1.4, depth / 2], "#edf3f4");
  box(scene, [width, .4, .04], [width / 2, 2.4, .02], "#378d89");
  const entrance = new Set(spec.room.entrance.cells.map(([column]) => column));
  for (let column = 0; column < width; column += 1) {
    if (!entrance.has(column)) rearWalls.push(box(scene, [1, 2.8, .15], [column + .5, 1.4, depth + .1], "#e9f0f2"));
  }
  spec.room.entrance.cells.forEach(([column, row]) => box(scene, [.98, .02, .98], [column + .5, .02, row + .5], "#587582"));
  const entranceCenter = spec.room.entrance.cells.reduce((sum, [column]) => sum + column + .5, 0) / spec.room.entrance.cells.length;
  box(scene, [width, .1, 3], [width / 2, -.1, depth + 1.5], "#a8b6bb");
  label(scene, "Entrance", [entranceCenter, 1.65, depth + 1.4], 1.7);
  label(scene, "Neighbourhood shop", [width / 2, 2.4, .15], 3);
  function person(position, color) {
    const group = new THREE.Group();
    group.position.set(...position);
    box(group, [.32, .62, .22], [0, .92, 0], color);
    box(group, [.12, .56, .14], [-.1, .31, 0], "#415465");
    box(group, [.12, .56, .14], [.1, .31, 0], "#415465");
    const head = new THREE.Mesh(new THREE.SphereGeometry(.16, 12, 10), material("#c79773"));
    head.position.y = 1.42; group.add(head); scene.add(group);
    return group;
  }
  const palette = ["#6cacc6", "#dfab64", "#d8877d", "#8bb59c"];
  spec.layout.forEach((object, objectIndex) => {
    const [column, row] = object.cell;
    const [objectWidth, objectDepth] = object.size;
    const group = new THREE.Group();
    group.position.set(column + objectWidth / 2, 0, row + objectDepth / 2);
    group.userData.objectId = object.id;
    scene.add(group);
    const color = palette[objectIndex % palette.length];
    if (["shelf", "fridge"].includes(object.asset)) {
      box(group, [objectWidth - .08, 1.6, .06], [0, .8, -objectDepth / 2 + .1], color);
      for (const side of [-1, 1]) box(group, [.06, 1.7, objectDepth - .08], [side * (objectWidth / 2 - .07), .85, 0], "#a1b4bd");
      for (let shelf = 0; shelf < 4; shelf += 1) {
        const height = .15 + shelf * .4;
        box(group, [objectWidth - .08, .05, objectDepth - .08], [0, height, 0], "#eef3f5");
        const count = Math.max(1, Math.floor(objectWidth / .28));
        for (let product = 0; product < count; product += 1) {
          const productColor = palette[(product + shelf + objectIndex) % palette.length];
          box(group, [.17, .25, .18], [-objectWidth / 2 + .2 + product * .28, height + .15, .1], productColor);
        }
      }
      label(group, (object.items || []).map((item) => `${item.sku}  ₹${item.price}`).join(" / ") || object.id, [0, 1.95, .15], Math.min(objectWidth, 2.8));
    } else if (object.asset === "counter") {
      box(group, [objectWidth - .08, .95, objectDepth - .08], [0, .48, 0], "#83a995");
      box(group, [objectWidth, .08, objectDepth], [0, 1, 0], "#f4f6ef");
      box(group, [.28, .25, .16], [0, 1.16, 0], "#37535e");
      label(group, "Checkout", [0, 2.05, 0], 1.65);
      person([column + objectWidth / 2, 0, Math.max(.5, row - .45)], "#34877e");
    } else {
      box(group, [objectWidth - .08, .7, objectDepth - .08], [0, .35, 0], "#b4bdc9");
      label(group, `${object.id} (${object.asset})`, [0, 1.15, 0], 1.6);
    }
    selectable.push(group);
  });
  const occupied = (column, row) => spec.layout.some((object) => column >= object.cell[0] && column < object.cell[0] + object.size[0] && row >= object.cell[1] && row < object.cell[1] + object.size[1]);
  for (let row = 2; row < depth - 1 && shoppers.length < 5; row += 2) {
    for (let column = 1; column < width - 1 && shoppers.length < 5; column += 3) {
      if (!occupied(column, row)) shoppers.push(person([column + .5, 0, row + .5], palette[shoppers.length % palette.length]));
    }
  }
  return { scene, rearWalls, shoppers, selectable, guide: buildGuide(scene, spec) };
}

export default function FourWallPreview({ spec, pathway = "B", displayMode = "overview", learnerPosition = null, onMove, onSelect, onPause, interactiveKeyboard = false, previewOnly = false, onObjectSelect, paused = false, guidance = null, controlsExtra = null }) {
  const hostRef = useRef(null);
  const canvasRef = useRef(null);
  const liveRef = useRef({ learnerPosition, pathway, paused, guidance });
  const controlsRef = useRef(null);
  const [view, setView] = useState(displayMode);
  const [failure, setFailure] = useState("");
  const requestedWall = new URLSearchParams(location.search).get("wall")?.toUpperCase();
  const wall = WALLS.includes(requestedWall) ? requestedWall : null;
  const mode = wall && interactiveKeyboard ? wall : view;

  useEffect(() => { liveRef.current = { learnerPosition, pathway, paused, guidance }; }, [learnerPosition, pathway, paused, guidance]);
  useEffect(() => { setView(displayMode); }, [displayMode]);
  useEffect(() => {
    if (!spec?.room || !spec?.layout) return;
    let renderer;
    try {
      const context = canvasRef.current.getContext("webgl2", { antialias: true, preserveDrawingBuffer: true });
      if (!context) throw new Error("WebGL2 unavailable");
      context.pixelStorei(context.UNPACK_FLIP_Y_WEBGL, false);
      context.pixelStorei(context.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false);
      renderer = new THREE.WebGLRenderer({ canvas: canvasRef.current, context, antialias: true, preserveDrawingBuffer: true });
    }
    catch { setFailure("3D preview is unavailable. WebGL2 is required."); return; }
    setFailure("");
    renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 1.5));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    const store = buildScene(spec);
    const camera = new THREE.PerspectiveCamera(42, 1, .05, 200);
    const host = hostRef.current;
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enabled = mode === "overview" && !previewOnly;
    controls.enablePan = false;
    controls.maxPolarAngle = Math.PI / 2.3;
    controls.minDistance = 7;
    controls.maxDistance = 38;
    controls.target.set(spec.room.w / 2, .2, spec.room.h / 2);
    controlsRef.current = controls;
    let resetPosition;
    function resize() {
      const width = host.clientWidth;
      const height = host.clientHeight;
      if (!width || !height) return;
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      const distance = Math.max(spec.room.w, spec.room.h) * Math.max(1.1, 1 / camera.aspect);
      resetPosition = new THREE.Vector3(spec.room.w / 2 + distance * .48, distance * .9, spec.room.h / 2 + distance);
      if (mode === "overview") { camera.position.copy(resetPosition); controls.update(); }
    }
    const observer = new ResizeObserver(resize);
    observer.observe(host); resize();
    controlsRef.current.resetView = () => { camera.position.copy(resetPosition); controls.target.set(spec.room.w / 2, .2, spec.room.h / 2); controls.update(); };
    const raycaster = new THREE.Raycaster();
    function selectObject(event) {
      if (mode !== "overview" || !onObjectSelect) return;
      const bounds = renderer.domElement.getBoundingClientRect();
      raycaster.setFromCamera(new THREE.Vector2((event.clientX - bounds.left) / bounds.width * 2 - 1, -(event.clientY - bounds.top) / bounds.height * 2 + 1), camera);
      const hit = raycaster.intersectObjects(store.selectable, true)[0];
      if (hit) {
        let object = hit.object;
        while (object && !object.userData.objectId) object = object.parent;
        if (object) onObjectSelect(object.userData.objectId);
      }
    }
    renderer.domElement.addEventListener("click", selectObject);
    let clock = 0;
    let previous = 0;
    const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)");
    renderer.setAnimationLoop((time) => {
      const elapsed = Math.min((time - previous) / 1000 || 0, .1); previous = time;
      const live = liveRef.current;
      if (!live.paused && !reducedMotion.matches) clock += elapsed;
      const position = live.learnerPosition || { x: spec.room.entrance.cells[0][0], y: spec.room.entrance.cells[0][1], dir: "N" };
      const density = spec.support?.[live.pathway]?.density ?? 2;
      store.shoppers.forEach((shopper, index) => {
        shopper.visible = index < density && Math.hypot(shopper.position.x - position.x - .5, shopper.position.z - position.y - .5) > 1.05;
        shopper.rotation.y = Math.sin(clock * .5 + index) * .25;
      });
      store.rearWalls.forEach((object) => { object.visible = mode !== "overview"; });
      updateGuide(store.guide, live.guidance, clock, reducedMotion.matches);
      const width = host.clientWidth; const height = host.clientHeight;
      renderer.setScissorTest(false); renderer.clear();
      if (mode === "overview") { controls.update(); renderer.setViewport(0, 0, width, height); renderer.render(store.scene, camera); return; }
      const directions = (mode === "room" || mode === "grid2x2") ? WALLS : [wall || (mode === "laptop" ? position.dir : mode)];
      renderer.setScissorTest(true);
      directions.forEach((direction, index) => {
        const columns = directions.length === 1 ? 1 : (mode === "grid2x2" || width < 700 ? 2 : 4);
        const rows = directions.length / columns;
        const viewWidth = Math.floor(width / columns); const viewHeight = Math.floor(height / rows);
        camera.fov = 70; camera.aspect = viewWidth / viewHeight; camera.updateProjectionMatrix();
        camera.position.set(position.x + .5, 1.45, position.y + .5);
        const delta = DIRECTIONS[direction] || DIRECTIONS.N;
        camera.lookAt(position.x + .5 + delta[0], 1.25, position.y + .5 + delta[1]); // slight downward tilt shows floor arrows
        renderer.setViewport(index % columns * viewWidth, height - (Math.floor(index / columns) + 1) * viewHeight, viewWidth, viewHeight);
        renderer.setScissor(index % columns * viewWidth + 1, height - (Math.floor(index / columns) + 1) * viewHeight + 1, viewWidth - 2, viewHeight - 2);
        renderer.render(store.scene, camera);
      });
    });
    return () => {
      renderer.setAnimationLoop(null); observer.disconnect(); controls.dispose();
      renderer.domElement.removeEventListener("click", selectObject);
      store.scene.traverse((object) => {
        object.geometry?.dispose();
        if (object.material?.map) object.material.map.dispose();
        object.material?.dispose();
      });
      renderer.dispose(); controlsRef.current = null;
    };
  }, [spec, mode, previewOnly, onObjectSelect]);

  useEffect(() => {
    if (!interactiveKeyboard) return;
    function keydown(event) {
      if (event.target.closest("input,textarea,select,button,[contenteditable]")) return;
      const direction = { ArrowUp: "N", ArrowDown: "S", ArrowLeft: "W", ArrowRight: "E" }[event.key];
      if (direction) { event.preventDefault(); onMove?.(direction); }
      else if (event.key === " ") { event.preventDefault(); onSelect?.(); }
      else if (event.key === "Escape") { event.preventDefault(); onPause?.(); }
    }
    window.addEventListener("keydown", keydown);
    return () => window.removeEventListener("keydown", keydown);
  }, [interactiveKeyboard, onMove, onSelect, onPause]);

  const labels = mode === "room" || mode === "grid2x2" ? WALLS : [mode === "overview" ? "Scene overview" : mode === "laptop" ? learnerPosition?.dir || "N" : mode];
  return (
    <section className={`four-wall-preview ${previewOnly ? "preview-only" : ""}`}>
      {!previewOnly && <header className="scene-toolbar"><h3>Scene preview</h3><div className="scene-tools">
        <select aria-label="Scene view" value={view} onChange={(event) => setView(event.target.value)}>
          <option value="overview">Overview</option><option value="laptop">Laptop</option><option value="room">Four walls</option><option value="grid2x2">2 x 2 grid</option>
          {WALLS.map((direction) => <option key={direction} value={direction}>{direction} wall</option>)}
        </select>
        <button type="button" className="icon-button" aria-label="Reset camera" title="Reset camera" disabled={mode !== "overview"} onClick={() => controlsRef.current?.resetView()}><RotateCcw size={16} /></button>
      </div></header>}
      <div ref={hostRef} className={`scene-viewport ${labels.length === 4 ? "multi-view" : ""} ${paused ? "is-paused" : ""}`}>
        <canvas ref={canvasRef} aria-label="3D shop scene" />
        {!previewOnly && <div className={`scene-labels ${mode === "grid2x2" ? "force-grid" : ""}`}>
          {labels.map((name) => <span key={name}>{name}</span>)}
        </div>}
        {(failure || !spec) && <p className="scene-failure" role="status">{failure || "No scene available."}</p>}
        {guidance?.level === "full" && guidance.text && !paused && (() => {
          const CueIcon = CUE_ICONS[guidance.cue];
          return <p className="scene-guidance" role="status" aria-live="polite">{CueIcon && <CueIcon size={26} aria-hidden="true" />}<span>{guidance.text}</span></p>;
        })()}
        {paused && <div className="scene-paused"><Pause size={24} /><strong>Paused</strong></div>}
      </div>
      {interactiveKeyboard && <div className="runtime-key-controls" aria-label="Learner controls">
        {[["W", ArrowLeft], ["N", ArrowUp], ["S", ArrowDown], ["E", ArrowRight]].map(([direction, Icon]) => <button key={direction} type="button" className="icon-button" title={`Move ${direction}`} aria-label={`Move ${direction}`} disabled={paused} onClick={() => onMove?.(direction)}><Icon size={28} /></button>)}
        <button type="button" className="icon-button" title="Select item" aria-label="Select item" onClick={onSelect}><Hand size={28} /></button>
        <button type="button" className="icon-button" title={paused ? "Resume" : "Pause"} aria-label={paused ? "Resume" : "Pause"} onClick={onPause}><Pause size={28} /></button>
        {controlsExtra}
      </div>}
    </section>
  );
}