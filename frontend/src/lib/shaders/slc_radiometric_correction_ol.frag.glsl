#ifdef GL_FRAGMENT_PRECISION_HIGH
precision highp float;
#else
precision mediump float;
#endif

varying vec2 v_textureCoord;
varying vec2 v_mapCoord;

uniform vec4 u_renderExtent;
uniform float u_transitionAlpha;
uniform float u_texturePixelWidth;
uniform float u_texturePixelHeight;
uniform float u_resolution;
uniform float u_zoom;
uniform sampler2D u_tileTextures[1];

uniform vec3 u_noiseCoefs[3];
uniform vec3 u_sigmaZeroCoefs[3];

float evalPoly(vec3 coefs, float x) {
  return coefs.x + coefs.y * x + coefs.z * x * x;
}

void main() {
  if (
    v_mapCoord[0] < u_renderExtent[0] ||
    v_mapCoord[1] < u_renderExtent[1] ||
    v_mapCoord[0] > u_renderExtent[2] ||
    v_mapCoord[1] > u_renderExtent[3]
  ){
    discard;
  }

  float intensity = texture2D(u_tileTextures[0], v_textureCoord).r;
  float row = v_textureCoord.y * u_texturePixelHeight;

  float noise = evalPoly(u_noiseCoefs[0], row)
   + evalPoly(u_noiseCoefs[1], row)
   + evalPoly(u_noiseCoefs[2], row);

  intensity = max(intensity - noise, 1e-6);

  float sigma0 = intensity * (
    evalPoly(u_sigmaZeroCoefs[0], row) +
    evalPoly(u_sigmaZeroCoefs[1], row) +
    evalPoly(u_sigmaZeroCoefs[2], row)
  );

  float dB = 10.0 * log10(max(sigma0, 1e-10));

  float logValue = clamp((dB + 50.0) / 50.0, 0.0, 1.0);
  logValue = clamp(logValue, 0.0, 1.0);

  gl_FragColor = vec4(vec3(logValue), 1.0);
  gl_FragColor.rgb *= gl_FragColor.a;
  gl_FragColor *= u_transitionAlpha;
}
