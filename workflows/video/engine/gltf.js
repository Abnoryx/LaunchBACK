// glTF model layers (AE "ThreeDModelLayer") rendered with three.js, matching After Effects' Advanced 3D view.
// Maths measured against the reel (research/models3d): a glTF point v maps to AE layer space as U*(X,-Y,-Z),
// U = 508 px per unit; AE ignores the file's single scene-root transform; the model comp's default camera
// has zoom 1500; lighting is a neutral environment (no lights in the project).
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

export const U = 508;
export const ANCHOR_RAW = 552960; // AE stores model anchors as px * 552960 / U

export class ModelRenderer {
  constructor(w, h) {
    this.canvas = document.createElement('canvas');
    this.canvas.width = w; this.canvas.height = h;
    this.r = new THREE.WebGLRenderer({ canvas: this.canvas, alpha: true, antialias: true, preserveDrawingBuffer: true, premultipliedAlpha: true });
    this.r.setPixelRatio(1);
    this.r.setSize(w, h, false);
    this.r.outputColorSpace = THREE.SRGBColorSpace;
    this.r.toneMapping = THREE.NoToneMapping;
    this.r.setClearColor(0x000000, 0);
    this.scene = new THREE.Scene();
    const pm = new THREE.PMREMGenerator(this.r);
    this.scene.environment = pm.fromScene(new RoomEnvironment(), 0.04).texture;
    this.scene.environmentIntensity = 2.2; // calibrated: phone back panel ~#9D9D9D after the scene's Tint/Curves
    this.models = new Map();
    this.loader = new GLTFLoader();
    this.w = w; this.h = h;
  }

  async load(url, opts = {}) {
    if (this.models.has(url)) return this.models.get(url);
    const gltf = await this.loader.loadAsync(url);
    const root = gltf.scene;
    // AE ignores a single scene-root node's transform
    if (root.children.length === 1) { const c = root.children[0]; c.position.set(0, 0, 0); c.quaternion.identity(); c.scale.set(1, 1, 1); }
    const holder = new THREE.Group();
    holder.matrixAutoUpdate = false;
    holder.add(root);
    holder.visible = false;
    this.scene.add(holder);
    if (opts.screenTexture) await this.applyScreen(root, opts.screenTexture);
    this.models.set(url, holder);
    return holder;
  }

  // Put an image on the material named `Material.001` (the iPhone screen), with planar UVs over its bounds.
  async applyScreen(root, url, materialName = 'Material.001') {
    const tex = await new THREE.TextureLoader().loadAsync(url);
    tex.colorSpace = THREE.SRGBColorSpace; tex.flipY = false;
    root.updateMatrixWorld(true);
    root.traverse((o) => {
      if (!o.isMesh || o.material?.name !== materialName) return;
      const g = o.geometry, pos = g.attributes.position, box = new THREE.Box3().setFromBufferAttribute(pos);
      const uv = new Float32Array(pos.count * 2);
      for (let i = 0; i < pos.count; i++) {
        const v = new THREE.Vector3().fromBufferAttribute(pos, i).applyMatrix4(o.matrixWorld);
        uv[i * 2] = 0; uv[i * 2 + 1] = 0;
        uv[i * 2] = v.x; uv[i * 2 + 1] = v.y;
      }
      // normalise in world xy (screen plane faces +Z)
      let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
      for (let i = 0; i < pos.count; i++) { x0 = Math.min(x0, uv[i * 2]); x1 = Math.max(x1, uv[i * 2]); y0 = Math.min(y0, uv[i * 2 + 1]); y1 = Math.max(y1, uv[i * 2 + 1]); }
      for (let i = 0; i < pos.count; i++) { uv[i * 2] = (uv[i * 2] - x0) / (x1 - x0); uv[i * 2 + 1] = 1 - (uv[i * 2 + 1] - y0) / (y1 - y0); }
      g.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
      o.material = new THREE.MeshStandardMaterial({ map: tex, emissiveMap: tex, emissive: 0xffffff, emissiveIntensity: 0.9, roughness: 0.35, metalness: 0 });
    });
  }

  // aeWorld: column-major 4x4 AE world matrix of the model layer (comp space, px). zoom: comp camera zoom.
  // camView: optional AE camera view matrix (comp space) when the model comp has a camera.
  render(url, aeWorld, zoom = 1500, compW = this.w, compH = this.h) {
    const holder = this.models.get(url);
    if (!holder) return null;
    for (const m of this.models.values()) m.visible = false;
    holder.visible = true;
    // C: AE comp -> three  (x-W/2, -(y-H/2), -z);  F: glTF -> AE layer space U*(X,-Y,-Z)
    const C = new THREE.Matrix4().set(1, 0, 0, -compW / 2, 0, -1, 0, compH / 2, 0, 0, -1, 0, 0, 0, 0, 1);
    const M = new THREE.Matrix4().fromArray(aeWorld);
    const F = new THREE.Matrix4().makeScale(U, -U, -U);
    holder.matrix.copy(C).multiply(M).multiply(F);
    holder.matrixWorldNeedsUpdate = true;
    const fov = (2 * Math.atan(compH / 2 / zoom) * 180) / Math.PI;
    if (!this.cam) this.cam = new THREE.PerspectiveCamera(fov, compW / compH, 1, 100000);
    this.cam.fov = fov; this.cam.aspect = compW / compH; this.cam.position.set(0, 0, zoom); this.cam.lookAt(0, 0, 0);
    this.cam.near = 1; this.cam.far = 200000; this.cam.updateProjectionMatrix();
    this.r.render(this.scene, this.cam);
    return this.canvas;
  }
}
