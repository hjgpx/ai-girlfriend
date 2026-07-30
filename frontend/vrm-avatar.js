import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { VRMLoaderPlugin, VRMUtils } from '@pixiv/three-vrm';

let renderer, scene, camera, clock;
let currentVrm = null;
let mouthValue = 0;
let targetMouth = 0;
let blinkValue = 0;
let nextBlinkTime = 0;
let isSpeakingFlag = false;

export function initVRM(containerId = 'vrmContainer', canvasId = 'vrmCanvas') {
  const container = document.getElementById(containerId);
  const canvas = document.getElementById(canvasId);
  if (!container || !canvas) {
    console.error('找不到 vrm 容器或 canvas');
    return;
  }

  const width = container.clientWidth || 400;
  const height = container.clientHeight || 500;

  renderer = new THREE.WebGLRenderer({
    canvas,
    alpha: true,
    antialias: true,
  });
  renderer.setSize(width, height);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;

  scene = new THREE.Scene();

  const light = new THREE.DirectionalLight(0xffffff, Math.PI);
  light.position.set(1, 1.5, 1).normalize();
  scene.add(light);
  scene.add(new THREE.AmbientLight(0xffffff, 0.6));

  camera = new THREE.PerspectiveCamera(30, width / height, 0.1, 20);
  camera.position.set(0, 1.35, 1.8);
  camera.lookAt(0, 1.25, 0);

  clock = new THREE.Clock();

  loadVRM('./models/xiaonuan.vrm');

  window.addEventListener('resize', () => {
    const w = container.clientWidth;
    const h = container.clientHeight;
    if (w === 0 || h === 0) return;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  });

  animate();
}

function loadVRM(url) {
  const loader = new GLTFLoader();
  loader.register((parser) => new VRMLoaderPlugin(parser));

  loader.load(
    url,
    (gltf) => {
      const vrm = gltf.userData.vrm;

      VRMUtils.removeUnnecessaryVertices(gltf.scene);
      VRMUtils.combineSkeletons(gltf.scene);
      VRMUtils.combineMorphs(vrm);
      VRMUtils.rotateVRM0(vrm);

      vrm.scene.traverse((obj) => {
        obj.frustumCulled = false;
      });

      vrm.scene.position.set(0, 0, 0);
      vrm.scene.rotation.y = Math.PI;

      if (currentVrm) {
        scene.remove(currentVrm.scene);
      }
      scene.add(vrm.scene);
      currentVrm = vrm;
      // 把手臂从 T 字姿势放下
const humanoid = vrm.humanoid;
if (humanoid) {
  const leftUpperArm = humanoid.getNormalizedBoneNode('leftUpperArm');
  const rightUpperArm = humanoid.getNormalizedBoneNode('rightUpperArm');
  const leftLowerArm = humanoid.getNormalizedBoneNode('leftLowerArm');
  const rightLowerArm = humanoid.getNormalizedBoneNode('rightLowerArm');

  if (leftUpperArm) leftUpperArm.rotation.z = 1.2;
  if (rightUpperArm) rightUpperArm.rotation.z = -1.2;
  if (leftLowerArm) leftLowerArm.rotation.y = 0.3;
  if (rightLowerArm) rightLowerArm.rotation.y = -0.3;
}

      const tip = document.getElementById('loadingTip');
      if (tip) tip.style.display = 'none';

      console.log('VRM 加载成功');
    },
    (progress) => {
      const p = progress.total ? (progress.loaded / progress.total) * 100 : 0;
      const tip = document.getElementById('loadingTip');
      if (tip) tip.textContent = `小暖加载中... ${p.toFixed(0)}%`;
    },
    (err) => {
      console.error('VRM 加载失败', err);
      const tip = document.getElementById('loadingTip');
      if (tip) tip.textContent = '模型加载失败，请检查 models/xiaonuan.vrm';
    }
  );
}

function animate() {
  requestAnimationFrame(animate);
  const delta = clock.getDelta();
  const t = clock.elapsedTime;

  if (currentVrm) {
    mouthValue += (targetMouth - mouthValue) * Math.min(1, delta * 12);
    currentVrm.expressionManager.setValue('aa', mouthValue);
    currentVrm.expressionManager.setValue('happy', isSpeakingFlag ? 0.6 : 0.2);
    currentVrm.expressionManager.setValue('relaxed', isSpeakingFlag ? 0.0 : 0.3);

    if (t > nextBlinkTime) {
      blinkValue = 1;
      nextBlinkTime = t + 2.5 + Math.random() * 3;
    }
    blinkValue *= 0.85;
    currentVrm.expressionManager.setValue('blink', blinkValue);

    currentVrm.update(delta);
  }

  if (renderer && scene && camera) {
    renderer.render(scene, camera);
  }
}

export function startSpeaking() {
  isSpeakingFlag = true;
}

export function stopSpeaking() {
  isSpeakingFlag = false;
  targetMouth = 0;
}

export function setMouthOpen(volume) {
  targetMouth = Math.min(1, volume * 3.8);
}

export function connectAudio(audioElement) {
  const AudioContext = window.AudioContext || window.webkitAudioContext;
  const ctx = new AudioContext();
  const source = ctx.createMediaElementSource(audioElement);
  const analyser = ctx.createAnalyser();
  analyser.fftSize = 256;
  source.connect(analyser);
  analyser.connect(ctx.destination);

  const data = new Uint8Array(analyser.frequencyBinCount);

  function tick() {
    if (!isSpeakingFlag) return;
    analyser.getByteFrequencyData(data);

    let sum = 0;
    const len = Math.floor(data.length * 0.4);
    for (let i = 0; i < len; i++) sum += data[i];
    const volume = sum / len / 255;

    setMouthOpen(volume);
    requestAnimationFrame(tick);
  }

  audioElement.addEventListener('play', () => {
    startSpeaking();
    if (ctx.state === 'suspended') ctx.resume();
    tick();
  });

  audioElement.addEventListener('ended', () => {
    stopSpeaking();
  });
  audioElement.addEventListener('pause', () => {
    stopSpeaking();
  });
}

// 页面加载后自动初始化
initVRM();