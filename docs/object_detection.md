# Image annotation formats

## Common objects in context (COCO)

COCO stores annotations using JSON.

```json
annotation{
  "id": int,
  "image_id": int,
  "category_id": int,
  "segmentation": RLE or [polygon]
  "area": float
  "bbox": [x,y,width,height]
  "iscrowd": bool
}
categories[{
  "id": int,
  "name": str,
  "supercategory": str
}]
```

## Pascal visual object classes (PVOC)

Pascal VOC stores annotations using XML

```xml
<annotation>
  <folder></folder>
  <filename></filename>
  <path></path>
  <source>
    <database></database>
  </source>
  <size>
    <width></width>
    <height></height>
    <depth></depth>
  </size>
  <segmented>bool</segmented>
  <object>
    <name></name>
    <pose></pose>
    <truncated>bool</truncated>
    <difficult>bool</difficult>
    <occluded>bool</occluded>
    <bndbox>
      <xmin></xmin>
      <xmax></xmax>
      <ymin></ymin>
      <ymax></ymax>
    </bndbox>
  </object>
</annotation>
```

## You only look once (YOLO)

In the YOLO labeling format, a `.txt` file with the same name is created for each image file in the same directory.

```txt
<object-class> <x> <y> <width> <height>
```
