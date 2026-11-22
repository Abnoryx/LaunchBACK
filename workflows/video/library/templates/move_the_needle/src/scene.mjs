import * as THREE from 'three';
import {sampleEdge} from './shot.mjs';

const fonts = {
  'Arimo Bold': '700 SIZEpx Arimo',
  'Bodoni Moda Bold Italic': 'italic 700 SIZEpx "Bodoni Moda"',
};
const vertex = `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

function rgb(hex) {
  const value = Number.parseInt(hex.slice(1), 16);
  return new THREE.Color((value >> 16) / 255, (value >> 8 & 255) / 255, (value & 255) / 255);
}

export async function createScene(canvas, shot) {
  const {width, height} = shot;
  const camera = new THREE.OrthographicCamera(0, width, height, 0, 0.1, 100);
  camera.position.z = 10;
  const renderer = new THREE.WebGLRenderer({canvas, alpha: false, preserveDrawingBuffer: true, antialias: true});
  renderer.outputColorSpace = THREE.LinearSRGBColorSpace;
  renderer.setSize(width, height, false);
  renderer.autoClear = false;

  await Promise.all(Object.values(fonts).map((font) => document.fonts.load(font.replace('SIZE', '40'))));
  const loader = new THREE.TextureLoader();
  const assets = [...new Set(shot.at(0).layers.filter(({kind}) => kind === 'image').map(({asset}) => asset))];
  const textures = new Map(await Promise.all(assets.map(async (asset) => [asset, await loader.loadAsync(asset)])));
  const base = new THREE.Scene();
  const type = new THREE.Scene();
  const above = new THREE.Scene();
  const composite = new THREE.Scene();
  const target = () => new THREE.WebGLRenderTarget(width, height, {
    depthBuffer: false, stencilBuffer: false, minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter,
  });
  const plateTarget = target();
  const textTarget = target();
  const unitQuad = new THREE.PlaneGeometry(1, 1);
  const fullQuad = new THREE.PlaneGeometry(width, height);
  const blend = new THREE.ShaderMaterial({
    uniforms: {uPlate: {value: plateTarget.texture}, uType: {value: textTarget.texture}},
    vertexShader: vertex,
    fragmentShader: `
      uniform sampler2D uPlate;
      uniform sampler2D uType;
      varying vec2 vUv;
      void main() {
        vec3 base = texture2D(uPlate, vUv).rgb;
        vec4 type = texture2D(uType, vUv);
        gl_FragColor = vec4(base + type.rgb - 2.0 * base * type.rgb, 1.0);
      }
    `,
    depthTest: false, depthWrite: false,
  });
  const compositeMesh = new THREE.Mesh(fullQuad, blend);
  compositeMesh.position.set(width / 2, height / 2, 0);
  composite.add(compositeMesh);

  const cutouts = new Map();
  const registry = new Map();
  const ctxMeasure = document.createElement('canvas').getContext('2d');

  function trackedWidth(ctx, string, tracking) {
    return Array.from(string).reduce((sum, character) => sum + ctx.measureText(character).width + tracking, 0);
  }

  function textTexture(layer) {
    const {text, size, font, color, tracking = 0} = layer;
    const key = JSON.stringify([text,size,font,color,tracking]);
    if (cutouts.has(key)) return cutouts.get(key);
    const cssFont = (fonts[font] ?? '700 SIZEpx sans-serif').replace('SIZE', size);
    const spacing = size * tracking / 1000;
    ctxMeasure.font = cssFont;
    const advance = trackedWidth(ctxMeasure, text, spacing);
    const pad = Math.ceil(size * .25) + 4;
    const baseline = Math.ceil(size * 1.25);
    const w = Math.ceil(Math.max(0, advance) + pad * 2);
    const h = baseline + pad + Math.ceil(size * .28);
    const bitmap = document.createElement('canvas');
    bitmap.width = w * 2;
    bitmap.height = h * 2;
    const ctx = bitmap.getContext('2d');
    ctx.scale(2, 2);
    ctx.font = cssFont;
    ctx.fillStyle = color;
    let x = pad;
    for (const character of text) {
      ctx.fillText(character, x, baseline);
      x += ctx.measureText(character).width + spacing;
    }
    const texture = new THREE.CanvasTexture(bitmap);
    texture.minFilter = THREE.LinearFilter;
    texture.generateMipmaps = false;
    const result = {texture, w, h, advance, pad, baseline, cssFont, spacing};
    cutouts.set(key, result);
    return result;
  }

  function meshFor(layer, scene, order) {
    let item = registry.get(layer.id);
    if (item) return item;
    const group = new THREE.Group();
    const attributes = [undefined, undefined];
    const standard = () => new THREE.MeshBasicMaterial({transparent: true, depthTest: false, depthWrite: false});
    let mesh;
    if (layer.kind === 'wave') {
      const data = new Float32Array(height * 4);
      const edge = new THREE.DataTexture(data, 1, height, THREE.RGBAFormat, THREE.FloatType);
      edge.needsUpdate = true;
      const material = new THREE.ShaderMaterial({
        transparent: true, depthTest: false, depthWrite: false, vertexShader: vertex,
        uniforms: {uEdges:{value:edge}, uWidth:{value:width}, uColor:{value:rgb(layer.color)}, uFeather:{value:layer.feather}, uOpacity:{value:layer.opacity}, uHalo:{value:layer.halo ?? 0}},
        fragmentShader: `
          varying vec2 vUv;
          uniform sampler2D uEdges;
          uniform float uWidth, uFeather, uOpacity, uHalo;
          uniform vec3 uColor;
          void main() {
            vec2 edges = texture2D(uEdges, vec2(.5, 1.0 - vUv.y)).rg;
            float x = vUv.x * uWidth;
            float feather = max(0.75, uFeather);
            float a = smoothstep(edges.x - feather, edges.x + feather, x);
            float b = smoothstep(edges.y - feather, edges.y + feather, x);
            float halo = max(0.0, uHalo);
            float spread = max(0.75, feather + halo);
            float soft = smoothstep(edges.x - spread, edges.x + spread, x)
                       - smoothstep(edges.y - spread, edges.y + spread, x);
            float core = max(0.0, a - b);
            float coverage = max(core, soft * step(0.5, halo) * 0.22);
            gl_FragColor = vec4(uColor, coverage * uOpacity);
          }
        `,
      });
      mesh = new THREE.Mesh(fullQuad, material);
      mesh.position.set(width / 2, height / 2, 0);
      attributes[0] = data;
      attributes[1] = edge;
    } else if (layer.kind === 'polygon') {
      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array((layer.points.length - 2) * 9), 3));
      const material = standard();
      material.color.copy(rgb(layer.color));
      material.side = THREE.DoubleSide;
      mesh = new THREE.Mesh(geometry, material);
    } else {
      mesh = new THREE.Mesh(unitQuad, standard());
    }
    mesh.frustumCulled = false;
    mesh.renderOrder = order;
    group.add(mesh);
    scene.add(group);
    item = {group, mesh, data: attributes[0], edge: attributes[1]};
    registry.set(layer.id, item);
    return item;
  }

  function update(layer, scene, order) {
    const {group, mesh, data, edge} = meshFor(layer, scene, order);
    group.visible = layer.opacity > 0 && (layer.kind !== 'text' || layer.text.length > 0);
    if (!group.visible) return;
    if (layer.kind === 'wave') {
      for (let y = 0; y < height; y++) {
        data[4 * y] = sampleEdge(layer.left, y + .5);
        data[4 * y + 1] = sampleEdge(layer.right, y + .5);
      }
      edge.needsUpdate = true;
      mesh.material.uniforms.uOpacity.value = layer.opacity;
      mesh.material.uniforms.uFeather.value = layer.feather;
      mesh.material.uniforms.uHalo.value = layer.halo ?? 0;
      return;
    }
    mesh.material.opacity = layer.opacity;
    if (layer.kind === 'polygon') {
      const buffer = mesh.geometry.attributes.position;
      for (let i = 1; i < layer.points.length - 1; i++) {
        for (const [j, point] of [layer.points[0], layer.points[i], layer.points[i + 1]].entries()) {
          buffer.setXYZ((i - 1) * 3 + j, point[0], height - point[1], 0);
        }
      }
      buffer.needsUpdate = true;
      return;
    }
    const angle = -(layer.angle ?? 0) * Math.PI / 180;
    group.rotation.z = angle;
    if (layer.kind === 'image') {
      const [u, v] = layer.anchor ?? [.5, .5];
      group.position.set(layer.x, height - layer.y, 0);
      mesh.position.set((.5 - u) * layer.width, (v - .5) * layer.height, 0);
      mesh.scale.set(layer.width, layer.height, 1);
      if (!mesh.material.map) {
        mesh.material.map = textures.get(layer.asset);
        mesh.material.needsUpdate = true;
      }
      return;
    }
    const glyph = textTexture(layer);
    ctxMeasure.font = glyph.cssFont;
    const after = layer.after ? trackedWidth(ctxMeasure, layer.after, glyph.spacing) : 0;
    const textAlign = layer.align === 'center' ? -glyph.advance / 2 : 0;
    group.position.set(layer.x + after, height - layer.y, 0);
    mesh.position.set(glyph.w / 2 - glyph.pad + textAlign, glyph.baseline - glyph.h / 2, 0);
    mesh.scale.set(glyph.w, glyph.h, 1);
    if (mesh.material.map !== glyph.texture) {
      mesh.material.map = glyph.texture;
      mesh.material.needsUpdate = true;
    }
  }

  function renderFrame(frameIndex) {
    const state = shot.at(frameIndex);
    let cut = false;
    for (const [order, layer] of state.layers.entries()) {
      if (layer.blend === 'exclusion') {
        cut = true;
        update(layer, type, order);
      } else update(layer, cut ? above : base, order);
    }
    renderer.setRenderTarget(plateTarget);
    renderer.setClearColor(0, 1);
    renderer.clear();
    renderer.render(base, camera);
    renderer.setRenderTarget(textTarget);
    renderer.setClearColor(0, 0);
    renderer.clear();
    renderer.render(type, camera);
    renderer.setRenderTarget(null);
    renderer.render(composite, camera);
    renderer.render(above, camera);
    return state;
  }

  return {renderFrame};
}
