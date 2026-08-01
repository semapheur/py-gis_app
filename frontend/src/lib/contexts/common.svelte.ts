import type {
  ImageInfo,
  RadiometricParams,
  SelectOption,
} from "$lib/utils/types";
import { createContext } from "svelte";
import type { AnnotationInfo } from "$lib/contexts/annotate.svelte";
import type { AreaInfo } from "./area_editor.svelte";

interface EquipmentOptions {
  confidenceOptions: SelectOption[];
  visibilityOptions: SelectOption[];
  statusOptions: SelectOption[];
  configurationOptions: SelectOption[];
  modificationOptions: SelectOption[];
  camoflageOptions: SelectOption[];
}

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
