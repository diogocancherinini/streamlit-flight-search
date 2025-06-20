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
    passengers = st.number_input("Cantidad de pasajeros (ADT + CNN)", min_value=1, max_value=9, value=1)
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
                    legs = []
                    connection_time_str = ""
                    flights_list = option["flights"]

                    for flight in flights_list:
                        leg_info = (
                            f"- Vuelo {flight['flight_number']}: {flight['departure_airport']['id']}"
                            f" ({flight['departure_airport']['time']}) → {flight['arrival_airport']['id']}"
                            f" ({flight['arrival_airport']['time']})"
                        )
                        legs.append(leg_info)

                    # Calcular tiempo de conexión si hay más de un tramo
                    if len(flights_list) > 1:
                        arrival_time_str = flights_list[0]["arrival_airport"]["time"]
                        departure_time_str = flights_list[1]["departure_airport"]["time"]
                        fmt = "%Y-%m-%d %H:%M"
                        arrival_dt = datetime.datetime.strptime(arrival_time_str, fmt)
                        departure_dt = datetime.datetime.strptime(departure_time_str, fmt)
                        diff = departure_dt - arrival_dt
                        total_minutes = int(diff.total_seconds() // 60)
                        hours = total_minutes // 60
                        minutes = total_minutes % 60
                        connection_time_str = f"{hours}h {minutes}m"

                    first = flights_list[0]
                    last = flights_list[-1]
                    logo = option.get("airline_logo")

                    total_minutes = option.get("total_duration", 0)
                    hours = total_minutes // 60
                    minutes = total_minutes % 60
                    duration_str = f"{hours}h {minutes}m"

                    filtered.append({
                        "Vuelos": ", ".join(f["flight_number"] for f in flights_list),
                        "Salida": f"{first['departure_airport']['name']} ({first['departure_airport']['id']}) - {first['departure_airport']['time']}",
                        "Llegada": f"{last['arrival_airport']['name']} ({last['arrival_airport']['id']}) - {last['arrival_airport']['time']}",
                        "Duración": duration_str,
                        "Tiempo de conexión": connection_time_str,
                        "Lugares solicitados": passengers,
                        "Logo": logo,
                        "Tramos": "\n".join(legs)
                    })

            if filtered:
                st.success(f"Se encontraron {len(filtered)} opciones completas de la aerolínea {airline_code.upper()}:")
                for vuelo in filtered:
                    if vuelo["Logo"]:
                        st.image(vuelo["Logo"], width=60)
                    st.write(f"**Vuelos:** {vuelo['Vuelos']}")
                    st.write(f"**Salida:** {vuelo['Salida']}")
                    st.write(f"**Llegada:** {vuelo['Llegada']}")
                    st.write(f"**Duración:** {vuelo['Duración']}")
                    if vuelo["Tiempo de conexión"]:
                        st.write(f"**Tiempo de conexión:** {vuelo['Tiempo de conexión']}")
                    st.write(f"**Lugares solicitados:** {vuelo['Lugares solicitados']}")
                    st.write("**Tramos:**")
                    st.markdown(vuelo["Tramos"])
                    st.markdown("---")
                # Mostrar como tabla secundaria sin logo y sin tramos
                st.dataframe([
                    {k: v for k, v in f.items() if k not in ["Logo", "Tramos"]}
                    for f in filtered
                ])
            else:
                st.warning("No se encontraron vuelos disponibles con todos los tramos operados por la aerolínea seleccionada.")
