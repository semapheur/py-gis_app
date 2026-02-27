import type {
  ImageInfo,
  RadiometricParams,
  SelectOption,
} from "$lib/utils/types";
import { createContext } from "svelte";
import type { AnnotationInfo } from "./annotate.svelte";

interface EquipmentOptions {
  confidenceOptions: SelectOption[];
  statusOptions: SelectOption[];
}

export const [getEquipmentOptions, setEquipmentOptions] =
  createContext<EquipmentOptions>();

export interface ImageViewerOptions {
  imageInfo: ImageInfo;
  radiometricParams: RadiometricParams;
  annotations: AnnotationInfo[];
}

export const [getImageViewerOptions, setImageViewerOptions] =
  createContext<ImageViewerOptions>();
