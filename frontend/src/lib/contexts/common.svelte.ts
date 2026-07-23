import type {
  ImageInfo,
  RadiometricParams,
  SelectOption,
} from "$lib/utils/types";
import { createContext } from "svelte";
import type { AnnotationInfo } from "$lib/contexts/annotate.svelte";
import type { SchemaId } from "$lib/utils/brand";

interface EquipmentOptions {
  schemaOptions: SelectOption<SchemaId>[];
  confidenceOptions: Record<SchemaId, SelectOption[]>;
  statusOptions: Record<SchemaId, SelectOption[]>;
  configurationOptions: Record<SchemaId, SelectOption[]>;
  modificationOptions: Record<SchemaId, SelectOption[]>;
  visibilityOptions: Record<SchemaId, SelectOption[]>;
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
