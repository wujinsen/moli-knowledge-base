import pinsDoc from '../data/红楼梦.garden_digital_tour_pins.json';

export type PinTier = 'primary' | 'secondary' | 'minor';

export type ExteriorLabelAnchor = 'north' | 'south' | 'east' | 'west';

export interface CalibratedPin {
  xPct: number;
  yPct: number;
  tier: PinTier;
}

export interface ExteriorLabel {
  id: string;
  xPct: number;
  yPct: number;
  anchor: ExteriorLabelAnchor;
  href?: string;
}

export const GARDEN_DIGITAL_TOUR_PINS: Record<string, CalibratedPin> = pinsDoc.pins;

export const GARDEN_DIGITAL_TOUR_EXTERIOR: ExteriorLabel[] = pinsDoc.exteriorLabels ?? [];

export const GARDEN_DIGITAL_TOUR_WALL = pinsDoc.gardenWall ?? null;

export const GARDEN_DIGITAL_TOUR_IMAGE = pinsDoc.baseImage;

export const GARDEN_DIGITAL_TOUR_PIN_NOTE = pinsDoc.note;

/** 底图像素坐标（与 GardenDigitalTour 画布一致） */
export function pinToScene(id: string, sceneW: number, sceneH: number): { x: number; y: number } | null {
  const pin = GARDEN_DIGITAL_TOUR_PINS[id];
  if (!pin) return null;
  return { x: (pin.xPct / 100) * sceneW, y: (pin.yPct / 100) * sceneH };
}

export function pinToPercent(id: string): { left: number; top: number } | null {
  const pin = GARDEN_DIGITAL_TOUR_PINS[id];
  if (!pin) return null;
  return { left: pin.xPct, top: pin.yPct };
}
