// ======= Config =======
const API_BASE = "http://localhost:5000"; 
const OSRM_BASE = "https://router.project-osrm.org";

// ======= Estado =======
let map, sitiosGlobal = [];
let markers = [];
let originFromMap = null;
let originMarker = null;
let routeLayer = null;

// ======= Init =======
async function init() {
  map = L.map('map').setView([-4.01, -80.05], 13);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap'
  }).addTo(map);

  map.on('click', (ev) => {
    const pickOnMap = document.getElementById('pickOnMap').checked;
    if (!pickOnMap) return;
    originFromMap = ev.latlng;
    if (originMarker) originMarker.remove();
    originMarker = L.marker(originFromMap, { title: 'Origen' }).addTo(map);
  });

  await cargarSitios();
  prepararControles();
}
document.addEventListener('DOMContentLoaded', init);

// ======= Datos/UI =======
async function cargarSitios() {
  const r = await fetch(`${API_BASE}/sitios`);
  const sitios = await r.json();
  sitiosGlobal = sitios;

  const destinoSelect = document.getElementById('destinoSelect');
  destinoSelect.innerHTML = `<option value="">— Selecciona destino —</option>`;

  const contenedor = document.getElementById('contenedor-cards');
  contenedor.innerHTML = "";

  sitios.forEach((s, idx) => {
    const m = L.marker([s.lat, s.lon], { title: s.nombre }).addTo(map)
      .bindPopup(`<b>${s.nombre}</b><br>${s.descripcion}`);
    markers.push(m);

    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = `
      <img src="${s.imagen || 'https://via.placeholder.com/300x180'}" alt="${s.nombre}">
      <div class="card-content">
        <h3>${s.nombre}</h3>
        <p>${s.descripcion}</p>
        <p><strong>Categoría:</strong> ${s.categoria || '-'}</p>
        <p><strong>Estado de vía:</strong> ${s.estado_via || '-'}</p>
        <div class="card-actions">
          <label>
            <input type="checkbox" class="chkWaypoint" data-id="${s._id}">
            Agregar a ruta
          </label>
          <button onclick="verEnMapa(${idx})">Ver en mapa</button>
        </div>
      </div>
    `;
    contenedor.appendChild(card);

    const opt = document.createElement('option');
    opt.value = s._id;
    opt.textContent = s.nombre;
    destinoSelect.appendChild(opt);
  });
}

function verEnMapa(i) {
  map.setView(markers[i].getLatLng(), 15);
  markers[i].openPopup();
}

function prepararControles() {
  const useGeoloc = document.getElementById('useGeoloc');
  const pickOnMap = document.getElementById('pickOnMap');
  const calcBtn = document.getElementById('calcBtn');
  const limpiarBtn = document.getElementById('limpiarBtn');

  useGeoloc.addEventListener('change', () => {
    if (useGeoloc.checked) {
      pickOnMap.checked = false;
      originFromMap = null;
      if (originMarker) { originMarker.remove(); originMarker = null; }
    }
  });

  pickOnMap.addEventListener('change', () => {
    if (pickOnMap.checked) {
      useGeoloc.checked = false;
      alert("Haz clic en el mapa para fijar el ORIGEN.");
    } else {
      originFromMap = null;
      if (originMarker) { originMarker.remove(); originMarker = null; }
    }
  });

  calcBtn.addEventListener('click', calcularRutaOSRM);
  limpiarBtn.addEventListener('click', limpiarRuta);
}

function limpiarRuta() {
  if (routeLayer) { routeLayer.remove(); routeLayer = null; }
  document.getElementById("resumenRuta").innerHTML = "";
  document.querySelectorAll(".chkWaypoint").forEach(chk => chk.checked = false);
  originFromMap = null;
  if (originMarker) { originMarker.remove(); originMarker = null; }
}

// ======= Helpers =======
function getCurrentPosition() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) return reject(new Error("Geolocalización no disponible"));
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve(L.latLng(pos.coords.latitude, pos.coords.longitude)),
      (err) => reject(err),
      { enableHighAccuracy: true, timeout: 8000 }
    );
  });
}

// ======= Routing con OSRM (optimizado) =======
async function calcularRutaOSRM() {
  const destinoId = document.getElementById("destinoSelect").value;
  const useGeoloc = document.getElementById("useGeoloc").checked;

  if (!destinoId) return alert("Selecciona un destino final.");

  // Origen
  let origin = null;
  if (originFromMap) origin = originFromMap;
  else if (useGeoloc) {
    try { origin = await getCurrentPosition(); }
    catch { return alert("Activa permisos de ubicación o elige origen en el mapa."); }
  } else {
    return alert("Elige un origen (ubicación o clic en el mapa).");
  }

  // Destino
  const destino = sitiosGlobal.find(s => s._id === destinoId);
  if (!destino) return alert("Destino inválido.");

  // Waypoints
  const seleccionados = Array.from(document.querySelectorAll(".chkWaypoint"))
    .filter(chk => chk.checked)
    .map(chk => chk.getAttribute("data-id"))
    .filter(id => id !== destinoId);

  // Construimos lista: [origen, ...wps, destino]
  const coords = [];
  coords.push([origin.lng, origin.lat]); // OSRM espera lon,lat
  seleccionados.forEach(id => {
    const s = sitiosGlobal.find(x => x._id === id);
    coords.push([s.lon, s.lat]);
  });
  coords.push([destino.lon, destino.lat]);

  if (coords.length < 2) return alert("Selecciona al menos origen y destino.");

  // OSRM Trip optimiza el orden de puntos intermedios
  const coordStr = coords.map(c => `${c[0]},${c[1]}`).join(';');

// después (agrega geometries=geojson)
const url = `${OSRM_BASE}/trip/v1/driving/${coordStr}`
          + `?source=first&destination=last&roundtrip=false`
          + `&steps=true&overview=full&geometries=geojson`;

  let data;
  try {
    const r = await fetch(url);
    data = await r.json();
  } catch (e) {
    console.error(e);
    return alert("No se pudo contactar al servicio de rutas.");
  }

  if (data.code !== "Ok" || !data.trips || !data.trips.length) {
    console.error("OSRM trip error:", data);
    return alert("No se pudo calcular la ruta (OSRM).");
  }

  const trip = data.trips[0]; // ruta optimizada
  const geo = L.geoJSON(trip.geometry);
  if (routeLayer) routeLayer.remove();
  routeLayer = geo.addTo(map);
  map.fitBounds(geo.getBounds(), { padding: [40, 40] });

  // Resumen
  const distanciaKm = (trip.distance / 1000).toFixed(1);
  const durMin = Math.round(trip.duration / 60);

  // Orden (waypoints) devuelto por OSRM en data.waypoints
  // Primero y último ya son origen/destino por los params
  const names = ["Origen"];
  // Los intermedios vienen reordenados; mapéalos contra tus sitios:
  // data.waypoints incluye todos; salta idx 0 (origen) y el último (destino)
  for (let i = 1; i < data.waypoints.length - 1; i++) {
    const wp = data.waypoints[i];
    // wp.name puede ser pobre; buscamos el más cercano en tus sitios
    const nearest = nearestSite(wp.location[1], wp.location[0]);
    names.push(nearest?.nombre || `Parada ${i}`);
  }
  names.push(destino.nombre);

  const lista = names.map((n, i) => `${i+1}. ${n}`).join("<br/>");
  document.getElementById("resumenRuta").innerHTML = `
    <strong>Orden optimizado:</strong><br/>
    ${lista}<br/><br/>
    <strong>Distancia total:</strong> ${distanciaKm} km<br/>
    <strong>Duración estimada:</strong> ${durMin} min
  `;
}

function nearestSite(lat, lon) {
  let best = null, bestD = Infinity;
  for (const s of sitiosGlobal) {
    const d = Math.hypot(s.lat - lat, s.lon - lon);
    if (d < bestD) { bestD = d; best = s; }
  }
  return best;
}
