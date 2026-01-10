import { UTM } from "$lib/utils/geo/utm";
import { type LatLon } from "$lib/utils/geo/latlon";

const BAND_Y_BAND_TRIALS: Record<string, number[]> = {
  C: [1, 0],
  D: [1, 0],
  E: [1],
  F: [2, 1],
  G: [2],
  H: [3, 2],
  J: [3],
  K: [4, 3],
  L: [4],
  M: [4],
  N: [0],
  P: [0],
  Q: [0, 1],
  R: [1],
  S: [1, 2],
  T: [2],
  U: [2, 3],
  V: [3],
  W: [3, 4],
  X: [3, 4],
};

function bandLatitudeRange(band: string): [number, number] {
  MGRS.validateBand(band);

  const index = band.charCodeAt(0) - "C".charCodeAt(0);
  const min = -80 + index * 8;
  const max = band === "X" ? 84 : min + 8;

  return [min, max];
}

export class MGRS {
  static readonly #columnLetters = ["ABCDEFGH", "JKLMNPQR", "STUVWXYZ"];

  static readonly #rowLetters = [
    "ABCDEFGHJKLMNPQRSTUV",
    "FGHJKLMNPQRSTUVABCDE",
  ];

  static readonly #mgrsPattern =
    /^(\d{1,2})([C-HJ-NP-X])(?:([A-HJ-NP-Z][A-HJ-NP-V])((\d{2}){0,5}))?$/i;
  static readonly #mgrsInvalidPattern = /^3[246]X.*$/;

  readonly #zone: number;
  readonly #band: string;
  readonly #column: string;
  readonly #row: string;
  readonly #easting: number;
  readonly #northing: number;

  constructor(
    zone: number,
    band: string,
    easting: number,
    northing: number,
    column?: string,
    row?: string,
  ) {
    UTM.validateZone(zone);
    MGRS.validateBand(band);

    this.#zone = zone;
    this.#band = band;
    this.#column = column ?? MGRS.getColumnLetter(zone, easting);
    this.#row = row ?? MGRS.getRowLetter(zone, northing);
    this.#easting = easting;
    this.#northing = northing;
  }

  public static parse(mgrs: string): MGRS {
    const mgrsNormalized = mgrs.replaceAll(/\s/g, "");

    const matches = mgrsNormalized.match(MGRS.#mgrsPattern);
    if (!matches) {
      throw new Error(`Invalid MGRS: ${mgrs}`);
    }

    const zone = Number.parseInt(matches[1]);

    const band = matches[2].toUpperCase().charAt(0);

    let squareLetters = matches[3];
    if (!squareLetters) {
      throw new Error(`Parsing for passed format not implemented: ${mgrs}`);
    }

    squareLetters = squareLetters.toUpperCase();

    const column = squareLetters.charAt(0);
    const row = squareLetters.charAt(1);

    const location = matches![4];
    if (location.length === 0) {
      throw new Error(`Parsing for passed format not implemented: ${mgrs}`);
    }

    let easting = 0;
    let northing = 0;

    const precision = location.length / 2;
    const multiplier = Math.pow(10.0, 5 - precision);
    easting = +location.substring(0, precision) * multiplier;
    northing = +location.substring(precision) * multiplier;

    return new MGRS(zone, band, easting, northing, column, row);
  }

  public toUTM() {
    const easting = this.getUTMEasting();
    const northing = this.getUTMNorthing();
    const hemisphere = UTM.getHemisphere(this.#band);

    return new UTM(this.#zone, hemisphere, easting, northing);
  }

  public getUTMEasting(): number {
    const columnLetters = MGRS.getColumnLetters(this.#zone);
    const columnIndex = columnLetters.indexOf(this.#column);
    const e100kNum = (columnIndex + 1) * 100000.0;

    return e100kNum + this.#easting;
  }

  public getUTMNorthing(): number {
    const rowLetters = MGRS.getRowLetters(this.#zone);
    const rowIndex = rowLetters.indexOf(this.#row);
    let n100kNum = rowIndex * 100000.0;

    const trials = BAND_Y_BAND_TRIALS[this.#band];
    if (trials.length === 1) {
      return trials[0] * 2000000 + n100kNum + this.#northing;
    }

    const bandSouthLatitude = bandLatitudeRange(this.#band)[0];
    const bandNorthing = UTM.fromGeographic(0, bandSouthLatitude).northing;

    const nBand = Math.floor(bandNorthing / 100000) * 100000;

    let n2M = 0;

    while (n2M + n100kNum + this.#northing < nBand) {
      n2M += 2000000;
    }

    return n2M + n100kNum + this.#northing;
  }

  public toLatLon(): LatLon {
    return this.toUTM().toLatLon();
  }

  public static validateBand(letter: string) {
    const letterCode = letter.charCodeAt(0);
    const omittedLetters = "IO";
    if (
      letterCode < "C".charCodeAt(0) ||
      letterCode > "X".charCodeAt(0) ||
      omittedLetters.includes(letter)
    ) {
      throw new Error(`Invalid band letter (CDEFGHJKLMNPQRSTUVWX): ${letter}`);
    }
  }

  public static getColumnLetter(zone: number, easting: number) {
    const column = Math.floor(easting / 100000);
    const columnLetters = MGRS.getColumnLetters(zone);
    return columnLetters.charAt(column - 1);
  }

  public static getRowLetter(zone: number, northing: number): string {
    const row = Math.floor(northing / 100000) % 20;
    const rowLetters = MGRS.getRowLetters(zone);
    return rowLetters.charAt(row);
  }

  private static getColumnLetters(zone: number): string {
    return MGRS.#columnLetters[(zone - 1) % 3];
  }

  private static getRowLetters(zone: number): string {
    return MGRS.#rowLetters[(zone - 1) % 2];
  }
}
