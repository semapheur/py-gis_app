export enum Hemisphere {
  NORTH,
  SOUTH,
}

export class UTM {
  readonly #zone: number;
  readonly #hemisphere: Hemisphere;
  readonly #easting: number;
  readonly #northing: number;

  static readonly #utmPattern =
    /^(\d{1,2})\s*([N|S])\s*(\d+\.?\d*)\s*(\d+\.?\d*)$/i;

  constructor(
    zone: number,
    hemisphere: Hemisphere,
    easting: number,
    northing: number,
  ) {
    this.#zone = zone;
    this.#hemisphere = hemisphere;
    this.#easting = easting;
    this.#northing = northing;
  }

  public toPoint(): Point {
    let north = this.#northing;
    if (this.#hemisphere === Hemisphere.SOUTH) {
      // Remove 10,000,000 meter offset used for southern hemisphere
      north -= 10000000.0;
    }

    let latitude =
      ((north / 6366197.724 / 0.9996 +
        (1 +
          0.006739496742 * Math.pow(Math.cos(north / 6366197.724 / 0.9996), 2) -
          (0.006739496742 *
            Math.sin(north / 6366197.724 / 0.9996) *
            Math.cos(north / 6366197.724 / 0.9996) *
            (Math.atan(
              Math.cos(
                Math.atan(
                  (Math.exp(
                    ((this.#easting - 500000) /
                      ((0.9996 * 6399593.625) /
                        Math.sqrt(
                          1 +
                            0.006739496742 *
                              Math.pow(
                                Math.cos(north / 6366197.724 / 0.9996),
                                2,
                              ),
                        ))) *
                      (1 -
                        (((0.006739496742 *
                          Math.pow(
                            (this.#easting - 500000) /
                              ((0.9996 * 6399593.625) /
                                Math.sqrt(
                                  1 +
                                    0.006739496742 *
                                      Math.pow(
                                        Math.cos(north / 6366197.724 / 0.9996),
                                        2,
                                      ),
                                )),
                            2,
                          )) /
                          2) *
                          Math.pow(Math.cos(north / 6366197.724 / 0.9996), 2)) /
                          3),
                  ) -
                    Math.exp(
                      (-(this.#easting - 500000) /
                        ((0.9996 * 6399593.625) /
                          Math.sqrt(
                            1 +
                              0.006739496742 *
                                Math.pow(
                                  Math.cos(north / 6366197.724 / 0.9996),
                                  2,
                                ),
                          ))) *
                        (1 -
                          (((0.006739496742 *
                            Math.pow(
                              (this.#easting - 500000) /
                                ((0.9996 * 6399593.625) /
                                  Math.sqrt(
                                    1 +
                                      0.006739496742 *
                                        Math.pow(
                                          Math.cos(
                                            north / 6366197.724 / 0.9996,
                                          ),
                                          2,
                                        ),
                                  )),
                              2,
                            )) /
                            2) *
                            Math.pow(
                              Math.cos(north / 6366197.724 / 0.9996),
                              2,
                            )) /
                            3),
                    )) /
                    2 /
                    Math.cos(
                      ((north -
                        0.9996 *
                          6399593.625 *
                          (north / 6366197.724 / 0.9996 -
                            ((0.006739496742 * 3) / 4) *
                              (north / 6366197.724 / 0.9996 +
                                Math.sin((2 * north) / 6366197.724 / 0.9996) /
                                  2) +
                            (((Math.pow((0.006739496742 * 3) / 4, 2) * 5) / 3) *
                              (3 *
                                (north / 6366197.724 / 0.9996 +
                                  Math.sin((2 * north) / 6366197.724 / 0.9996) /
                                    2) +
                                Math.sin((2 * north) / 6366197.724 / 0.9996) *
                                  Math.pow(
                                    Math.cos(north / 6366197.724 / 0.9996),
                                    2,
                                  ))) /
                              4 -
                            (((Math.pow((0.006739496742 * 3) / 4, 3) * 35) /
                              27) *
                              ((5 *
                                (3 *
                                  (north / 6366197.724 / 0.9996 +
                                    Math.sin(
                                      (2 * north) / 6366197.724 / 0.9996,
                                    ) /
                                      2) +
                                  Math.sin((2 * north) / 6366197.724 / 0.9996) *
                                    Math.pow(
                                      Math.cos(north / 6366197.724 / 0.9996),
                                      2,
                                    ))) /
                                4 +
                                Math.sin((2 * north) / 6366197.724 / 0.9996) *
                                  Math.pow(
                                    Math.cos(north / 6366197.724 / 0.9996),
                                    2,
                                  ) *
                                  Math.pow(
                                    Math.cos(north / 6366197.724 / 0.9996),
                                    2,
                                  ))) /
                              3)) /
                        ((0.9996 * 6399593.625) /
                          Math.sqrt(
                            1 +
                              0.006739496742 *
                                Math.pow(
                                  Math.cos(north / 6366197.724 / 0.9996),
                                  2,
                                ),
                          ))) *
                        (1 -
                          ((0.006739496742 *
                            Math.pow(
                              (this.#easting - 500000) /
                                ((0.9996 * 6399593.625) /
                                  Math.sqrt(
                                    1 +
                                      0.006739496742 *
                                        Math.pow(
                                          Math.cos(
                                            north / 6366197.724 / 0.9996,
                                          ),
                                          2,
                                        ),
                                  )),
                              2,
                            )) /
                            2) *
                            Math.pow(
                              Math.cos(north / 6366197.724 / 0.9996),
                              2,
                            )) +
                        north / 6366197.724 / 0.9996,
                    ),
                ),
              ) *
                Math.tan(
                  ((north -
                    0.9996 *
                      6399593.625 *
                      (north / 6366197.724 / 0.9996 -
                        ((0.006739496742 * 3) / 4) *
                          (north / 6366197.724 / 0.9996 +
                            Math.sin((2 * north) / 6366197.724 / 0.9996) / 2) +
                        (((Math.pow((0.006739496742 * 3) / 4, 2) * 5) / 3) *
                          (3 *
                            (north / 6366197.724 / 0.9996 +
                              Math.sin((2 * north) / 6366197.724 / 0.9996) /
                                2) +
                            Math.sin((2 * north) / 6366197.724 / 0.9996) *
                              Math.pow(
                                Math.cos(north / 6366197.724 / 0.9996),
                                2,
                              ))) /
                          4 -
                        (((Math.pow((0.006739496742 * 3) / 4, 3) * 35) / 27) *
                          ((5 *
                            (3 *
                              (north / 6366197.724 / 0.9996 +
                                Math.sin((2 * north) / 6366197.724 / 0.9996) /
                                  2) +
                              Math.sin((2 * north) / 6366197.724 / 0.9996) *
                                Math.pow(
                                  Math.cos(north / 6366197.724 / 0.9996),
                                  2,
                                ))) /
                            4 +
                            Math.sin((2 * north) / 6366197.724 / 0.9996) *
                              Math.pow(
                                Math.cos(north / 6366197.724 / 0.9996),
                                2,
                              ) *
                              Math.pow(
                                Math.cos(north / 6366197.724 / 0.9996),
                                2,
                              ))) /
                          3)) /
                    ((0.9996 * 6399593.625) /
                      Math.sqrt(
                        1 +
                          0.006739496742 *
                            Math.pow(Math.cos(north / 6366197.724 / 0.9996), 2),
                      ))) *
                    (1 -
                      ((0.006739496742 *
                        Math.pow(
                          (this.#easting - 500000) /
                            ((0.9996 * 6399593.625) /
                              Math.sqrt(
                                1 +
                                  0.006739496742 *
                                    Math.pow(
                                      Math.cos(north / 6366197.724 / 0.9996),
                                      2,
                                    ),
                              )),
                          2,
                        )) /
                        2) *
                        Math.pow(Math.cos(north / 6366197.724 / 0.9996), 2)) +
                    north / 6366197.724 / 0.9996,
                ),
            ) -
              north / 6366197.724 / 0.9996) *
            3) /
            2) *
          (Math.atan(
            Math.cos(
              Math.atan(
                (Math.exp(
                  ((this.#easting - 500000) /
                    ((0.9996 * 6399593.625) /
                      Math.sqrt(
                        1 +
                          0.006739496742 *
                            Math.pow(Math.cos(north / 6366197.724 / 0.9996), 2),
                      ))) *
                    (1 -
                      (((0.006739496742 *
                        Math.pow(
                          (this.#easting - 500000) /
                            ((0.9996 * 6399593.625) /
                              Math.sqrt(
                                1 +
                                  0.006739496742 *
                                    Math.pow(
                                      Math.cos(north / 6366197.724 / 0.9996),
                                      2,
                                    ),
                              )),
                          2,
                        )) /
                        2) *
                        Math.pow(Math.cos(north / 6366197.724 / 0.9996), 2)) /
                        3),
                ) -
                  Math.exp(
                    (-(this.#easting - 500000) /
                      ((0.9996 * 6399593.625) /
                        Math.sqrt(
                          1 +
                            0.006739496742 *
                              Math.pow(
                                Math.cos(north / 6366197.724 / 0.9996),
                                2,
                              ),
                        ))) *
                      (1 -
                        (((0.006739496742 *
                          Math.pow(
                            (this.#easting - 500000) /
                              ((0.9996 * 6399593.625) /
                                Math.sqrt(
                                  1 +
                                    0.006739496742 *
                                      Math.pow(
                                        Math.cos(north / 6366197.724 / 0.9996),
                                        2,
                                      ),
                                )),
                            2,
                          )) /
                          2) *
                          Math.pow(Math.cos(north / 6366197.724 / 0.9996), 2)) /
                          3),
                  )) /
                  2 /
                  Math.cos(
                    ((north -
                      0.9996 *
                        6399593.625 *
                        (north / 6366197.724 / 0.9996 -
                          ((0.006739496742 * 3) / 4) *
                            (north / 6366197.724 / 0.9996 +
                              Math.sin((2 * north) / 6366197.724 / 0.9996) /
                                2) +
                          (((Math.pow((0.006739496742 * 3) / 4, 2) * 5) / 3) *
                            (3 *
                              (north / 6366197.724 / 0.9996 +
                                Math.sin((2 * north) / 6366197.724 / 0.9996) /
                                  2) +
                              Math.sin((2 * north) / 6366197.724 / 0.9996) *
                                Math.pow(
                                  Math.cos(north / 6366197.724 / 0.9996),
                                  2,
                                ))) /
                            4 -
                          (((Math.pow((0.006739496742 * 3) / 4, 3) * 35) / 27) *
                            ((5 *
                              (3 *
                                (north / 6366197.724 / 0.9996 +
                                  Math.sin((2 * north) / 6366197.724 / 0.9996) /
                                    2) +
                                Math.sin((2 * north) / 6366197.724 / 0.9996) *
                                  Math.pow(
                                    Math.cos(north / 6366197.724 / 0.9996),
                                    2,
                                  ))) /
                              4 +
                              Math.sin((2 * north) / 6366197.724 / 0.9996) *
                                Math.pow(
                                  Math.cos(north / 6366197.724 / 0.9996),
                                  2,
                                ) *
                                Math.pow(
                                  Math.cos(north / 6366197.724 / 0.9996),
                                  2,
                                ))) /
                            3)) /
                      ((0.9996 * 6399593.625) /
                        Math.sqrt(
                          1 +
                            0.006739496742 *
                              Math.pow(
                                Math.cos(north / 6366197.724 / 0.9996),
                                2,
                              ),
                        ))) *
                      (1 -
                        ((0.006739496742 *
                          Math.pow(
                            (this.#easting - 500000) /
                              ((0.9996 * 6399593.625) /
                                Math.sqrt(
                                  1 +
                                    0.006739496742 *
                                      Math.pow(
                                        Math.cos(north / 6366197.724 / 0.9996),
                                        2,
                                      ),
                                )),
                            2,
                          )) /
                          2) *
                          Math.pow(Math.cos(north / 6366197.724 / 0.9996), 2)) +
                      north / 6366197.724 / 0.9996,
                  ),
              ),
            ) *
              Math.tan(
                ((north -
                  0.9996 *
                    6399593.625 *
                    (north / 6366197.724 / 0.9996 -
                      ((0.006739496742 * 3) / 4) *
                        (north / 6366197.724 / 0.9996 +
                          Math.sin((2 * north) / 6366197.724 / 0.9996) / 2) +
                      (((Math.pow((0.006739496742 * 3) / 4, 2) * 5) / 3) *
                        (3 *
                          (north / 6366197.724 / 0.9996 +
                            Math.sin((2 * north) / 6366197.724 / 0.9996) / 2) +
                          Math.sin((2 * north) / 6366197.724 / 0.9996) *
                            Math.pow(
                              Math.cos(north / 6366197.724 / 0.9996),
                              2,
                            ))) /
                        4 -
                      (((Math.pow((0.006739496742 * 3) / 4, 3) * 35) / 27) *
                        ((5 *
                          (3 *
                            (north / 6366197.724 / 0.9996 +
                              Math.sin((2 * north) / 6366197.724 / 0.9996) /
                                2) +
                            Math.sin((2 * north) / 6366197.724 / 0.9996) *
                              Math.pow(
                                Math.cos(north / 6366197.724 / 0.9996),
                                2,
                              ))) /
                          4 +
                          Math.sin((2 * north) / 6366197.724 / 0.9996) *
                            Math.pow(
                              Math.cos(north / 6366197.724 / 0.9996),
                              2,
                            ) *
                            Math.pow(
                              Math.cos(north / 6366197.724 / 0.9996),
                              2,
                            ))) /
                        3)) /
                  ((0.9996 * 6399593.625) /
                    Math.sqrt(
                      1 +
                        0.006739496742 *
                          Math.pow(Math.cos(north / 6366197.724 / 0.9996), 2),
                    ))) *
                  (1 -
                    ((0.006739496742 *
                      Math.pow(
                        (this.#easting - 500000) /
                          ((0.9996 * 6399593.625) /
                            Math.sqrt(
                              1 +
                                0.006739496742 *
                                  Math.pow(
                                    Math.cos(north / 6366197.724 / 0.9996),
                                    2,
                                  ),
                            )),
                        2,
                      )) /
                      2) *
                      Math.pow(Math.cos(north / 6366197.724 / 0.9996), 2)) +
                  north / 6366197.724 / 0.9996,
              ),
          ) -
            north / 6366197.724 / 0.9996)) *
        180) /
      Math.PI;

    latitude = Math.round(latitude * 10000000);
    latitude = latitude / 10000000;

    let longitude =
      (Math.atan(
        (Math.exp(
          ((this.#easting - 500000) /
            ((0.9996 * 6399593.625) /
              Math.sqrt(
                1 +
                  0.006739496742 *
                    Math.pow(Math.cos(north / 6366197.724 / 0.9996), 2),
              ))) *
            (1 -
              (((0.006739496742 *
                Math.pow(
                  (this.#easting - 500000) /
                    ((0.9996 * 6399593.625) /
                      Math.sqrt(
                        1 +
                          0.006739496742 *
                            Math.pow(Math.cos(north / 6366197.724 / 0.9996), 2),
                      )),
                  2,
                )) /
                2) *
                Math.pow(Math.cos(north / 6366197.724 / 0.9996), 2)) /
                3),
        ) -
          Math.exp(
            (-(this.#easting - 500000) /
              ((0.9996 * 6399593.625) /
                Math.sqrt(
                  1 +
                    0.006739496742 *
                      Math.pow(Math.cos(north / 6366197.724 / 0.9996), 2),
                ))) *
              (1 -
                (((0.006739496742 *
                  Math.pow(
                    (this.#easting - 500000) /
                      ((0.9996 * 6399593.625) /
                        Math.sqrt(
                          1 +
                            0.006739496742 *
                              Math.pow(
                                Math.cos(north / 6366197.724 / 0.9996),
                                2,
                              ),
                        )),
                    2,
                  )) /
                  2) *
                  Math.pow(Math.cos(north / 6366197.724 / 0.9996), 2)) /
                  3),
          )) /
          2 /
          Math.cos(
            ((north -
              0.9996 *
                6399593.625 *
                (north / 6366197.724 / 0.9996 -
                  ((0.006739496742 * 3) / 4) *
                    (north / 6366197.724 / 0.9996 +
                      Math.sin((2 * north) / 6366197.724 / 0.9996) / 2) +
                  (((Math.pow((0.006739496742 * 3) / 4, 2) * 5) / 3) *
                    (3 *
                      (north / 6366197.724 / 0.9996 +
                        Math.sin((2 * north) / 6366197.724 / 0.9996) / 2) +
                      Math.sin((2 * north) / 6366197.724 / 0.9996) *
                        Math.pow(Math.cos(north / 6366197.724 / 0.9996), 2))) /
                    4 -
                  (((Math.pow((0.006739496742 * 3) / 4, 3) * 35) / 27) *
                    ((5 *
                      (3 *
                        (north / 6366197.724 / 0.9996 +
                          Math.sin((2 * north) / 6366197.724 / 0.9996) / 2) +
                        Math.sin((2 * north) / 6366197.724 / 0.9996) *
                          Math.pow(
                            Math.cos(north / 6366197.724 / 0.9996),
                            2,
                          ))) /
                      4 +
                      Math.sin((2 * north) / 6366197.724 / 0.9996) *
                        Math.pow(Math.cos(north / 6366197.724 / 0.9996), 2) *
                        Math.pow(Math.cos(north / 6366197.724 / 0.9996), 2))) /
                    3)) /
              ((0.9996 * 6399593.625) /
                Math.sqrt(
                  1 +
                    0.006739496742 *
                      Math.pow(Math.cos(north / 6366197.724 / 0.9996), 2),
                ))) *
              (1 -
                ((0.006739496742 *
                  Math.pow(
                    (this.#easting - 500000) /
                      ((0.9996 * 6399593.625) /
                        Math.sqrt(
                          1 +
                            0.006739496742 *
                              Math.pow(
                                Math.cos(north / 6366197.724 / 0.9996),
                                2,
                              ),
                        )),
                    2,
                  )) /
                  2) *
                  Math.pow(Math.cos(north / 6366197.724 / 0.9996), 2)) +
              north / 6366197.724 / 0.9996,
          ),
      ) *
        180) /
        Math.PI +
      this.#zone * 6 -
      183;

    longitude = Math.round(longitude * 10000000);
    longitude = longitude / 10000000;

    return Point.degrees(longitude, latitude);
  }

  public static parse(utm: string): UTM {
    const matches = utm.match(UTM.#utmPattern);
    if (!matches) {
      throw new Error(`Invalid UTM: ${utm}`);
    }

    const zone = parseInt(matches[1], 10);
    UTM.validateZone(zone);

    const hemisphere =
      matches[2].toUpperCase() === "N" ? Hemisphere.NORTH : Hemisphere.SOUTH;

    const easting = +matches[3];
    const northing = +matches[4];

    return new UTM(zone, hemisphere, easting, northing);
  }

  public static validateZone(zone: number) {
    if (zone < 1 || zone > 60) {
      throw new Error(`Invalid MGRS zone (1-60): ${zone}`);
    }
  }
}
