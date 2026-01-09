[NGA.SIG.0012_2.0.0_UTMUPS](https://nsgreg.nga.mil/doc/view?i=4056)

# Military Grid Reference System (MGRS)

### UTM portion
The UTM portion of MGRS is the following sequence alphanumeric sequence
1. UTM zone number (1-60)
2. UTM band letter (C-HJ-NP-X)
3. 100,000-meter square identification (two letters) 
4. UTM easting (zero to five decimal digits)
5. UTM northing (zero to five decimal digits)

### 100,000-meter square identification

#### Lettering scheme "AA"

Let $Z$ be UTM zone and $(y, x)$ be the UTM easting and northing of a point within these limits:
- $100,000 \leq x < 900,000$
- $0 \leq y 9,700,000$ if $Z > 0$
- $300,000 \leq y < 10,000,000$ if $Z \leq 0$

The 100,000 meter square identifier consists of an easting letter followed by a northing letter. The easting letter is the conversion of $\lfloor x / 100,000 \rfloor$ according to the following set of tables

- if $|Z| \bmod 3 = 1$:

| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|
| A | B | C | D | E | F | G | H |

- if $|Z| \bmod 3 = 2$:

| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|
| J | K | L | M | N | P | Q | R |

- if $|Z| \bmod 3 = 0$

| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|
| S | T | U | V | W | X | Y | Z |

The northing letter is the conversion of

$$
  \lfloor (y \bmod 2,000,000) / 100,000 \rfloor
$$

according to the following set of tables

- if $|Z|$ is odd

| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | B | C | D | E | F | G | H | J | K | L | M | N | P | Q | R | S | T | U | V |

- if $|Z|$ is even

| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F | G | H | J | K | L | M | N | P | Q | R | S | T | U | V | A | B | C | D | E |

## UPS portion

The UPS portion of MGRS is the following alphanumeric sequence
1. Three letters, two easting letters and one northing letter, representing a 100,000-meter square
2. UTM easting (zero to five decimal digits)
3. UTM northing (zero to five decimal digits)

### Conversion of MGRS to UTM or UPS

If the first character of an MGRS string is a digit, the string belongs to the UTM portion of MGRS and can be con-
verted to UTM coordinates. Otherwise the string belongs to the UPS portion of MGRS and can be converted to UPS
coordinates. In both cases, the easting $x$ is obtained by:

$$
  x = 100,000 x_\text{letter} + 10^{5-n} x_\text{digits}
$$

where
- $x_\text{letter}$ is the number listed in the appropriate lettering-scheme table for the given easting letter(s) and
- $x_\text{digit}$ is easting given to a precision of $n$ digits

For the UPS portion of MGRS, the northing $y$ is obtained by

$$
  y = 100,000 y_\text{letter} + 10^{5-n} y_\text{digits}
$$

where
- $y_\text{letter}$ is the number listed in the appropriate lettering-scheme table for the given northing letter and
- $y_\text{digit}$ is northing given to a precision of $n$ digits

For the UTM portion of MGRS, the obtaining the northing requires several steps. A preliminary northing $y_\text{prelim}$ is obtained by

$$
  y_\text{prelim} = 100,000 y_\text{letter} + 10^{5-n} y_\text{digit}
$$

where $y_\text{letter}$ and $y_\text{digit}$ are given like above for the UPS portion. Then the northing $y$ is given by

$$
  y = 2,000,000 y_\text{band} + y_\text{prelim}
$$

where $y_\text{band}$ is the choice among $\set{0,1,2,3,4}$ that satisfies the requirement that converting the obtained UTM coordinates $(x, y)$ back to longitude and latitude $(\lambda, \phi)$ yield a latitude $\phi$ lying in the given MGRS latitude band. The following table show trial values of $y_\text{band}$ corresponding to MGRS latitude band letters. For some latitude letters, there is only one possibility and the trial value is the actual value. In such cases, a UTM-to-Lon/Lat calculation is not needed.

| C | D | E | F | G | H | J | K | L | M | N | P | Q | R | S | T | U | V | W | X |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 1 | 2 | 2 | 3 | 3 | 4 | 4 | 4 | 0 | 0 | 0 | 1 | 1 | 2 | 2 | 3 | 3 | 3 |
| 0 | 0 |   | 1 |   | 2 |   | 3 |   |   |   |   | 1 |   | 2 |   | 3 |   | 4 | 4 |
