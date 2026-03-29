ultimo_estado = False
from playwright.sync_api import sync_playwright
import time
import requests

URL = "https://nunoa.ingelan.cl/"
MESES_A_REVISAR = 4  # mes actual + 3 siguientes

# ====== PEGA AQUÍ TUS DATOS DE TELEGRAM ======
TOKEN = "8274340316:AAHP7-5jWZWHPwMB6klySiJ9g6PKt0kSQwk"
CHAT_ID = 1677543714
# ============================================


def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": mensaje
    }

    try:
        respuesta = requests.post(url, data=data, timeout=15)
        if respuesta.status_code == 200:
            print("Mensaje enviado a Telegram")
        else:
            print(f"Error Telegram: {respuesta.status_code} - {respuesta.text}")
    except Exception as e:
        print(f"Error enviando mensaje a Telegram: {e}")


def obtener_titulo_mes(page):
    try:
        mes = page.locator(".ui-datepicker-month").inner_text().strip()
        anio = page.locator(".ui-datepicker-year").inner_text().strip()
        return f"{mes} {anio}"
    except Exception:
        return "Mes desconocido"


def revisar_disponibilidad_mes_actual(page):
    page.wait_for_selector("#ui-datepicker-div", timeout=10000)

    titulo_mes = obtener_titulo_mes(page)
    print(f"\nRevisando mes: {titulo_mes}")

    dias_habilitados = page.locator("#ui-datepicker-div td[data-handler='selectDay'] a")
    cantidad = dias_habilitados.count()

    print(f"Días habilitados encontrados en {titulo_mes}: {cantidad}")

    dias = []
    for i in range(cantidad):
        texto = dias_habilitados.nth(i).inner_text().strip()
        if texto:
            dias.append(texto)

    if cantidad > 0:
        print(f"HAY días disponibles en {titulo_mes}: {', '.join(dias)}")
        return {
            "hay_cupo": True,
            "mes": titulo_mes,
            "dias": dias
        }
    else:
        print(f"NO hay días disponibles en {titulo_mes}")
        return {
            "hay_cupo": False,
            "mes": titulo_mes,
            "dias": []
        }


def avanzar_mes(page, numero_mes):
    try:
        boton = page.get_by_title("Sig >")
        boton.wait_for(timeout=5000)
        boton.click()
        page.wait_for_timeout(1500)
        print(f"Avancé al siguiente mes ({numero_mes})")
        return True
    except Exception as e:
        print(f"No se pudo avanzar al mes siguiente ({numero_mes}): {e}")
        return False


def revisar_todos_los_meses(page, cantidad_meses):
    resultados = []

    for i in range(cantidad_meses):
        resultado = revisar_disponibilidad_mes_actual(page)
        resultados.append(resultado)

        if i < cantidad_meses - 1:
            pudo_avanzar = avanzar_mes(page, i + 1)
            if not pudo_avanzar:
                print("No se pudo seguir avanzando en el calendario.")
                break

    return resultados


def revisar_una_vez():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--window-size=1366,768"]
        )

        page = browser.new_page(
            viewport={"width": 1366, "height": 768}
        )

        page.goto(URL, wait_until="domcontentloaded", timeout=30000)
        print("Página cargada")

        page.wait_for_selector("#txt_sucursalC", timeout=20000)
        page.locator("#txt_sucursalC").select_option("3")
        print("Sucursal OK")

        page.wait_for_selector("#txt_centroAtencion", timeout=20000)
        page.locator("#txt_centroAtencion").select_option("3")
        print("Centro de atención OK")

        page.wait_for_selector("#txt_servicios", timeout=20000)
        page.locator("#txt_servicios").select_option("1")
        print("Servicio OK")

        page.wait_for_timeout(1500)

        page.get_by_title("Siguiente").click()
        print("Botón Siguiente OK")

        page.wait_for_timeout(2500)

        page.wait_for_selector('input[placeholder="Seleccione una Fecha"]', timeout=20000)
        page.locator('input[placeholder="Seleccione una Fecha"]').click()
        print("Calendario abierto")

        page.wait_for_selector("#ui-datepicker-div", timeout=10000)
        page.wait_for_timeout(1500)

        resultados = revisar_todos_los_meses(page, MESES_A_REVISAR)

        hay_cupo = any(r["hay_cupo"] for r in resultados)

        print("\n===== RESUMEN =====")
        for r in resultados:
            if r["hay_cupo"]:
                print(f"{r['mes']}: DISPONIBLE -> {', '.join(r['dias'])}")
            else:
                print(f"{r['mes']}: sin cupos")

        browser.close()
        return hay_cupo, resultados


def main():
    enviar_telegram("Prueba de bot Ñuñoa funcionando")
    ultimo_estado = False
    while True:
        print("\n==============================")
        print("Nueva revisión iniciada")
        print("==============================")

        try:
            hay_cupo, resultados = revisar_una_vez()

            if hay_cupo and not ultimo_estado:
                mensaje = "🚨 CUPOS DISPONIBLES EN ÑUÑOA 🚨\n\n"

                for r in resultados:
                    if r["hay_cupo"]:
                        mensaje += f"{r['mes']}: {', '.join(r['dias'])}\n"

                enviar_telegram(mensaje)
                print("\nALERTA ENVIADA A TELEGRAM")
            elif not hay_cupo and ultimo_estado:
                print("Los cupos desaparecieron")
            ultimo_estado = hay_cupo
            
        except Exception as e:
            print(f"\nOcurrió un error: {e}")
            print("Se volverá a intentar en 60 segundos...")
            time.sleep(60)


if __name__ == "__main__":
    main()