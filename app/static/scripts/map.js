let map = L.map('map', {
    minZoom: 2.5,
    maxZoom: 20,
    maxBounds: [[-90, -180], [90, 180]],  // World bounds
    maxBoundsViscosity: 1.0
}).setView([47.2852069, 8.5653081], 10);

let marker = L.marker([47.2852069, 8.5653081]).addTo(map)

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
}).addTo(map);

const defaultMaplayer = new L.tileLayer.provider('OpenStreetMap.Mapnik');
const lightMaplayer = new L.tileLayer.provider('CartoDB.Positron');
const darkMaplayer = new L.tileLayer.provider('CartoDB.DarkMatter');
const satelliteMaplayer = new L.tileLayer.provider('Esri.WorldImagery');

const baseLayers = {
    "Default": defaultMaplayer,
    "Light": lightMaplayer,
    "Dark": darkMaplayer,
    "Satellite": satelliteMaplayer
}

// Layercontrol
const layerControl = L.control.layers(baseLayers).addTo(map);
map.addLayer(defaultMaplayer);

marker.setLatLng([0,0]);