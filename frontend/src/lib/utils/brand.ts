declare const __brand: unique symbol;
type Brand<T, B extends string> = T & { [__brand]: B };

export type ImageId = Brand<string, "imageId">;
export type AttributeId = Brand<string, "attributeId">;
export type SchemaId = Brand<string, "schemaId">;
