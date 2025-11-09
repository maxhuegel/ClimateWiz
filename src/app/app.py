import streamlit as st
from streamlit.components.v1 import html

st.set_page_config(page_title="EmissionWiz", page_icon="🌍", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
<style>
#MainMenu, header, footer {visibility:hidden;}
.block-container {padding:0;}
html, body, .main, [data-testid="stAppViewContainer"] {height:100%; background:#000;}
</style>
""", unsafe_allow_html=True)

AUTO_ROTATE = True
ROT_SPEED = 0.2
LIGHT_INTENSITY = 1.1
NIGHT_SOFTNESS = 0.22

HTML = r"""
<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<style>html,body,#root{margin:0;height:100%;background:#000;overflow:hidden}</style>
<script src="https://unpkg.com/three@0.155.0/build/three.min.js"></script>
<script src="https://unpkg.com/globe.gl@2.33.1/dist/globe.gl.min.js"></script>
</head>
<body>
<div id="root"></div>
<script>
  const DAY_TEX_CANDIDATES = [
    'https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg',
    'https://cdn.jsdelivr.net/npm/three-globe/example/img/earth-blue-marble.jpg'
  ];
  const NIGHT_TEX_CANDIDATES = [
    'https://unpkg.com/three-globe/example/img/earth-night.jpg',
    'https://cdn.jsdelivr.net/npm/three-globe/example/img/earth-night.jpg'
  ];
  const BUMP_TEX  = 'https://unpkg.com/three-globe/example/img/earth-topology.png';
  const BG_TEX    = 'https://unpkg.com/three-globe/example/img/night-sky.png';

  const pickTexture = (urls) => new Promise(resolve => {
    const loader = new THREE.TextureLoader();
    const tryNext = (i) => {
      const url = urls[i];
      if (!url) { resolve(null); return; }
      loader.load(url, tex => { tex.colorSpace = THREE.SRGBColorSpace; resolve(tex); },
                      ()  => tryNext(i+1));
    };
    tryNext(0);
  });

  (async function init() {
    const dayTex   = await pickTexture(DAY_TEX_CANDIDATES);
    const nightTex = await pickTexture(NIGHT_TEX_CANDIDATES);

    const globe = Globe()(document.getElementById('root'))
      .globeImageUrl(DAY_TEX_CANDIDATES[0])
      .bumpImageUrl(BUMP_TEX)
      .backgroundImageUrl(BG_TEX)
      .showAtmosphere(true)
      .atmosphereColor('#88ccff')
      .atmosphereAltitude(0.18)
      .width(window.innerWidth)
      .height(window.innerHeight);

    globe.controls().autoRotate = __SPIN__;
    globe.controls().autoRotateSpeed = __SPEED__;
    globe.controls().addEventListener('start', () => globe.controls().autoRotate = false);
    globe.controls().addEventListener('end',   () => globe.controls().autoRotate = __SPIN__);

    const ambient = new THREE.AmbientLight(0x666666, 1.0);
    const sun     = new THREE.DirectionalLight(0xffffff, 0.9);
    sun.position.set(5, 3, 5);
    globe.scene().add(ambient);
    globe.scene().add(sun);

    fetch('https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson')
      .then(r => r.json())
      .then(geo => {
        globe
          .polygonsData(geo.features)
          .polygonAltitude(0.002)
          .polygonCapColor(() => 'rgba(0,0,0,0)')
          .polygonSideColor(() => 'rgba(0,0,0,0)')
          .polygonStrokeColor(() => 'rgba(255,255,255,120)')
          .polygonsTransitionDuration(300)
          .polygonLabel(({properties}) => properties.NAME);
      });
    const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
    globe.renderer().setPixelRatio(dpr);

    if (nightTex) {
      let R = 100;
      globe.scene().traverse(obj => {
        if (obj.isMesh && obj.geometry && obj.geometry.type === 'SphereGeometry') {
          const p = obj.geometry.parameters || {};
          if (typeof p.radius === 'number') R = p.radius;
        }
      });

      const nightGeom = new THREE.SphereGeometry(R * 1.001, 128, 128);
      const nightMat = new THREE.ShaderMaterial({
        uniforms: {
          uTex:        { value: nightTex },
          uSunDir:     { value: new THREE.Vector3().copy(sun.position).normalize() },
          uIntensity:  { value: __INTENSITY__ },
          uSoftness:   { value: __SOFTNESS__ }
        },
        vertexShader: `
          varying vec2 vUv;
          varying vec3 vNormalW;
          void main() {
            vUv = uv;
            vNormalW = normalize(normalMatrix * normal);
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
          }
        `,
        fragmentShader: `
          precision mediump float;
          uniform sampler2D uTex;
          uniform vec3 uSunDir;
          uniform float uIntensity;
          uniform float uSoftness;
          varying vec2 vUv;
          varying vec3 vNormalW;
          void main() {
            float d = dot(normalize(vNormalW), normalize(uSunDir));
            float nightFactor = clamp( (1.0 - d) * 0.5, 0.0, 1.0 );
            nightFactor = smoothstep(0.0, uSoftness, nightFactor);
            vec3 nightCol = texture2D(uTex, vUv).rgb * uIntensity;
            gl_FragColor = vec4(nightCol * nightFactor, nightFactor);
          }
        `,
        transparent: true,
        depthWrite: false,
        blending: THREE.AdditiveBlending
      });
      const nightMesh = new THREE.Mesh(nightGeom, nightMat);
      nightMesh.renderOrder = 2;
      globe.scene().add(nightMesh);

      const updateSunDir = () => {
        const cam = globe.camera();
        const dir = new THREE.Vector3(0,0,1).applyQuaternion(cam.quaternion);
        sun.position.copy(dir.clone().multiplyScalar(5));
        nightMat.uniforms.uSunDir.value.copy(sun.position).normalize();
      };
      globe.controls().addEventListener('change', updateSunDir);
      updateSunDir();
    }

    const gm = globe.globeMaterial();
    if (gm) {
      gm.color = new THREE.Color(0x90aaff);
      gm.roughness = 0.95; gm.metalness = 0.08;
    }

    window.addEventListener('resize', () => {
      globe.width(window.innerWidth); globe.height(window.innerHeight);
    });
  })();
</script>
</body>
</html>
"""

html(
    HTML.replace("__SPIN__", "true" if AUTO_ROTATE else "false")
    .replace("__SPEED__", str(float(ROT_SPEED)))
    .replace("__INTENSITY__", str(float(LIGHT_INTENSITY)))
    .replace("__SOFTNESS__", str(float(NIGHT_SOFTNESS))),
    height=800,
    scrolling=False
)
