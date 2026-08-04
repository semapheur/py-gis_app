import type {
  ImageInfo,
  RadiometricParams,
  SelectOption,
} from "$lib/utils/types";
import { createContext } from "svelte";
import type { AnnotationInfo } from "$lib/contexts/annotate.svelte";
import type { AreaInfo } from "$lib/contexts/area_editor.svelte";
import type {
  EquipmentFieldKey,
  equipmentSchema,
} from "$lib/schemas/equipment_annotation";

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

export interface ImageViewerOptions {
  imageInfo: ImageInfo;
  radiometricParams: RadiometricParams;
  annotations: AnnotationInfo[];
  areas: AreaInfo[];
}

export const [getImageViewerOptions, setImageViewerOptions] =
  createContext<ImageViewerOptions>();
