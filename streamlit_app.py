import streamlit as st
import requests
import datetime
from urllib.parse import urlencode

# Interfaz de entrada
st.title("Buscador de Vuelos por Compañía Aérea (vía SerpApi)")

with st.form("flight_form"):
    departure_id = st.text_input("Origen (código IATA)", "AEP")
    arrival_id = st.text_input("Destino (código IATA)", "MDZ")
    date = st.date_input("Fecha del vuelo", datetime.date.today())
    passengers = st.number_input("Cantidad de pasajeros", min_value=1, max_value=9, value=1)
    airline_code = st.text_input("Código IATA de la compañía aérea (ej: AR, LA, FO)", "AR")
    api_key = st.text_input("Tu API Key de SerpApi", type="password")
    submitted = st.form_submit_button("Buscar")

if submitted:
    with st.spinner("Consultando SerpApi..."):
        params = {
            "engine": "google_flights",
            "departure_id": departure_id.upper(),
            "arrival_id": arrival_id.upper(),
            "outbound_date": date.strftime("%Y-%m-%d"),
            "adults": passengers,
            "currency": "ARS",
            "type": "2",  # One-way explícito
            "api_key": api_key
        }
        url = "https://serpapi.com/search"

        # Mostrar URL de debugging
        st.code(f"Request URL: {url}?{urlencode(params)}")

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            st.error(f"Error en la solicitud: {response.status_code} - {response.text}")
        except Exception as e:
            st.error(f"Ocurrió un error inesperado: {str(e)}")
        else:
            data = response.json()
            flights = data.get("best_flights", []) + data.get("other_flights", [])

            filtered = []
            for option in flights:
                all_match = all(
                    flight.get("flight_number", "").upper().startswith(airline_code.upper())
                    for flight in option["flights"]
                )
                if all_match:
                    first = option["flights"][0]
                    last = option["flights"][-1]
                    filtered.append({
                        "Aerolínea": first.get("airline"),
                        "Vuelos": ", ".join(f["flight_number"] for f in option["flights"]),
                        "Salida": f"{first['departure_airport']['name']} ({first['departure_airport']['id']}) - {first['departure_airport']['time']}",
                        "Llegada": f"{last['arrival_airport']['name']} ({last['arrival_airport']['id']}) - {last['arrival_airport']['time']}",
                        "Duración (min)": option.get("total_duration"),
                        "Precio ARS": option.get("price")
                    })

            if filtered:
                st.success(f"Se encontraron {len(filtered)} opciones completas de la aerolínea {airline_code.upper()}:")
                st.dataframe(filtered)
            else:
                st.warning("No se encontraron vuelos disponibles con todos los tramos operados por la aerolínea seleccionada.")
