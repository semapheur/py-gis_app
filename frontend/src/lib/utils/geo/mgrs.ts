import { UTM, Hemisphere } from "$lib/utils/geo/utm";

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
    this.#zone = zone;
    this.#band = band;
    this.#column = column ?? MGRS.getColumnLetter(zone, easting);
    this.#row = row ?? MGRS.getRowLetter(zone, easting);
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
    UTM.validateZone(zone);

    const band = matches[2].toUpperCase().charAt(0);
    MGRS.validateBand(band);

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
    const hemisphere = MGRS.getHemisphere(this.#band);

    return new UTM(this.#zone, hemisphere, easting, northing);
  }

  public getUTMEasting(): number {
    const columnLetters = MGRS.getColumnLetters(this.#zone);
    const columnIndex = columnLetters.indexOf(this.#column) + 1;
    const e100kNum = columnIndex * 100000.0;

    return e100kNum + this.#easting;
  }

  public getUTMNorthing(): number {
    const rowLetters = MGRS.getRowLetters(this.#zone);
    const rowIndex = rowLetters.indexOf(this.#row) + 1;
    const n100kNum = rowIndex * 100000.0;
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

  public static getHemisphere(band: string) {
    return band < "N" ? Hemisphere.SOUTH : Hemisphere.NORTH;
  }

  public static getColumnLetter(zone: number, easting: number) {
    const column = ~~Math.floor(easting / 100000) % 20;
    const columnLetters = MGRS.getColumnLetters(zone);
    return columnLetters.charAt(column - 1);
  }

  public static getRowLetter(zone: number, northing: number): string {
    const row = ~~Math.floor(northing / 100000) % 20;
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
