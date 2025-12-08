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


class LatLonHeightIndex(LatLonHeight):
  index: int


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


class MinMax(TypedDict):
  Min: float
  Max: float


class TxStep(TypedDict):
  WFIndex: Optional[int]
  TxPolarization: Optional[Literal["V", "H", "RHC", "LHC", "OTHER"]]


class ChanParameters(TypedDict):
  TxRcvPolarization: Literal[
    "V:V",
    "H",
    "H:V",
    "H",
    "RHC:RHC",
    "RHC:LHC",
    "LHC:RHC",
    "LHC:LHC",
    "RHC:V",
    "RHC:H",
    "LHC:V",
    "LHC:H",
    "V:RHC",
    "V:LHC",
    "H:RHC",
    "H:LHC",
    "OTHER",
    "UNKNOWN",
  ]
  RcvAPCIndex: Optional[int]


class WFParameters(TypedDict):
  TxPulseLength: Optional[float]
  TxRFBandwidth: Optional[float]
  TxFreqStart: Optional[float]
  TxFMRate: Optional[float]
  RcvDemodType: Optional[Literal["STRECTH", "CHIRP"]]
  RcvWindowLength: Optional[float]
  ADCSampleRate: Optional[float]
  RcvIFBandwith: Optional[float]
  RcvFreqStart: Optional[float]
  RcvFMRate: Optional[float]


class ReferencePoint(TypedDict):
  ECF: XYZ
  Line: float
  Sample: float


class XDirection(TypedDict):
  UVectECF: XYZ
  LineSpacing: float
  NumLines: int
  FirstLine: int


class YDirection(TypedDict):
  UVectECF: XYZ
  SampleSpacing: float
  NumSamples: int
  FirstSample: int


class Segment(TypedDict):
  StartLine: int
  StartSample: int
  EndLine: int
  EndSample: int
  Identifier: str


class PlaneObject(TypedDict):
  RefPt: ReferencePoint
  XDir: XDirection
  YDir: YDirection
  SegmentList: Optional[list[Segment]]
  Orientation: Optional[Literal["UP", "DOWN", "LEFT", "RIGHT", "ARBITRARY"]]


class AreaObject(TypedDict):
  Corner: list[LatLonHeightIndex]
  Plane: Optional[PlaneObject]
  Parameter: Optional[dict[str, str]]


class RadarCollectionObject(TypedDict):
  TxFrequency: MinMax
  RefFreqIndex: Optional[int]
  Waveform: Optional[list[WFParameters]]
  TxPolarization: Literal["V", "H", "RHC", "LHC", "OTHER", "UNKNOWN", "SEQUENCE"]
  TxSequence: Optional[list[TxStep]]
  RcvChannels: list[ChanParameters]
  Area: Optional[AreaObject]


class Sicd(TypedDict):
  CollectionInfo: CollectionInfoObject
  ImageCreation: dict
  ImageData: dict
  GeoData: GeoDataObject
  Grid: GridObject
  Timeline: TimelineObject
  Position: dict
  RadarCollection: RadarCollectionObject
  SCPCOA: SceneCenterPointCenterOfAperture
  Radiometric: Optional[dict]
  Antenna: Optional[dict]
  ErrorStatistics: Optional[dict]
  PFA: dict


class SicdObject(TypedDict):
  version: str
  metadata: Sicd
