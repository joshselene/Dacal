// Google Material Symbols Rounded, exported under the component names the app already uses.
// Subset font: fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,400,0..1,0
//   &icon_names=<sorted, comma-separated names below>&display=block
import React from "react";
import "./icons.css";

export function MaterialSymbol({ name, size = 24, className = "", ...rest }) {
  return (
    <span className={`material-symbols-rounded ${className}`} aria-hidden="true"
      style={{ fontSize: size, width: size, height: size }} {...rest}>
      {name}
    </span>
  );
}

const make = (name) => {
  const Icon = (props) => <MaterialSymbol name={name} {...props} />;
  Icon.displayName = `MaterialSymbol(${name})`;
  return Icon;
};

export const ArrowDown = make("arrow_downward");
export const ArrowLeft = make("arrow_back");
export const ArrowRight = make("arrow_forward");
export const ArrowUp = make("arrow_upward");
export const Bell = make("notifications");
export const BookOpen = make("menu_book");
export const CircleHelp = make("help");
export const Clock3 = make("schedule");
export const FolderOpen = make("folder_open");
export const Hand = make("back_hand");
export const House = make("home");
export const LayoutGrid = make("grid_view");
export const LogOut = make("logout");
export const Moon = make("dark_mode");
export const Pause = make("pause");
export const Plus = make("add");
export const RotateCcw = make("restart_alt");
export const Sparkles = make("auto_awesome");
export const Sun = make("light_mode");
export const Volume2 = make("volume_up");
export const VolumeX = make("volume_off");
export const X = make("close");
