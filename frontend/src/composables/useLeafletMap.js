import { ref } from 'vue';

const DEFAULT_CENTER = [47.2852069, 8.5653081];

export function useLeafletMap() {
    const mapElement = ref(null);
    let map = null;
    let marker = null;

    const initMap = () => {
        if (!window.L || !mapElement.value || map) {
            return;
        }

        map = window.L.map(mapElement.value, {
            minZoom: 2.5,
            maxZoom: 20,
            maxBounds: [[-90, -180], [90, 180]],
            maxBoundsViscosity: 1.0
        }).setView(DEFAULT_CENTER, 10);

        marker = window.L.marker(DEFAULT_CENTER).addTo(map);

        const defaultMaplayer = new window.L.tileLayer.provider('OpenStreetMap.Mapnik');
        const lightMaplayer = new window.L.tileLayer.provider('CartoDB.Positron');
        const darkMaplayer = new window.L.tileLayer.provider('CartoDB.DarkMatter');
        const satelliteMaplayer = new window.L.tileLayer.provider('Esri.WorldImagery');

        const baseLayers = {
            Default: defaultMaplayer,
            Light: lightMaplayer,
            Dark: darkMaplayer,
            Satellite: satelliteMaplayer
        };

        window.L.control.layers(baseLayers).addTo(map);
        map.addLayer(defaultMaplayer);
        marker.setLatLng([0, 0]);
    };

    const setMarkerPosition = (lat, lon) => {
        const latitude = Number(lat);
        const longitude = Number(lon);

        if (!marker || Number.isNaN(latitude) || Number.isNaN(longitude)) {
            return;
        }

        marker.setLatLng([latitude, longitude]);
    };

    const destroyMap = () => {
        if (map) {
            map.remove();
        }
        map = null;
        marker = null;
    };

    return {
        mapElement,
        initMap,
        setMarkerPosition,
        destroyMap
    };
}
