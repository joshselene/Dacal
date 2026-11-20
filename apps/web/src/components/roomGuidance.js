// Pathway guidance for the learner room: what to do next, how to get there, and how to say it.
// Pure functions of a validated spec plus run state, so the room never invents its own task.

const STEPS = { N: [0, -1], E: [1, 0], S: [0, 1], W: [-1, 0] };
const COMPASS = { N: "north", E: "east", S: "south", W: "west" };

// Pathway prompt level (A = 3 most prompting, C = 1 fewest) -> what the room shows by itself.
export function guidanceLevel(prompt) {
  if (prompt >= 3) return "full";        // highlight + floor arrows + spoken next step
  if (prompt === 2) return "highlight";  // highlight only; speech when the tutor prompts
  return "none";                         // nothing shown; speech when the tutor prompts
}

function footprint(object) {
  const [x, y] = object.cell; const [w, h] = object.size;
  const cells = [];
  for (let cx = x; cx < x + w; cx += 1) for (let cy = y; cy < y + h; cy += 1) cells.push([cx, cy]);
  return cells;
}

function occupiedSet(spec) {
  const occupied = new Set();
  for (const object of spec.layout || []) for (const [x, y] of footprint(object)) occupied.add(`${x},${y}`);
  return occupied;
}

// Next goal: the first required item not yet in the basket (cheapest shelf that stocks it), then the counter.
export function nextTarget(spec, basket = [], stepsCompleted = []) {
  if (!spec?.layout || !spec?.task) return null;
  if (stepsCompleted.includes("completed_checkout")) return null;
  const have = new Set(basket.map((item) => item.sku));
  for (const sku of spec.task.required || []) {
    if (have.has(sku)) continue;
    let best = null;
    for (const object of spec.layout) {
      const item = (object.items || []).find((entry) => entry.sku === sku);
      if (item && (!best || item.price < best.price)) best = { object, price: item.price };
    }
    if (best) return { kind: "item", sku, objectId: best.object.id, object: best.object };
  }
  const counter = spec.layout.find((object) => object.asset === "counter" || object.id === "counter");
  return counter ? { kind: "counter", objectId: counter.id, object: counter } : null;
}

// Shortest walkable path (BFS, 4-neighbour) from the learner to any free cell next to the target.
export function pathToTarget(spec, from, target) {
  if (!spec?.room || !from || !target) return [];
  const { w, h } = spec.room;
  const occupied = occupiedSet(spec);
  const goals = new Set();
  for (const [x, y] of footprint(target.object)) {
    for (const [dx, dy] of Object.values(STEPS)) {
      const nx = x + dx; const ny = y + dy;
      if (nx >= 0 && ny >= 0 && nx < w && ny < h && !occupied.has(`${nx},${ny}`)) goals.add(`${nx},${ny}`);
    }
  }
  const start = `${from.x},${from.y}`;
  if (goals.has(start)) return [[from.x, from.y]];
  const previous = new Map([[start, null]]);
  const queue = [[from.x, from.y]];
  while (queue.length) {
    const [x, y] = queue.shift();
    for (const [dx, dy] of Object.values(STEPS)) {
      const nx = x + dx; const ny = y + dy; const key = `${nx},${ny}`;
      if (nx < 0 || ny < 0 || nx >= w || ny >= h || occupied.has(key) || previous.has(key)) continue;
      previous.set(key, `${x},${y}`);
      if (goals.has(key)) {
        const path = [];
        for (let cursor = key; cursor; cursor = previous.get(cursor)) path.unshift(cursor.split(",").map(Number));
        return path;
      }
      queue.push([nx, ny]);
    }
  }
  return [];
}

export function directionBetween([ax, ay], [bx, by]) {
  return Object.keys(STEPS).find((dir) => STEPS[dir][0] === bx - ax && STEPS[dir][1] === by - ay) || null;
}

// Plain-language next step, relative to where the learner is facing when we know it.
export function promptText(target, path, facing) {
  if (!target) return "You have finished the shopping task.";
  if (path.length === 1) {
    return target.kind === "counter"
      ? "You are at the checkout counter. Press the hand button to pay."
      : `The ${target.sku} is next to you. Press the hand button to pick it up.`;
  }
  if (path.length < 2) return target.kind === "counter" ? "Now go to the checkout counter to pay." : `Next, find the ${target.sku}.`;
  const dir = directionBetween(path[0], path[1]);
  const lead = target.kind === "counter" ? "You have everything. Go to the checkout counter." : `Next, find the ${target.sku}.`;
  const turn = facing && dir ? relativeTurn(facing, dir) : null;
  const how = turn ? `${turn}.` : `Walk ${COMPASS[dir] || "ahead"}.`;
  return `${lead} ${how}`;
}

// Where the next step is relative to the learner: forward, right, around, left, or "here" when at the goal.
export function relativeCue(path, facing) {
  if (path.length === 1) return "here";
  if (path.length < 2) return null;
  const dir = directionBetween(path[0], path[1]);
  if (!facing || !dir) return "forward";
  const order = ["N", "E", "S", "W"];
  return ["forward", "right", "around", "left"][(order.indexOf(dir) - order.indexOf(facing) + 4) % 4];
}

function relativeTurn(facing, dir) {
  const order = ["N", "E", "S", "W"];
  const delta = (order.indexOf(dir) - order.indexOf(facing) + 4) % 4;
  return ["Walk forward", "Turn right", "Turn around", "Turn left"][delta];
}

// Floor arrows: one per path cell pointing to the next cell, and a last one turning toward the target.
export function arrowSteps(path, target, limit = 6) {
  if (!target || !path.length) return [];
  const arrows = [];
  for (let index = 0; index < path.length - 1 && arrows.length < limit; index += 1) {
    arrows.push({ x: path[index][0], y: path[index][1], dir: directionBetween(path[index], path[index + 1]) });
  }
  const last = path[path.length - 1];
  const facing = footprint(target.object).map((cell) => directionBetween(last, cell)).find(Boolean);
  if (facing && arrows.length < limit) arrows.push({ x: last[0], y: last[1], dir: facing });
  return arrows;
}

// The run's compiled config (from the approved version) is what the server moves against; prefer it.
export function roomSpecFor(spec, run) {
  const compiled = run?.compiled_config;
  if (!compiled?.layout || !compiled?.room) return spec;
  return { ...spec, room: compiled.room, layout: compiled.layout, task: compiled.task || spec?.task };
}

export function guidanceFor(spec, run, pathway) {
  const support = run?.compiled_config?.prompt != null && run?.pathway === pathway
    ? { prompt: run.compiled_config.prompt, volume: run.compiled_config.volume }
    : spec?.support?.[pathway] || { prompt: 2, volume: 60 };
  const position = run?.learner_position || null;
  const target = nextTarget(spec, run?.basket || [], run?.steps_completed || []);
  const path = target && position ? pathToTarget(spec, position, target) : [];
  return {
    level: guidanceLevel(support.prompt),
    volume: Math.max(0, Math.min(support.volume ?? 60, 80)),
    target,
    targetId: target?.objectId || null,
    path,
    arrows: arrowSteps(path, target),
    cue: target ? relativeCue(path, position?.dir) : null,
    text: promptText(target, path, position?.dir),
  };
}
