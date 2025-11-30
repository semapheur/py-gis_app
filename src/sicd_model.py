import json
from typing import Literal, Optional, TypeAlias, TypedDict, Union, cast


class RadarModeObject(TypedDict):
  ModeType: Literal["SPOTLIGHT", "STRIPMAP", "DYNAMIC STRIPMAP"]
  ModeID: Optional[str]


class CollectionInfoObject(TypedDict):
  CollectorName: str
  CoreName: str
  CollectType: Literal["MONOSTATIC", "BISTATIC"]
  RadarMode: RadarModeObject
  Classification: str
  CountryCode: Optional[str]
  Parameter: Optional[dict[str, str]]


class XYZ(TypedDict):
  X: float
  Y: float
  Z: float


class LatLon(TypedDict):
  Lat: float
  Lon: float


class LatLonHeight(LatLon):
  HAE: float


class SceneCenterPointObject(TypedDict):
  ECF: XYZ
  LLH: LatLonHeight


class ImageCorner(LatLon):
  index: Literal["1:FRFC", "2:FRLC", "3:LRLC", "4:LRFC"]


class GeoDataObject(TypedDict):
  EarthModel: str
  SCP: SceneCenterPointObject
  ImageCorners: list[ImageCorner]


class Polynomial(TypedDict):
  Coeffs: list[float]


class WeightType(TypedDict):
  WindowName: str
  Parameter: Optional[dict[str, str]]


class GridAxis(TypedDict):
  UVectECF: XYZ
  SS: float
  ImpRespWid: float
  Sgn: Literal[-1, 1]
  ImpRespBW: float
  KCtr: float
  DeltaK1: float
  DeltaK2: float
  DeltaKCOAPoly: Optional[Polynomial]
  WgtType: Optional[WeightType]
  WgtFunct: Optional[list[float]]


class GridObject(TypedDict):
  ImagePlane: Literal["GROUND", "SLANT", "OTHER"]
  Type: Literal["RGAZIM", "RGZERO", "XRGYCR", "XCTYAT", "PLANE"]
  TimeCOAPoly: Polynomial
  Row: GridAxis
  Col: GridAxis


class InterPulsePeriod(TypedDict):
  TStart: float
  TEnd: float
  IPPStart: float
  IPPEnd: float
  IPPPoly: Polynomial
  index: int


class TimelineObject(TypedDict):
  CollectStart: str
  CollectDuration: float
  IPP: list[InterPulsePeriod]


class SceneCenterPointCenterOfAperture(TypedDict):
  SCPTime: float
  ARPPos: XYZ
  ARPVel: XYZ
  ARPAcc: XYZ
  SideOfTrack: Literal["L", "H"]
  SlantRange: float
  GroundRange: float
  DopplerConeAng: float
  GrazeAng: float
  IncidenceAng: float
  TwistAng: float
  SlopeAng: float
  AzimAng: float
  LayoverAng: float


class Sicd(TypedDict):
  CollectionInfo: CollectionInfoObject
  ImageCreation: dict
  ImageData: dict
  GeoData: GeoDataObject
  Grid: GridObject
  Timeline: TimelineObject
  Position: dict
  RadarCollection: dict
  SCPCOA: SceneCenterPointCenterOfAperture
  Radiometric: Optional[dict]
  Antenna: Optional[dict]
  ErrorStatistics: Optional[dict]
  PFA: dict


class SicdObject(TypedDict):
  version: str
  metadata: Sicd
