# Usage instructions

## Prerequisites

This application consists of a Python backend and a SvelteKit frontend built on Node.js using the pnpm package manager. The backend requires Python 3.10 or newer and runs without any external Python dependencies.

The application also depends on QGIS being installed. QGSI includes the required geospatial tools:
1. GDAL
2. SpatiaLite

The application locates these binaries using environment variables defined in the `.env` file:
- `GDAL_PATH`: path to GDAL installation
- `SPATIALITE`: path SpatiaLite library
- `QGIS_PATH`: path to the QGIS installation (needed because SpatiaLite is accessed through QGIS)

## Development mode

Install the required Node.js modules by running `pnpm i` (or another Node.js package manager) inside the `frontend` directory. To run the application in development mode, start two terminals:
1. **Backend (Python):** 

Run from the project root:

```sh
python app.py
```

The backend runs on host `0.0.0.0` and port `8080`. Both values can be changed in the `.env` file.

2. **Frontend (Vite/SvelteKit):** 

Run from the `frontend` directory:

```
pnpm dev
```

The Vite development server runs is available at `http://localhost:5173`.

### Specify map servers

In development mode, map servers can be configured in the `map_config.json` file located in `frontend/static`.

## Installation

To build the application, run the following command from the project root:

```
python pack.py
```

The packaged application will be generated in the `dist` directory at the root of the project. To start the application run `app.py` from inside the `dist` directory. In production mode, map servers can be configured in the `map_config.json` file located in `dist/static`.
