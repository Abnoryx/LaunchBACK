// WebGL2 compositor: premultiplied RGBA16F buffers, perspective quads, AE blend modes,
// track mattes, masks, and the effects used by the reference projects as shader passes.

const VS = `#version 300 es
in vec4 aPos; in vec2 aUV; out vec2 vUV;
void main(){ gl_Position = aPos; vUV = aUV; }`;

const FS_HEAD = `#version 300 es
precision highp float; in vec2 vUV; out vec4 o; uniform sampler2D uTex; uniform vec2 uRes;`;

const SHADERS = {
  copy: `${FS_HEAD} void main(){ o = texture(uTex, vUV); }`,
  // Layer composite: src texture * opacity * matte * mask, blended over dst copy with an AE blend mode.
  layer: `${FS_HEAD}
  uniform sampler2D uDst, uMatte, uMask; uniform float uOpacity; uniform int uMode, uMatteMode, uHasMask;
  vec3 ov(vec3 a, vec3 b){ return mix(2.0*a*b, 1.0-2.0*(1.0-a)*(1.0-b), step(0.5,a)); }
  vec3 sl(vec3 b, vec3 s){ // soft light (b = backdrop, s = source)
    vec3 d = mix(sqrt(b), ((16.0*b-12.0)*b+4.0)*b, step(b, vec3(0.25)));
    return mix(b - (1.0-2.0*s)*b*(1.0-b), b + (2.0*s-1.0)*(d-b), step(0.5, s)); }
  void main(){
    vec4 s = texture(uTex, vUV) * uOpacity;
    vec2 sc = gl_FragCoord.xy / uRes;
    if (uMatteMode != 0) { vec4 m = texture(uMatte, sc);
      float k = uMatteMode==1 ? m.a : uMatteMode==2 ? 1.0-m.a : uMatteMode==3 ? dot(m.rgb,vec3(.2126,.7152,.0722)) : 1.0-dot(m.rgb,vec3(.2126,.7152,.0722));
      s *= k; }
    if (uHasMask == 1) s *= texture(uMask, vUV).a;
    vec4 d = texture(uDst, sc);
    if (uMode == 10) { o = s; return; }
    if (uMode == 0) { o = s + d*(1.0-s.a); return; }
    vec3 sc3 = s.a > 0.0 ? s.rgb/s.a : vec3(0.0), dc3 = d.a > 0.0 ? d.rgb/d.a : vec3(0.0);
    vec3 b;
    if (uMode == 1) b = sc3*dc3;                       // multiply
    else if (uMode == 2) b = 1.0-(1.0-sc3)*(1.0-dc3);  // screen
    else if (uMode == 3) b = ov(dc3, sc3);             // overlay
    else if (uMode == 4) b = sl(dc3, sc3);             // soft light
    else if (uMode == 5) b = min(sc3+dc3, 1.0);        // add
    else if (uMode == 6) b = abs(dc3-sc3);             // difference
    else if (uMode == 7) b = sc3+dc3-2.0*sc3*dc3;      // exclusion
    else if (uMode == 8) b = ov(sc3, dc3);             // hard light
    else b = sc3;
    vec3 rgb = (1.0-d.a)*s.rgb + (1.0-s.a)*d.rgb + s.a*d.a*b;
    if (uMode == 9) { o = d * s.a; return; }           // stencil alpha
    o = vec4(rgb, s.a + d.a*(1.0-s.a));
  }`,
  blur: `${FS_HEAD} uniform vec2 uDir; uniform float uSigma;
  void main(){ float s = max(uSigma, 0.01); int r = int(min(ceil(s*3.0), 24.0));
    vec4 acc = vec4(0.0); float w = 0.0;
    for (int i=-24;i<=24;i++){ if (i<-r||i>r) continue; float g = exp(-0.5*float(i*i)/(s*s));
      acc += texture(uTex, vUV + uDir*float(i)/uRes) * g; w += g; }
    o = acc / w; }`,
  minimax: `${FS_HEAD} uniform vec2 uDir; uniform float uRad; uniform int uMax;
  void main(){ int r = int(min(uRad, 120.0)); vec4 m = texture(uTex, vUV);
    for (int i=-120;i<=120;i++){ if (i<-r||i>r) continue; vec4 c = texture(uTex, vUV + uDir*float(i)/uRes);
      m = uMax==1 ? max(m,c) : min(m,c); } o = m; }`,
  // colour ops on premultiplied input
  color: `${FS_HEAD}
  uniform int uOp; uniform vec4 uA, uB; uniform float uK; uniform sampler2D uLut;
  void main(){ vec4 c = texture(uTex, vUV); float a = c.a; vec3 rgb = a > 0.0 ? c.rgb/a : vec3(0.0);
    if (uOp == 1) rgb = mix(rgb, uA.rgb, uK);                                     // fill
    else if (uOp == 2) { float l = dot(rgb, vec3(.2126,.7152,.0722)); rgb = mix(rgb, mix(uA.rgb, uB.rgb, l), uK); } // tint
    else if (uOp == 3) { rgb = pow(max(rgb*exp2(uA.x) + uA.y, 0.0), vec3(1.0/max(uA.z,0.01))); }               // exposure
    else if (uOp == 4) { rgb = vec3(texture(uLut, vec2(rgb.r,.5)).r, texture(uLut, vec2(rgb.g,.5)).g, texture(uLut, vec2(rgb.b,.5)).b); } // curves
    else if (uOp == 5) { float l = dot(rgb, vec3(.2126,.7152,.0722)); rgb = vec3(step(uK, l)); }                 // threshold
    else if (uOp == 6) { rgb = 1.0 - rgb; }                                                                       // invert
    else if (uOp == 7) { vec2 p = vUV*uRes; vec2 d = uB.xy-uA.xy; float f = clamp(dot(p-uA.xy,d)/max(dot(d,d),1e-3),0.0,1.0); rgb *= mix(vec3(0.0), vec3(1.0), f) * uK + (1.0-uK); } // gradient multiply
    else if (uOp == 8) { vec2 p = vUV - 0.5; float v = 1.0 - uK*dot(p,p)*2.0; rgb *= clamp(v,0.0,1.0); }         // vignette
    else if (uOp == 9) { // dot halftone (AM, 45 deg): uK = cell px, uA = ink, uB = paper
      vec2 p = vUV*uRes; float c = 0.70710678; mat2 R = mat2(c,-c,c,c); vec2 q = R*p; vec2 cell = floor(q/uK)*uK + 0.5*uK;
      vec2 cp = transpose(R)*cell; vec4 s = texture(uTex, cp/uRes); float l = s.a > 0.0 ? dot(s.rgb/s.a, vec3(.2126,.7152,.0722)) : 1.0;
      float r = uK*0.5*1.414*sqrt(clamp(1.0-l,0.0,1.0)); float d = length(q-cell);
      float ink = 1.0 - smoothstep(r-0.75, r+0.75, d); rgb = mix(uB.rgb, uA.rgb, ink); }
    else if (uOp == 11) { // Extract luma key: uA = (black, white, black soft, white soft)
      float l = dot(rgb, vec3(.2126,.7152,.0722));
      float k = smoothstep(uA.x - uA.z, uA.x + uA.z, l) * (1.0 - smoothstep(uA.y - uA.w, uA.y + uA.w, l));
      a *= k; }
    else if (uOp == 12) { // linear wipe: uA = (cx, cy, angle deg, half-extent), uK = completion 0..1, uB.x = feather px
      vec2 p = vUV*uRes; float an = radians(uA.z); vec2 d = vec2(sin(an), -cos(an));
      float u = (dot(p - uA.xy, d) + uA.w) / max(2.0*uA.w, 1e-3); float f = max(uB.x, 1e-3) / max(2.0*uA.w, 1e-3);
      a *= smoothstep(uK - f*0.5, uK + f*0.5, u * (1.0 + f) - f*0.5 + 1e-4) * step(1e-4, 1.0 - uK); }
    else if (uOp == 13) { // colour balance (HLS): uA = (hue deg, lightness -100..100, saturation -100..100)
      float mx = max(rgb.r, max(rgb.g, rgb.b)), mn = min(rgb.r, min(rgb.g, rgb.b)), l = (mx + mn) * 0.5, dl = mx - mn;
      float h = 0.0, sat = 0.0;
      if (dl > 1e-5) { sat = l > 0.5 ? dl / (2.0 - mx - mn) : dl / (mx + mn);
        h = mx == rgb.r ? (rgb.g - rgb.b) / dl + (rgb.g < rgb.b ? 6.0 : 0.0) : mx == rgb.g ? (rgb.b - rgb.r) / dl + 2.0 : (rgb.r - rgb.g) / dl + 4.0; h /= 6.0; }
      h = fract(h + uA.x / 360.0); sat = clamp(sat * (1.0 + uA.z / 100.0), 0.0, 1.0);
      l = uA.y >= 0.0 ? l + (1.0 - l) * uA.y / 100.0 : l * (1.0 + uA.y / 100.0);
      float q = l < 0.5 ? l * (1.0 + sat) : l + sat - l * sat, pp = 2.0 * l - q;
      vec3 t3 = fract(vec3(h + 1.0/3.0, h, h - 1.0/3.0)); vec3 c3;
      for (int i = 0; i < 3; i++) { float tt = t3[i]; c3[i] = tt < 1.0/6.0 ? pp + (q - pp) * 6.0 * tt : tt < 0.5 ? q : tt < 2.0/3.0 ? pp + (q - pp) * (2.0/3.0 - tt) * 6.0 : pp; }
      rgb = c3; }
    else if (uOp == 10) { // light sweep: band across direction uA.z (deg) centred at uA.xy (px), width uK, colour uB
      vec2 p = vUV*uRes; float an = radians(uA.z); vec2 n = vec2(cos(an), sin(an)); float d = abs(dot(p-uA.xy, n));
      float k = exp(-d*d/(2.0*uK*uK/9.0)); rgb = rgb + uB.rgb*k*uB.a; }
    o = vec4(rgb*a, a); }`,
  // drop shadow: uTex = blurred source alpha, uDst = original. Offset in px.
  shadow: `${FS_HEAD} uniform sampler2D uDst; uniform vec2 uOff; uniform vec4 uA; uniform float uK; uniform int uOnly;
  void main(){ float sa = texture(uTex, vUV - uOff/uRes).a * uK; vec4 sh = vec4(uA.rgb*sa, sa); vec4 src = texture(uDst, vUV);
    o = uOnly==1 ? sh : src + sh*(1.0-src.a); }`,
  mtile: `${FS_HEAD} uniform float uK; uniform vec2 uOff; void main(){ vec2 q = vUV; if (uK > 0.5) { q = abs(mod(q + 1.0, 2.0) - 1.0); } else { q = fract(q); } o = texture(uTex, q); }`,
  stencil: `${FS_HEAD} uniform sampler2D uDst; uniform int uMode; void main(){ float a = texture(uTex, vUV).a; vec4 d = texture(uDst, vUV);
    o = uMode == 9 ? d * a : uMode == 11 ? d * (1.0 - a) : d; }`,
  flare: `${FS_HEAD} uniform vec2 uPos; uniform float uK, uS; void main(){ vec2 p = vUV*uRes - uPos; float r = length(p);
    float core = exp(-r*r/(2.0*pow(26.0*uS,2.0)));
    float glow = exp(-r/(170.0*uS)) * 0.55;
    float streak = exp(-abs(p.y)/(3.5*uS)) * exp(-abs(p.x)/(260.0*uS)) * 0.9;
    float streak2 = exp(-abs(p.y)/(1.6*uS)) * exp(-abs(p.x)/(140.0*uS)) * 0.6;
    vec3 c = vec3(1.0)*core + vec3(0.85,0.95,1.0)*(glow + streak + streak2);
    c *= uK; o = vec4(c, max(c.r, max(c.g, c.b))); }`,
  radialca: `${FS_HEAD} uniform float uK; void main(){ vec2 c = vec2(0.5); vec2 d = vUV - c; vec4 g = texture(uTex, vUV);
    o = vec4(texture(uTex, c + d*(1.0+uK)).r, g.g, texture(uTex, c + d*(1.0-uK)).b, g.a); }`,
  scanlines: `${FS_HEAD} uniform float uK, uP, uAng; void main(){ vec4 c = texture(uTex, vUV); vec2 p = vUV*uRes; float an = radians(uAng);
    float s = sin(6.2831853 * dot(p, vec2(cos(an), sin(an))) / uP); o = vec4(c.rgb + uK*s*c.a, c.a); }`,
  // 3D LUT tiled as N*N x N (blue slices side by side), trilinear by blending two slices
  lut3d: `${FS_HEAD} uniform sampler2D uLut; uniform float uN, uK; void main(){ vec4 c = texture(uTex, vUV); float a = c.a; vec3 rgb = a > 0.0 ? clamp(c.rgb/a, 0.0, 1.0) : vec3(0.0);
    float b = rgb.b*(uN-1.0), b0 = floor(b), b1 = min(b0+1.0, uN-1.0), f = b-b0;
    vec2 q = (rgb.rg*(uN-1.0) + 0.5) / vec2(uN*uN, uN);
    vec3 l0 = texture(uLut, q + vec2(b0/uN, 0.0)).rgb, l1 = texture(uLut, q + vec2(b1/uN, 0.0)).rgb;
    o = vec4(mix(rgb, mix(l0, l1, f), uK)*a, a); }`,
  rgbtime: `${FS_HEAD} uniform sampler2D uA, uB; void main(){ vec4 c = texture(uTex, vUV), a = texture(uA, vUV), b = texture(uB, vUV);
    o = vec4(a.r, c.g, b.b, max(c.a, max(a.a, b.a))); }`,
  rgbsplit: `${FS_HEAD} uniform vec2 uOff; void main(){ vec4 c = texture(uTex, vUV); float r = texture(uTex, vUV + uOff/uRes).r; float b = texture(uTex, vUV - uOff/uRes).b; o = vec4(r, c.g, b, c.a); }`,
  add: `${FS_HEAD} uniform sampler2D uDst; uniform float uK; void main(){ o = texture(uDst, vUV) + texture(uTex, vUV)*uK; }`,
  mix: `${FS_HEAD} uniform sampler2D uDst, uMask; uniform float uK; uniform int uHasMask;
  void main(){ float m = uK * (uHasMask==1 ? texture(uMask, vUV).a : 1.0); o = mix(texture(uDst, vUV), texture(uTex, vUV), m); }`,
  accum: `${FS_HEAD} uniform float uK; void main(){ o = texture(uTex, vUV) * uK; }`,
  transform: `${FS_HEAD} uniform mat3 uM; uniform float uK; void main(){ vec3 p = uM * vec3(vUV*uRes, 1.0); vec2 q = p.xy/uRes;
    o = (q.x<0.0||q.y<0.0||q.x>1.0||q.y>1.0) ? vec4(0.0) : texture(uTex, q) * uK; }`,
};

export class GL {
  constructor(canvas) {
    const gl = (this.gl = canvas.getContext('webgl2', { premultipliedAlpha: true, alpha: true, antialias: false, preserveDrawingBuffer: true }));
    if (!gl.getExtension('EXT_color_buffer_float')) throw new Error('no float buffers');
    gl.getExtension('OES_texture_float_linear');
    this.progs = {};
    for (const [k, fs] of Object.entries(SHADERS)) this.progs[k] = this.program(VS, fs);
    this.vbo = gl.createBuffer();
    this.pool = [];
    this.blank = this.texFromData(1, 1, new Uint8Array([0, 0, 0, 0]));
  }
  program(vs, fs) {
    const gl = this.gl, p = gl.createProgram();
    for (const [t, s] of [[gl.VERTEX_SHADER, vs], [gl.FRAGMENT_SHADER, fs]]) {
      const sh = gl.createShader(t); gl.shaderSource(sh, s); gl.compileShader(sh);
      if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(sh) + s.slice(0, 200));
      gl.attachShader(p, sh);
    }
    gl.bindAttribLocation(p, 0, 'aPos'); gl.bindAttribLocation(p, 1, 'aUV');
    gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p));
    p.u = {};
    const n = gl.getProgramParameter(p, gl.ACTIVE_UNIFORMS);
    p.ty = {};
    for (let i = 0; i < n; i++) { const u = gl.getActiveUniform(p, i); p.u[u.name] = gl.getUniformLocation(p, u.name); p.ty[u.name] = u.type; }
    return p;
  }
  texFromData(w, h, data) {
    const gl = this.gl, t = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, t);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, w, h, 0, gl.RGBA, gl.UNSIGNED_BYTE, data);
    this.params();
    return { tex: t, w, h };
  }
  params() {
    const gl = this.gl;
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  }
  // Upload an image/canvas as premultiplied texture.
  texFromImage(img, keep) {
    const gl = this.gl, t = keep?.tex || gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, t);
    gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, true);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
    gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false);
    this.params();
    return { tex: t, w: img.width, h: img.height };
  }
  deleteTex(t) { if (t && t.tex) this.gl.deleteTexture(t.tex); }
  // Float render target from a pool.
  target(w, h) {
    w = Math.max(1, Math.round(w)); h = Math.max(1, Math.round(h));
    const i = this.pool.findIndex((r) => r.w === w && r.h === h && !r.used);
    if (i >= 0) { const r = this.pool[i]; r.used = true; return r; }
    const pooled = this.pool.filter((r) => r.w === w && r.h === h).length;
    const gl = this.gl, tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA16F, w, h, 0, gl.RGBA, gl.HALF_FLOAT, null);
    this.params();
    const fb = gl.createFramebuffer();
    gl.bindFramebuffer(gl.FRAMEBUFFER, fb);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
    const r = { tex, fb, w, h, used: true };
    if ((this.keep || []).some(([a, b]) => a === w && b === h) && pooled < 24) this.pool.push(r);
    else r.temp = true;
    return r;
  }
  release(r) {
    if (!r || !r.fb) return;
    if (r.temp) { this.gl.deleteFramebuffer(r.fb); this.gl.deleteTexture(r.tex); r.fb = null; return; }
    r.used = false;
  }
  clear(r, c = [0, 0, 0, 0]) {
    const gl = this.gl;
    gl.bindFramebuffer(gl.FRAMEBUFFER, r.fb); gl.viewport(0, 0, r.w, r.h);
    gl.clearColor(...c); gl.clear(gl.COLOR_BUFFER_BIT);
  }
  // Draw with program into target. quad: 4 verts [x,y,z,w] clip, default full screen.
  run(prog, dst, uniforms = {}, texs = {}, quad = null, blend = null) {
    const gl = this.gl, p = this.progs[prog];
    gl.useProgram(p);
    gl.bindFramebuffer(gl.FRAMEBUFFER, dst ? dst.fb : null);
    gl.viewport(0, 0, dst.w, dst.h);
    let unit = 0;
    for (const [name, t] of Object.entries(texs)) {
      gl.activeTexture(gl.TEXTURE0 + unit);
      gl.bindTexture(gl.TEXTURE_2D, (t || this.blank).tex);
      gl.uniform1i(p.u[name], unit++);
    }
    if (p.u.uRes) gl.uniform2f(p.u.uRes, dst.w, dst.h);
    for (const [k, v] of Object.entries(uniforms)) {
      const loc = p.u[k]; if (loc == null) continue;
      if (typeof v === 'number') (p.ty[k] === gl.INT || p.ty[k] === gl.BOOL) ? gl.uniform1i(loc, v) : gl.uniform1f(loc, v);
      else if (v.length === 2) gl.uniform2fv(loc, v);
      else if (v.length === 4) gl.uniform4fv(loc, v);
      else if (v.length === 9) gl.uniformMatrix3fv(loc, false, v);
    }
    const q = quad || [[-1, -1, 0, 1], [1, -1, 0, 1], [-1, 1, 0, 1], [1, 1, 0, 1]];
    const uv = [[0, 0], [1, 0], [0, 1], [1, 1]];
    const data = new Float32Array(24);
    for (let i = 0; i < 4; i++) { data.set(q[i], i * 6); data.set(quad ? uv[i] : uv[i], i * 6 + 4); }
    gl.bindBuffer(gl.ARRAY_BUFFER, this.vbo);
    gl.bufferData(gl.ARRAY_BUFFER, data, gl.STREAM_DRAW);
    gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 4, gl.FLOAT, false, 24, 0);
    gl.enableVertexAttribArray(1); gl.vertexAttribPointer(1, 2, gl.FLOAT, false, 24, 16);
    if (blend) { gl.enable(gl.BLEND); gl.blendFunc(...blend); } else gl.disable(gl.BLEND);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  }
  copy(src, dst) { this.run('copy', dst, {}, { uTex: src }); }

  // ---- effect helpers (all return a new pooled target; caller releases src if wanted)
  blur(src, sigmaX, sigmaY = sigmaX) {
    // Large blurs run at reduced resolution (kernel sigma kept <= 4 px) and are scaled back up:
    // the result is smooth, so this is visually identical and far cheaper.
    let k = 1;
    let cur = src;
    while (Math.max(sigmaX, sigmaY) / (k * 2) >= 3 && cur.w > 8 && cur.h > 8) {
      // halving with bilinear sampling averages 2x2 texels
      const h = this.target(Math.ceil(cur.w / 2), Math.ceil(cur.h / 2));
      this.copy(cur, h);
      if (cur !== src) this.release(cur);
      cur = h; k *= 2;
    }
    for (const [dir, sig] of [[[1, 0], sigmaX / k], [[0, 1], sigmaY / k]]) {
      if (sig < 0.3) continue;
      const t = this.target(cur.w, cur.h);
      this.run('blur', t, { uDir: dir, uSigma: sig }, { uTex: cur });
      if (cur !== src) this.release(cur);
      cur = t;
    }
    if (cur === src) { const t = this.target(src.w, src.h); this.copy(src, t); return t; }
    if (k > 1) { const up = this.target(src.w, src.h); this.copy(cur, up); this.release(cur); return up; }
    return cur;
  }
  minimax(src, rad, dirs, isMax) {
    let cur = src;
    for (const d of dirs) {
      const t = this.target(src.w, src.h);
      this.run('minimax', t, { uDir: d, uRad: rad, uMax: isMax ? 1 : 0 }, { uTex: cur });
      if (cur !== src) this.release(cur);
      cur = t;
    }
    return cur;
  }
  color(src, op, u = {}, lut = null) {
    const t = this.target(src.w, src.h);
    this.run('color', t, { uOp: op, uA: [0, 0, 0, 0], uB: [0, 0, 0, 0], uK: 1, ...u }, { uTex: src, uLut: lut });
    return t;
  }
  lut3dTex(lut, n) { // lut: flat [r,g,b]*n^3 in 0..255, index ((b*n)+g)*n+r
    const d = new Uint8Array(n * n * n * 4);
    for (let b = 0; b < n; b++) for (let g = 0; g < n; g++) for (let r = 0; r < n; r++) {
      const i = ((b * n + g) * n + r) * 3, o = (g * n * n + b * n + r) * 4;
      d[o] = lut[i]; d[o + 1] = lut[i + 1]; d[o + 2] = lut[i + 2]; d[o + 3] = 255;
    }
    return this.texFromData(n * n, n, d);
  }
  lutTex(curve) { // curve: Float32Array(256) per channel x3 → RGBA8 1D texture
    const d = new Uint8Array(256 * 4);
    for (let i = 0; i < 256; i++) { d[i * 4] = curve[0][i]; d[i * 4 + 1] = curve[1][i]; d[i * 4 + 2] = curve[2][i]; d[i * 4 + 3] = 255; }
    return this.texFromData(256, 1, d);
  }
  readPixels(r) {
    const gl = this.gl;
    gl.bindFramebuffer(gl.FRAMEBUFFER, r.fb);
    const out = new Uint8Array(r.w * r.h * 4);
    gl.readPixels(0, 0, r.w, r.h, gl.RGBA, gl.UNSIGNED_BYTE, out);
    return out;
  }
}

export const BLEND = { 5212: 0, 5216: 1, 5222: 2, 5226: 3, 5227: 4, 5220: 5, 5223: 5, 5233: 6, 5234: 6, 5235: 7, 5228: 8, 5240: 9 };
