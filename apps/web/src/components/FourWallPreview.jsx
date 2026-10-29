
import React, { useState } from "react";
import "./FourWallPreview.css";

const WALLS = [
  { id: "front", label: "Front wall" },
  { id: "left", label: "Left wall" },
  { id: "right", label: "Right wall" },
  { id: "back", label: "Back wall" },
];

export default function FourWallPreview({ environment = "Classroom" }) {
  const [selectedWall, setSelectedWall] = useState("front");
  const [scene, setScene] = useState("classroom");
  const [showLabels, setShowLabels] = useState(true);

  const sceneClass = `scene-${scene}`;

  return (
    <section className="four-wall-preview">
      <header className="four-wall-header">
        <div>
          <span className="eyebrow">IMMERSIVE ROOM PREVIEW</span>
          <h2>Four-wall environment</h2>
          <p>
            Preview how the learning environment could be projected around
            the learner.
          </p>
        </div>

        <span className="prototype-badge">3D prototype</span>
      </header>

      <div className="four-wall-toolbar">
        <label>
          Environment
          <select
            value={scene}
            onChange={(event) => setScene(event.target.value)}
          >
            <option value="classroom">Classroom</option>
            <option value="forest">Forest</option>
            <option value="space">Space</option>
            <option value="calm">Calm room</option>
          </select>
        </label>

        <label className="wall-label-toggle">
          <input
            type="checkbox"
            checked={showLabels}
            onChange={(event) => setShowLabels(event.target.checked)}
          />
          Show wall labels
        </label>
      </div>

      <div className={`room-stage ${sceneClass}`}>
        <div className="room-perspective">
          <div className="room-wall room-back">
            {showLabels && <span className="wall-name">BACK WALL</span>}
            <div className="scene-content">
              {scene === "classroom" && (
                <>
                  <span className="window-shape" />
                  <span className="board-shape" />
                  <span className="room-caption">Welcome to class</span>
                </>
              )}
              {scene === "forest" && (
                <>
                  <span className="tree-shape tree-a" />
                  <span className="tree-shape tree-b" />
                  <span className="room-caption">Explore the forest</span>
                </>
              )}
              {scene === "space" && (
                <>
                  <span className="planet-shape" />
                  <span className="star-field">✦　·　✧　·　✦</span>
                </>
              )}
              {scene === "calm" && (
                <>
                  <span className="calm-circle" />
                  <span className="room-caption">A calm place</span>
                </>
              )}
            </div>
          </div>

          <div className="room-wall room-left">
            {showLabels && <span className="wall-name">LEFT WALL</span>}
            <div className="side-content">
              {scene === "forest" ? "🌳" : scene === "space" ? "✦" : "◇"}
            </div>
          </div>

          <div className="room-wall room-right">
            {showLabels && <span className="wall-name">RIGHT WALL</span>}
            <div className="side-content">
              {scene === "forest" ? "🌲" : scene === "space" ? "🪐" : "✧"}
            </div>
          </div>

          <div className="room-floor">
            {showLabels && <span className="floor-name">FLOOR</span>}
            <div className="floor-grid" />
          </div>
        </div>

        <p className="room-stage-note">
          Interactive concept preview · Not connected to physical projectors
        </p>
      </div>

      <div className="wall-selector">
        {WALLS.map((wall) => (
          <button
            key={wall.id}
            type="button"
            className={
              selectedWall === wall.id ? "wall-option selected" : "wall-option"
            }
            onClick={() => setSelectedWall(wall.id)}
          >
            <span className={`wall-mini wall-mini-${wall.id}`} />
            <span>{wall.label}</span>
            {selectedWall === wall.id && <span>✓</span>}
          </button>
        ))}
      </div>

      <div className="selected-wall-info">
        <div>
          <span className="mini-label">SELECTED SURFACE</span>
          <h3>
            {WALLS.find((wall) => wall.id === selectedWall)?.label}
          </h3>
          <p>
            This surface represents one part of the immersive learning
            environment.
          </p>
        </div>
        <span className="surface-status">Preview only</span>
      </div>
    </section>
  );
}
