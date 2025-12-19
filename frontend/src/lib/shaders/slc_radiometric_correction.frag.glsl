precision highp float;

uniform sampler2D u_texture;
uniform vec2 u_textureSize;

uniform vec3 u_noiseCoefs[3];
uniform vec3 u_sigmaZeroCoefs[3];

varying vec2 v_textureCoord;

float evalPoly(vec3 coefs, float x) {
  return coefs.x + coefs.y * x + coefs.z * x * x;
}

void main() {
  float intensity = texture(u_texture, v_textureCoord).r;

  // Row coordinate for polynomials
  float row = v_textureCoord.y * u_textureSize.y;

  float noise = evalPoly(u_noiseCoefs[0], row)
   + evalPoly(u_noiseCoefs[1], row)
   + evalPoly(u_noiseCoefs[2], row);

  intensity = max(intensity - noise, 1e-6);

  float sigma0 = intensity * (
    evalPoly(u_sigmaZeroCoefs[0], row) +
    evalPoly(u_sigmaZeroCoefs[1], row) +
    evalPoly(u_sigmaZeroCoefs[2], row)
  );

  float dB = 10.0 * log10(sigma0);

  float displayVal = (dB + 25.0) / 45.0;
  displayVal = clamp(displayVal, 0.0, 1.0);

  //float logVal = log(1.0 + sigma0);

  gl_FragColor = vec4(vec3(logVal), 1.0);
}
