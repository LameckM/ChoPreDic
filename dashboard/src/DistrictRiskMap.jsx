
import { useEffect, useMemo, useState, useCallback } from "react";
import { MapContainer, TileLayer, GeoJSON } from "react-leaflet";
import "leaflet/dist/leaflet.css";

const RISK_COLORS = {
  high: "#dc655b",
  medium: "#e7a84b",
  low: "#36a889",
};

const NO_MATCH_COLOR = "#aebbb5";

// Normalise punctuation and spacing without changing the original names.
function normaliseName(name) {
  return String(name || "")
    .toLowerCase()
    .replace(/['’\s-]/g, "");
}

// Explicit historical-name matching.
const DISTRICT_ALIASES = {
  chienge: "chiengi",
  chiengi: "chiengi",
  "shang'ombo": "shangombo",
  shangombo: "shangombo",
};

function getDistrictKey(name) {
  const normalised = normaliseName(name);
  return DISTRICT_ALIASES[normalised] || normalised;
}

export default function DistrictRiskMap({
  districts = [],
  onSelectDistrict,
}) {
  const [geoData, setGeoData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    fetch("/data/zambia_districts_2017.geojson")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Could not load the district boundary file.");
        }
        return response.json();
      })
      .then((result) => {
        if (!cancelled) {
          if (!result.features || !Array.isArray(result.features)) {
            throw new Error("The district boundary file is not valid GeoJSON.");
          }
          setGeoData(result);
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const districtLookup = useMemo(() => {
    const lookup = new Map();

    districts.forEach((district) => {
      lookup.set(getDistrictKey(district.district), district);
    });

    return lookup;
  }, [districts]);

  const getRiskForFeature = useCallback(
    (feature) => {
      const name = feature.properties?.NAME1_;
      return districtLookup.get(getDistrictKey(name));
    },
    [districtLookup]
  );

  const styleFeature = useCallback(
    (feature) => {
      const district = getRiskForFeature(feature);
      const level = district?.level?.toLowerCase();

      return {
        fillColor: RISK_COLORS[level] || NO_MATCH_COLOR,
        fillOpacity: 0.78,
        color: "#ffffff",
        weight: 1,
        opacity: 1,
      };
    },
    [getRiskForFeature]
  );

  const handleEachFeature = useCallback(
    (feature, layer) => {
      const name = feature.properties?.NAME1_ || "Unknown district";
      const district = getRiskForFeature(feature);
      const level = district?.level?.toLowerCase();

      layer.bindTooltip(
        district
          ? `${name} — ${level} risk`
          : `${name} — no matching prediction`,
        { sticky: true }
      );

      layer.on({
        click: () => {
          if (district) onSelectDistrict?.(district);
        },
        mouseover: (event) => {
          event.target.setStyle({
            weight: 2.5,
            color: "#294d43",
            fillOpacity: 0.95,
          });
          event.target.bringToFront();
        },
        mouseout: (event) => {
          event.target.setStyle(styleFeature(feature));
        },
      });
    },
    [getRiskForFeature, onSelectDistrict, styleFeature]
  );

  if (error) {
    return <div className="map-error">{error}</div>;
  }

  if (!geoData) {
    return <div className="map-loading">Loading district map...</div>;
  }

  return (
    <div className="risk-map-container">
      <div className="risk-map">
        <MapContainer
          center={[-13.5, 27.8]}
          zoom={6}
          minZoom={5}
          maxZoom={10}
          scrollWheelZoom={false}
          style={{ height: "100%", width: "100%" }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <GeoJSON
            key={`${geoData.features.length}-${districts.length}`}
            data={geoData}
            style={styleFeature}
            onEachFeature={handleEachFeature}
          />
        </MapContainer>
      </div>

      <div className="risk-map-legend">
        <span><i style={{ background: RISK_COLORS.high }} /> High risk</span>
        <span><i style={{ background: RISK_COLORS.medium }} /> Medium risk</span>
        <span><i style={{ background: RISK_COLORS.low }} /> Low risk</span>
        <span><i style={{ background: NO_MATCH_COLOR }} /> No matching prediction</span>
      </div>

      <p className="risk-map-note">
        Historical district boundaries and 2019 forecast classifications.
        Select a district to view its existing assessment.
      </p>
    </div>
  );
}
