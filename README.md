{'type': 'Polygon', 'coordinates': [[[8.51465933370227, 48.94427064678439], [14.73907893003144, 48.94427064678439], [14.73907893003144, 52.87026742245655], [8.51465933370227, 52.87026742245655], [8.51465933370227, 48.94427064678439]]]}


# National imagery transmission format (NTIF)

[MIL-STD-2500C](https://nsgreg.nga.mil/doc/view?i=4324)

# Synthetic aperture radar

Single Look Complex (SLC)
Ground Range Detected (GRD)

## Sensor Independent Complex Data (SICD)

[NGA.STND.0024-1](https://nsgreg.nga.mil/doc/view?i=4900)

File naming convention: IMG-<Polarization>-<Scene ID>-<Product ID>-SICD.nitf

Scene ID = AAAAA-YYYYMMDDThhmmssZ
- AAAAAA: Satellite type
- YYYYMMDD: Scene center observation date (YYYY: year, MM: month, DD: day)
- hhmmss: Scene center observation time* (hh: hour, mm: minutes, ss: seconds)

Product ID = DDEEE
- DD: Observation mode (SL: Sliding Spotlight mode, SM: Stripmap mode)
- EEE: Processing level (SLC: Single Look Complex)

### XML metadata

| Type | Meaning |
| --- | --- |
| TXT | Value is a string of characters |
| ENU | Value can be a string of characters or an integer. There is a certain allowed set of character strings or integer values. |
| BOOL | Value is a Boolean type. The Boolean type is used to specify true or false. |
| INT | Value is an integer. It may be a positive or negative value with an optional positive sign (“+”) when positive |
| DBL | Value is a real-valued decimal (base 10) number that when converted to binary format should be converted to a 64 bit floating point type (e.g. IEEE binary64 floating point). It may be a positive or negative value with an optional positive sign (“+”) when positive. The value is represented in the scientific notation (The E23.7 notation) with 16 digits of precision. |
| XDT | Value represents the dateTime XML type |
| RC | Identifies a parent tag that consists of a required row and column component. The values of each component are integers. |
| CMPLX | Identifies a parent tag that consists of a required real and imaginary component. The values of each component are floating point type. |
| XYZ | Identifies a parent tag that consists of a x, y and z component. |
| LLH | Identifies a parent tag that consists of a geodetic latitude, longitude and height above ellipsoid component. The values of each component are floating point type. |
| LL | Identifies a parent tag that consists of a geodetic latitude and longitude component. The values of each component are floating point type. |
| POLY | Identifies a parent tag that consists of a set of coefficients for a one-dimensional polynomial function. The values of each component are floating point type. |
| 2D_POLY | Identifies a parent tag that consists of a set of coefficients for a two-dimensional polynomial function. The values of each component are floating point type. |
| XYZ_POLY | Identifies a parent tag that consists of a x, y and z component. Each component is a POLY type. |

#### Collection and image creation information parameters

| Field Name | Req/Opt | Type | Description | Units | Rpt | Attributes / Allowed Values |
| --- | --- | --- | --- | --- | --- | --- |
| **SICD.CollectionInfo** | R | – | Block with general info about the collection | – | N | – |
| SICD.CollectionInfo.CollectorName | R | TXT | Radar platform identifier (receive platform for bistatic) | – | N | – |
| SICD.CollectionInfo.IlluminatorName | O | TXT | Transmit platform identifier (for bistatic collections) | – | N | – |
| SICD.CollectionInfo.CoreName | R | TXT | Collection & imaging dataset identifier | – | N | – |
| SICD.CollectionInfo.CollectType | O | ENU | Collection type identifier | – | N | Allowed: `MONOSTATIC`, `BISTATIC` |
| **SICD.CollectionInfo.RadarMode** | R | – | – | – | N | – |
| SICD.CollectionInfo.RadarMode.ModeType | R | ENU | Radar imaging mode | – | N | Allowed: `SPOTLIGHT`, `STRIPMAP`, `DYNAMIC STRIPMAP` |
| SICD.CollectionInfo.RadarMode.ModeID | O | TXT | Program-specific radar mode ID | – | N | – |
| SICD.CollectionInfo.Classification | R | TXT | Banner including classification & handling markings | – | N | Default: `UNCLASSIFIED` |
| SICD.CollectionInfo.CountryCode | O | TXT | List of country codes covered by image | – | Y | – |
| SICD.CollectionInfo.Parameter | O | TXT | Free-form parameter field | ~ | Y | `name="xxx"` |
| **SICD.ImageCreation** | O | – | General info about image creation | – | N | – |
| SICD.ImageCreation.Application | O | TXT | Name & version of creation application | – | N | – |
| SICD.ImageCreation.DateTime | O | XDT | UTC timestamp of image creation | – | N | – |
| SICD.ImageCreation.Site | O | TXT | Location where product was created | – | N | – |
| SICD.ImageCreation.Profile | O | TXT | Profile used for creation | – | N | – |

#### Image data parameters

| Field Name | Req/Opt | Type | Description | Units | Rpt | Attributes / Allowed Values |
| --- | --- | --- | --- | --- | --- | --- |
| **SICD.ImageData** | R | – | Block describing image pixel data | – | N | – |
| SICD.ImageData.PixelType | R | ENU | Pixel type and binary format | – | N | Allowed: `RE32F_IM32F`, `RE16I_IM16I`, `AMP8I_PHS8I` |
| SICD.ImageData.AmpTable | O | – | Amplitude LUT for `AMP8I_PHS8I` | – | N | `size="256"` |
| SICD.ImageData.Amplitude | R | DBL | Amplitude table entries | – | Y | `index="0"`–`"255"` |
| SICD.ImageData.NumRows | R | INT | Rows in product | – | N | – |
| SICD.ImageData.NumCols | R | INT | Columns in product | – | N | – |
| SICD.ImageData.FirstRow | R | INT | Global index of first row | – | N | – |
| SICD.ImageData.FirstCol | R | INT | Global index of first column | – | N | – |
| **SICD.ImageData.FullImage** | R | – | Describes original full image | – | N | – |
| SICD.ImageData.FullImage.NumRows | R | INT | Rows in full image | – | N | – |
| SICD.ImageData.FullImage.NumCols | R | INT | Columns in full image | – | N | – |
| SICD.ImageData.SCPPixel | R | RC | SCP pixel global row & col | – | N | – |
| **SICD.ImageData.ValidData** | O | – | Polygon enclosing valid data | – | N | `size=NumVertices` |
| SICD.ImageData.ValidData.Vertex | R | RC | Polygon vertices | – | Y | `index="1"`–`"x"` |

#### Image geographic reference parameters

| Field Name | Req/Opt | Type | Description | Units | Rpt | Attributes / Allowed Values |
| --- | --- | --- | --- | --- | --- | --- |
| **SICD.GeoData** | R | – | Geographic coverage of image | – | N | – |
| SICD.GeoData.EarthModel | R | ENU | Earth model used for lat/lon/height | – | N | – |
| **SICD.GeoData.SCP** | R |  | Scene Center Point (SCP) in full (global) image. This is the precise location | - | N |  |
| SICD.GeoData.SCP.ECH | R | XYZ | Scene Center Point position in ECF coordinates. | m | N |  |
| SICD.GeoData.SCP.LLH | R | LLH | Scene Center Point geodetic latitude, longitude and height | dd</br>dd</br> | N |  |
| **SICD.GeoData.ImageCorners** | R |  | Image corners points projected to the ground/surface level  | - | N |  |
| SICD.GeoData.ImageCorners.ICP | R | LL | Image Corner Point (ICP) data for the 4 corners in product. ICPs indexed x = 1, 2, 3, 4, clockwise.</br>x = 1 <-> First row, First column</br>x = 2 <-> First row, Last column</br>x = 3 <-> Last row, Last column</br>x = 4 <-> Last row, First column | dd | Y | index = `1:FRFC` or `2:FRLC` or `3:LRLC` or `4:LRFC` |
| **SICD.GeoData.ValidData** | O | – | Indicates valid + zero-filled pixel region | – | N | `size=NumVertices` |
| SICD.GeoData.ValidData.Vertex | R | LL | Ground-projected valid-data vertices | dd | Y | Lat: –90°–90°, Lon: –180°–180°, `index=1..x` |
| **SICD.GeoData.ValidData.GeoInfo** | O | – | Describes geographic features | – | Y | `name="xxx"` |
| SICD.GeoData.ValidData.Desc | O | TXT | Description of geographic feature | – | Y | `name="xxx"` |
| SICD.GeoData.ValidData.Point | O | LL | A single geolocated point | dd | N | – |
| **SICD.GeoData.GeoInfo.Line** | O | – | Linear feature with endpoints | – | N | `size=NumEndpoints` |
| SICD.GeoData.GeoInfo.Endpoint | R | LL | Endpoints of line segments | dd | Y | `index="x"` |
| **SIDC.GeoData.GeoInfo.Polygon** | O | – | Polygon area | – | N | `size=NumVertices` |
| SICD.GeoData.GeoInfo.Vertex | R | LL | Polygon corner vertices indexed clockwise | dd | Y | `index="x"` |


#### Image grid parameters

- RGAZIM: Grid for a simple range, Doppler image. Also, the natural grid for images formed with the Polar Format Algorithm
- RGZERO: A grid for images formed with the Range Migration Algorithm. Used only for imaging near closest approach (i.e. near zero Doppler).
- XRGYCR: Orthogonal slant plane grid oriented range and cross range relative to the ARP at a reference time.
- XCTYAT: Orthogonal slant plane grid with X oriented cross track.
- PLANE: Uniformly sampled in an arbitrary plane along directions U & V.

| Field Name | Req/Opt | Type | Description | Units | Rpt | Attributes / Allowed Values |
| --- | --: | --- | --- | --: | --: | --- |
| **SICD.Grid** | R | — | This block of parameters describes the image sample grid. | - | N | - |
| SICD.Grid.ImagePlane | R | ENU | Defines the type of image plane that best describes the sample grid (precise plane defined by Row & Column unit vectors). | - | N | Allowed: “GROUND”, “SLANT”, “OTHER” |
| SICD.Grid.Type | R | ENU | Type of spatial sampling grid represented by the image sample grid (row, col order). | - | N | Allowed: “RGAZIM”, “RGZERO”, “XRGYCR”, “XCTYAT”, “PLANE” |
| SICD.Grid.TimeCOAPoly | R | 2D_POLY | Time of Center Of Aperture (t_COA) polynomial as function of image coordinates (row = var1, col = var2). Coef(0,0) is SCP COA time. | s, s/m, s/m², ... | N | order1 = “M”, order2 = “N” |
| **Row direction parameters (increasing row index)** | | | | | | |
| SICD.Grid.Row | R | — | Parameters describing increasing **row** direction image coordinate. | - | N | - |
| SICD.Grid.Row.UVectECF | R | XYZ | Unit vector in increasing row direction (ECF) at SCP. | - | N | - |
| SICD.Grid.Row.SS | R | DBL | Sample spacing in the increasing row direction (precise spacing at SCP). | m | N | - |
| SICD.Grid.Row.ImpRespWid | R | DBL | Half-power impulse response width in the row direction at SCP. | m | N | - |
| SICD.Grid.Row.Sgn | R | ENU | Integer sign of exponent in DFT to transform row → spatial frequency (Krow). | - | N | Allowed: “-1”, “+1” |
| SICD.Grid.Row.ImpRespBW | R | DBL | Spatial bandwidth in Krow used to form the impulse response at SCP. | cyc/m | N | - |
| SICD.Grid.Row.KCtr | R | DBL | Center spatial frequency in Krow (zero frequency of DFT in row direction). | cyc/m | N | - |
| SICD.Grid.Row.DeltaK1 | R | DBL | Minimum row offset from KCtr of spatial frequency support. | cyc/m | N | - |
| SICD.Grid.Row.DeltaK2 | R | DBL | Maximum row offset from KCtr of spatial frequency support. | cyc/m | N | - |
| SICD.Grid.Row.DeltaKCOAPoly | O | 2D_POLY | Offset from KCtr of center of support in row spatial frequency (function of row & col). | cyc/m, */m², ... | N | order1 = “M”, order2 = “N” |
| SICD.Grid.Row.WgtType | O | TXT | Aperture weighting type applied in Krow to yield row impulse response. | - | N | - |
| SICD.Grid.Row.WindowName | R (when WgtType used) | TXT | Type/name of aperture weighting (examples: “UNIFORM”, “TAYLOR”, “HAMMING”, “UNKNOWN”). | - | N | - |
| SICD.Grid.Row.Parameter | O | TXT | Free-format field for weighting parameter information. | - | Y | name="xxx" |
| SICD.Grid.Row.WgtFunct | O | — | Sampled aperture amplitude weighting function in Krow. Attribute size = number of weights (NW). | - | N | size = “x” |
| SICD.Grid.Row.Wgt (child) | R (inside WgtFunct) | DBL | The sampled amplitude values that span ImpRespBW. Index n = 1..NW. | - | Y | index = “x” |
| **Column direction parameters (increasing column index)** | | | | | | |
| SICD.Grid.Col | R | — | Parameters describing increasing **column** direction image coordinate. | - | N | - |
| SICD.Grid.Col.UVectECF | R | XYZ | Unit vector in increasing column direction (ECF) at SCP. | - | N | - |
| SICD.Grid.Col.SS | R | DBL | Sample spacing in increasing column direction (precise at SCP). | m | N | - |
| SICD.Grid.Col.ImpRespWid | R | DBL | Half-power impulse response width in column direction at SCP. | m | N | - |
| SICD.Grid.Col.Sgn | R | ENU | Integer sign of exponent in DFT to transform column → Kcol. | - | N | Allowed: “-1”, “+1” |
| SICD.Grid.Col.ImpRespBW | R | DBL | Spatial bandwidth in Kcol used to form column impulse response. | cyc/m | N | - |
| SICD.Grid.Col.KCtr | R | DBL | Center spatial frequency in Kcol (zero freq of DFT in col direction). | cyc/m | N | - |
| SICD.Grid.Col.DeltaK1 | R | DBL | Minimum column offset from KCtr of spatial frequency support. | cyc/m | N | - |
| SICD.Grid.Col.DeltaK2 | R | DBL | Maximum column offset from KCtr of spatial frequency support. | cyc/m | N | - |
| SICD.Grid.Col.DeltaKCOAPoly | O | 2D_POLY | Offset from KCtr of center of support in Kcol (function of row & col). | cyc/m, */m², ... | N | order1 = “M”, order2 = “N” |
| SICD.Grid.Col.WgtType | O | TXT | Aperture weighting type in Kcol to yield column impulse response. | - | N | - |
| SICD.Grid.Col.WindowName | R (when WgtType used) | TXT | Type/name of aperture weighting. | - | N | Example: “UNIFORM”, “TAYLOR”, “HAMMING”, “UNKNOWN” |
| SICD.Grid.Col.Parameter | O | TXT | Free-format weighting parameter info. | - | Y | name="xxx" |
| SICD.Grid.Col.WgtFunct | O | — | Sampled aperture amplitude weighting in Kcol. Attribute size = NW. | - | N | size = “x” |
| SICD.Grid.Col.Wgt (child) | R (inside WgtFunct) | DBL | Sampled amplitude values; weights indexed n = 1..NW. | - | Y | index = “x” |

#### Collection timeline parameters

| Field Name | Req/Opt | Type | Description | Units | Rpt | Attributes |
| --- | --: | --- | --- | ---: | --: | --- |
| SICD.Timeline | R | — | Block describing the imaging collection timeline. | - | N | - |
| SICD.Timeline.CollectStart | R | XDT | Collection date and start time (UTC). Time reference for slow time t=0. | - | N | - |
| SICD.Timeline.CollectDuration | R | DBL | Duration of collection period. | sec | N | - |
| SICD.Timeline.IPP | O | — | Inter-Pulse Period (IPP) parameters. Attribute size = number of IPP sets. | - | N | size = “x” |
| SICD.Timeline.IPP.Set | O (at least 1) | — | Identifies set x of IPP parameters (indexed). | - | Y | index = “x” |
| SICD.Timeline.IPP.Set.IPPVal | R (within Set) | DBL / POLY etc | (various IPP-related parameters exist per Set; see doc for full list) | sec, sec/m, etc | N | — |

#### Reference position parameters

| Field Name | Req/Opt | Type | Description | Units | Rpt | Attributes |
| --- | --: | --- | --- | ---: | --: | --- |
| SICD.Position | R | — | Block of platform & reference positions in ECF vs time (ARP, GRP, Tx/Rx phase centers optional). | - | N | - |
| SICD.Position.ARP | R | XYZ_POLY / XYZ | Aperture Reference Point ECF position (possibly polynomial over time). | m | N | order attributes if POLY |
| SICD.Position.ARP.Vel | O | XYZ_POLY / XYZ | ARP velocity vs time. | m/s | N | - |
| SICD.Position.GRP | O | XYZ | Ground Reference Point ECF position. | m | N | - |
| SICD.Position.Parameters | O | — | Optional per-transmit/receive phase center positions & names. | - | Y | name="xxx" |

#### Radar collection parameters

| Field Name | Req/Opt | Type | Description | Units | Rpt | Attributes / Allowed Values |
| --- | --: | --- | --- | --: | --: | --- |
| SICD.RadarCollection | R | — | Parameters that describe the imaging collection (area, resolutions, waveforms, channels). | - | N | - |
| SICD.RadarCollection.RefFreqIndex | O | INT | Index indicating reference frequencies used (to express frequencies as offsets). | - | Y | index integer |
| SICD.RadarCollection.TxFrequency.Min | R | DBL | Minimum transmit frequency in product (may be offset if RefFreqIndex used). | Hz | N | - |
| SICD.RadarCollection.TxFrequency.Max | R | DBL | Maximum transmit frequency. | Hz | N | - |
| SICD.RadarCollection.ReceiveChannels | R | — | Receive channel descriptions (NumChan, Pol, etc). | - | Y | index="x" |
| SICD.RadarCollection.NumChan | R | INT | Number of receive channels. | - | N | - |
| SICD.RadarCollection.TxRcvPolarization | R | ENU | Combined Tx/Rcv polarization(s) for the collection. | - | N | Allowed values (expanded in doc) |
| SICD.RadarCollection.Waveform (child block) | O | — | Waveform parameters (pulse length, bandwidth, linear FM params). | sec, Hz, etc | Y | NumWaveforms attribute |

#### Image formation parameters

| Field Name | Req/Opt | Type | Description | Units | Rpt | Attributes / Allowed Values |
| --- | --: | --- | --- | ---: | --: | --- |
| SICD.ImageFormation | R | — | Image formation processing parameters describing what was processed and algorithms applied. | - | N | - |
| SICD.ImageFormation.NumChanProc | O | INT | Number of receive channels processed to form the image. | - | N | - |
| SICD.ImageFormation.TxRcvPolarizationProc | O | ENU | Combined Tx/Rcv polarization for the processed image. | - | N | allowed values updated in v1.2.1 |
| SICD.ImageFormation.ImageFormAlgo | R | ENU | Image formation algorithm used. | - | N | “RGAZCOMP”, “PFA”, “RMA” |
| SICD.ImageFormation.STBeamComp | O | BOOL | Slow Time Beam Compensation flag (whether beamshape compensation applied). | - | N | true/false |
| SICD.ImageFormation.PRFScaleFactor | O | DBL | PRF scale factor if effective PRF differs from true PRF. | - | N | - |

#### SCP center of aperture parameters

| Field Name | Req/Opt | Type | Description | Units | Rpt | Attributes |
| --- | --: | --- | --- | --: | --: | --- |
| SICD.SCP | R | — | Block describing Center-Of-Aperture (COA) time & geometry for the Scene Center Point. | - | N | - |
| SICD.SCP.ARPPos | R | XYZ | ARP position at SCP COA (ECF). | m | N | - |
| SICD.SCP.ARPVel | R | XYZ | ARP velocity at SCP COA. | m/s | N | - |
| SICD.SCP.SideOfTrack | R | ENU | Imaging side of track indicator. | - | N | - |
| SICD.SCP.Range | R | DBL | Range to the SCP from ARP at COA. | m | N | - |

#### Radiometric parameters

| Field Name | Req/Opt | Type | Description | Units | Rpt | Attributes |
| --- | --: | --- | --- | --: | --: | --- |
| SICD.Radiometric | O | — | Radiometric parameters for converting pixel power to reflectivity (σ0, RCS, clutter reflectivity). | - | N | - |
| SICD.Radiometric.NoiseLevel | O | DBL | Noise power level parameters (may include noise floor, noise estimate). | dB | N | - |
| SICD.Radiometric.TargetRCSSF | O | DBL | Target RCS scale factor for converting pixel power to RCS. | - | N | - |
| SICD.Radiometric.ClutterSF | O | DBL | Clutter reflectivity scale factors (σ0 scale). | - | N | - |

#### Antenna parameters

| Field Name | Req/Opt | Type | Description | Units | Rpt | Attributes |
| --- | --: | --- | --- | --: | --: | --- |
| SICD.Antenna | O | — | Transmit & receive antenna pattern description; supports 2-way effective pattern for monostatic ops. | - | N | - |
| SICD.Antenna.TwoWayPattern | O | — | Two-way antenna pattern parameters (orientation, mainlobe pointing, beam shape vs time). | - | N | - |
| SICD.Antenna.OneWayPattern | O | — | One-way transmit/receive patterns when provided separately. | - | N | - |
| SICD.Antenna.Orientation | O | XYZ | Antenna orientation vectors or angles. | deg, rad | N | - |


### Po
ARPPos: Antenna reference point position

ground_range_resolution
ground_azimuth_resolution
look_angle
incidence_angle
look_azimuth


# Tips

## Convert georeferenced rasters

```cmd
gdal_translate -of NITF "path/to/input/rater" "path/to/output/raster.ntf"
```
