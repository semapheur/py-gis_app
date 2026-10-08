import type {
  ImageInfo,
  RadiometricParams,
  SelectOption,
} from "#lib/utils/types.js";
import { createContext } from "svelte";
import type { AnnotationInfo } from "#lib/contexts/annotate.svelte.js";
import type { AreaInfo } from "#lib/contexts/area_editor.svelte.js";
import type {
  EquipmentFieldKey,
  equipmentSchema,
} from "#lib/schemas/equipment_annotation.js";

type EquipmentOptionKey = {
  [K in EquipmentFieldKey]: (typeof equipmentSchema)[K] extends {
    table: string;
  }
    ? K
    : never;
}[EquipmentFieldKey];

export type EquipmentOptions = Record<EquipmentOptionKey, SelectOption[]>;

export const [getEquipmentOptions, setEquipmentOptions] =
  createContext<EquipmentOptions>();

interface AnnotationData {
  equipment: AnnotationInfo[];
  personnel: AnnotationInfo[];
}

export interface ImageViewerOptions {
  imageInfo: ImageInfo;
  radiometricParams: RadiometricParams;
  annotations: AnnotationData;
  areas: AreaInfo[];
}

export const [getImageViewerOptions, setImageViewerOptions] =
  createContext<ImageViewerOptions>();
