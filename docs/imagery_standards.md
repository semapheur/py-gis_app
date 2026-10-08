# National imagery transmission format (NITF)

[MIL-STD-2500C](https://nsgreg.nga.mil/doc/view?i=4324)

## File header definition

Type: R = Required, C = Conditional, <R> = BCS spaces allowed for the entire field.

| Field | Name/Description | Size (bytes) | Value Range | Type | Comment |
|---|---|---|---|---|---|
| FHDR | File Profile Name | 4 | BCS-A “NITF” | R | Per Joint BIIF Profile (JBP) |
| FVER | File Version | 5 | BCS-A “02.10” | R | NITF Version 2.1 |
| CLEVEL | Complexity Level | 2 | BCS-A 03, 05, 06, 07 or 09 | R | Per JBP Annex G Table G-1 |
| STYPE | Standard Type | 4 | BCS-N “BF01” | R | Fixed value |
| OSTAID | Originating Station ID | 10 | BCS-A | R | Per the Product Specific Implementation Document; meaningful value; shall not be filled with BCS spaces (0x20) |
| FDT | File Date and Time | 14 | BCS-N CCYYMMDDhhmmss | R | File creation UTC date and time |
| FTITLE | File Title | 80 | ECS-A | <R> | Use product specific guidance if available |
| Security Tags | Use “FS” prefix for Tag | 167 | As defined in Table 2-2 | R | |
| FSCOP | File Copy Number | 5 | BCS-N | R | Not tracked per JBP; 00000 = no tracking of numbered file copies |
| FSCPYS | File Number of Copies | 5 | BCS-N | R | Not tracked per JBP; 00000 = no tracking of numbered file copies |
| ENCRYP | Encryption | 1 | BCS-N 0 | R | No Encryption |
| FBKGC | File Background Color | 3 | Unsigned binary integer; Default: 000 (0x00, 0x00, 0x00) | R | Default background color is black |
| ONAME | Originator’s Name | 24 | ECS-A; 24 ECS characters | <R> | Per the Product Specific Implementation Document |
| OPHONE | Originator’s Phone | 18 | ECS-A; 24 ECS characters | <R> | Per the Product Specific Implementation Document |
| FL | File Length | 12 | BCS-N | R | Number of bytes; Generate |
| HL | NITF File Header Length | 6 | BCS-N | R | Number of bytes in the header; Generate |
| NUMI | Number of Image Segments | 3 | BCS-N 001 to 999 | R | See Sections 2.4.2 and 2.4.3 |
| LISHn | Length of Image Sub-Header | 6 | BCS-N 000439 to 9999998 | C | Per JBP; Generate. Repeats as specified by NUMI |
| LIn | Length of nth Image Segment | 10 | BCS-N 0000000001 to 9999999998 | C | See Sections 2.4.2 and 2.4.3; Generate |
| NUMS | Number of graphic Segments | 3 | BCS-N 000 to 999 | R | Graphics segments |
| NUMX | Reserved | 3 | BCS-N 000 | R | Reserved |
| NUMT | Number of Text Segments | 3 | BCS-N 000 to 999 | R | Text segments |
| NUMDES | Number of data Extension Segments | 3 | BCS-N 001 to 999 | R | # product images + # input SICDs + remaining DES segments |
| LDSHn | Length of nth Data Extension Segment Sub-Header | 4 | BCS-N 0200 to 9998 | C | Length in bytes |
| LDn | Length of Data Extension Segment | 9 | BCS-N 000000001 to 999999998 | C | Length in bytes |
| NUMRES | Number of Reserved | 3 | BCS-N 000 | R | Not used |
| UDHDL | User-Defined Header Data Length | 5 | BCS-N 00000; 00003 + length of TREs | R | No TREs specified but use of TREs not prohibited |
| UDHOFL | User-Defined Header Overflow | 3 | BCS-N 000-999; Default 000 | C | If UDHDL = 00000 then omit field |
| UDHD | User-Defined Header Data | Equal to UDHDL minus 3 | User Defined | C | If UDHDL = 00000 then omit field |
| XHDL | Extended Header Data Length | 5 | BCS-N 00000; 00003 + length of TREs | R | No TREs specified but use of TREs not prohibited |
| XHDLOFL | Extended Header Data Overflow | 3 | BCS-N 000-999; Default 000 | C | If XHDL = 00000 then omit field|
| XHD | Extended Header Data | Equal to XHDL minus 3 | User Defined | C | If XHDL = 00000 then omit field |

## Image sub-header definition

| Field | Name/Description | Size (bytes) | Value Range | Type | Comment |
|---|---|---|---|---|---|
| IM | File Part Type | 2 | BCS-A: IM | R | |
| IID1 | Image Identifier 1 | 10 | BCS-A: SIDDmmmnnn or DED001 | R | mmm = product image number; nnn = segment number, starting at 001 |
| IDATIM | Image Date and Time | 14 | BCS-N: CCYYMMDDhhmmss | R | Equivalent to first SIDD.AdvancedExploitation.Collection.Information.CollectionDateTime |
| TGTID | Target Identifier | 17 | BCS-A | <R> | Blank |
| IID2 | Image Identifier 2 | 80 | — | <R>  | Additional image identification information |
| Security  | Use “IS” prefix for Tag | 167 | As defined in Table 2-2 | R | |
| ENCRYP | Encryption | 1 | BCS-N: 0 | R | 0 = not encrypted |
| ISORCE | Image Source | 42 | ECS-A; Collector Name | R | Equivalent to SIDD AdvancedExploitation.Collection.Information.SensorName |
| NROWS | Number of Significant Rows in Image | 8 | BCS-N: 00000001–9999999 | R | See Section 2.4.2 |
| NCOLS | Number of Significant Columns in Image | 8 | BCS-N: 00000001–9999999 | R | See Section 2.4.2 |
| PVTYPE | Pixel Value Type | 3 | BCS-A: INT, SI | R | SI for DED; INT for all others |
| IREP | Image Representation | 8 | BCS-A: MONO, RGB/LUT, RGB, NODISPLY | R | NODISPLY for DED |
| ICAT | Image Category | 8 | BCS-A: SAR, LEG, DED | R | SAR = Synthetic Aperture Radar; LEG = Legend; DED = Digital Elevation Data |
| ABPP | Actual Bits-Per-Pixel Per Band | 2 | BCS-N: 08 or 16 | R | See Table 2-6 |
| PJUST | Pixel Justification | 1 | BCS-A: R | R | |
| ICORDS | Image Coordinate Representation | 1 | BCS-A: G or blank | <R> | G for geographic; blank for legend segments |
| IGEOLO | Image Geographic Location | 60 | BCS-A | C | If ICORDS = G: four latitude/longitude corner pairs |
| NICOM | Number of Image Comments | 1 | BCS-N: 0–9 | R | Followed by ICOMn fields when nonzero |
| ICOMn | Image Comment n | 80 | ECS-A | C | User defined |
| IC | Image Compression | 2 | BCS-A: NC, C8, M8 | R | NC = no compression; C8 = JPEG 2000; M8 = JPEG 2000 mask-image compression |
| COMRAT | Compression Rate Code | 4 | BCS-A: Nxyz, Vxyz, wxyz | C | Included if IC = C8 or M8; xyz indicates expected/target bit rate |
| NBANDS | Number of Bands | 1 | BCS-N: 1, 3 | R | See Section 2.4.1 |
| IREPBANDn | nth Band Representation | 2 | BCS-A: LU, M, R, G, B, or BCS spaces | <R> | See Section 2.4.1 |
| ISUBCATn | nth Band Subcategory | 6 | BCS-A: spaces | <R>  | |
| IFCn | nth Band Image Filter Condition | 1 | BCS-A: N | R | |
| IMFLTn | nth Band Standard Image Filter Code | 3 | BCS-A: spaces | <R> | |
| NLUTSn | Number of LUTs for nth Image Band | 1 | BCS-N: 0–3 | R | See Table 2-6 |
| NELUTn | Number of LUT Entries for nth Image Band | 5 | BCS-N: 00001–65536 | C | Omitted if NLUTSn = 0 |
| LUTDnm | nth Image Band, mth LUT | NELUTn | Unsigned binary integer; LUT values  | C | Repeats NLUTSn times; omitted when NLUTSn = 0 |
| ISYNC | Image Sync code | 1 | BCS-N: 0 | R | |
| IMODE | Image Mode | 1 | BCS-A: B or P | R | If IREP = RGB, P; B otherwise. B = Band Interleaved by Block; P = Band Interleaved by Pixel |
| NBPR | Number of Blocks Per Row | 4 | BCS-N: 0001–9999 | R | |
| NBPC | Number of Blocks Per Column | 4 | BCS-N: 0001–9999 | R | |
| NPPBH | Number of Pixels Per Block Horizontal | 4 | BCS-N: 0001–8192 or 0000 | R | If >8192, populate 0000; otherwise zero-padded number of columns |
| NPPBV | Number of Pixels Per Block Vertical | 4 | BCS-N: 0001–8192 or 0000 | R | If >8192, populate 0000; otherwise zero-padded number of rows |
| NBPP | Number of Bits Per Pixel Per Band | 2 | BCS-N: 08 or 16 | R | See Table 2-6 |
| IDLVL | Image Display Level | 3 | BCS-N: 001–999 | R | See segmentation rules |
| IALVL | Attachment Level | 3 | BCS-N: 000–998 | R | See segmentation rules |
| ILOC | Image Location | 10 | BCS-N: RRRRRCCCCC | R | Location of first pixel; positive/negative row and column offsets |
| IMAG | Image Magnification | 4 | BCS-A | R | Default 1.0 |
| UDIDL | User Defined Image Data Length | 5 | BCS-N: 00000 or 00003 + TRE length | R | No TREs specified, but TRE use not prohibited |
| UDOFL | User-Defined Overflow | 3 | BCS-N: 000–999 | C | Omit if UDIDL = 00000 |
| UDID | User-Defined Image Data |  Equal to UDIDL minus 3 | User Defined | C | Omit if UDIDL = 00000 |
| IXSHDL | Image Extended Sub-Header Data Length | 5 | BCS-N: 00000 or 00003 + TRE length | R | No TREs specified, but TRE use not prohibited |
| IXSOFL | Image Extended Sub-Header Overflow | 3 | BCS-N: 000–999 | C | Omit if IXSHDL = 00000 |
| IXSHD | Image Extended Sub-Header Data | Equal to IXSHDL minus 3 | User Defined | C | Omit if IXSHDL = 00000 |

## Security fields

The `xx` prefix is replaced by `FS` for the File Header, `IS` for the Image Sub-Header, and `DES` for the DES.

| Base Field | Name/Description | Size (bytes) | Value Range | Type |
|---|---|---|---|---|
| xxCLAS| File Security Classification. Valid values: T (Top Secret), S (Secret), C (Confidential), R (Restricted), U (Unclassified). | 1 | ECS-A; “U” or per Program Specific Implementation Document | R |
| xxCLSY | File Security Classification System. National/multinational security system; country codes per FIPS PUB 10-4. “XN” identifies classified data generated using NATO security system marking guidance. All ECS spaces implies no classification system applies. | 2 | ECS-A; default ECS spaces (0x20) | <R> |
| xxCODE | File Codewords. Valid indicator of security compartments; digraphs from NITF Field Value Registry, separated by ECS spaces. All ECS spaces implies no codewords. | 11 | BCS-A; default BCS spaces (0x20) | <R> |
| xxCTLH | File Control and Handling. Additional security controls/handling instructions (caveats) using digraphs from the NITF Field Value. | 2 | ECS-A; default ECS spaces (0x20) | <R> |
| xxREL | File Releasing Instructions. Country and/or multilateral entity codes authorized for release, separated by ECS spaces. | 20 | ECS-A; default ECS spaces (0x20) | <R> |
| xxDCTP | File Declassification Type. DD, DE, GD, GE, O, X. | 2 | ECS-A; DD, DE, GD, GE, O, X | <R> |
| xxDCDT | File Declassification Date. Date on which file is declassified when DCTP is DD. | 8 | ECS-A; CCYYMMDD | <R> |
| xxDCXM | File Declassification Exemption. Reason for exemption when DCTP is X. | 4 | ECS-A; X1–X8, X251–X259 | <R> |
| xxDG | File Downgrade. Classification level to which file is downgraded when DCTP is GD or GE. |            1 | ECS-A; S, C, R | <R> |
| xxDGDT | File Downgrade Date. Date on which file is downgraded when DCTP is GD. | 8 | ECS-A; CCYYMMDD | <R> |
| xxCLTX | File Classification Text. Additional information about classification, declassification/downgrading events, multiple sources, or special handling rules. | 43 | ECS-A; free text | <R> |
| xxCATP | File Classification Authority Type. O = original classification authority; D = derivative from a single source; M = derivative from multiple sources. | 1 | ECS-A; O, D, M | <R> |
| xxCAUT | File Classification Authority. Identifies classification authority according to xxCATP; user-defined free text. | 40 | ECS-A; free text | <R> |
| xxCRSN | File Classification Reason. Reason for classification corresponding to E.O. 12958 §1.5(a)-(g). | 1 | ECS-A; A–G | <R> |
| xxSRDT | File Security Source Date. Date of source used to derive classification; for multiple sources, most recent source. | 8 | ECS-A; CCYYMMDD | <R> |
| xxCTLN | File Security Control Number. Security control number associated with the file. | 15 | ECS-A; per applicable security regulations | <R> |

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
