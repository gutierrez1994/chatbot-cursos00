from flask import Flask, request, jsonify, render_template_string
import requests
from bs4 import BeautifulSoup
import re
from unidecode import unidecode

app = Flask(__name__)

#Array de municipios de Madrid
MUNICIPIOS_MADRID = [
    "acebeda", "ajalvir", "alameda del valle", "el álamo", "alcalá de henares",
    "alcobendas", "alcorcón", "aldea del fresno", "algete", "alpedrete",
    "ambite", "anchuelo", "aranjuez", "arganda del rey", "arroyomolinos",
    "el atazar", "batres", "becerril de la sierra", "belmonte de tajo",
    "el berrueco", "berzosa del lozoya", "el boalo", "boadilla del monte",
    "braojos", "brea de tajo", "brunete", "buitrago del lozoya",
    "bustarviejo", "cabanillas de la sierra", "la cabrera",
    "cadalso de los vidrios", "camarma de esteruelas", "campo real",
    "canencia", "carabaña", "casarrubuelos", "cenicientos", "cercedilla",
    "cervera de buitrago", "chapinería", "chinchón", "ciempozuelos",
    "cobeña", "collado mediano", "collado villalba", "colmenar de oreja",
    "colmenar del arroyo", "colmenar viejo", "colmenarejo", "corpa",
    "coslada", "cubas de la sagra", "daganzo de arriba", "el escorial",
    "estremera", "fresnedillas de la oliva", "fresno de torote",
    "fuenlabrada", "fuente el saz de jarama", "fuentidueña de tajo",
    "galapagar", "garganta de los montes",
    "gargantilla del lozoya y pinilla de buitrago", "gascones",
    "getafe", "griñón", "guadalix de la sierra", "guadarrama",
    "la hiruela", "horcajo de la sierra-aoslos", "horcajuelo de la sierra",
    "hoyo de manzanares", "humanes de madrid", "leganés", "loeches",
    "los molinos", "los santos de la humosa",
    "lozoya", "lozoyuela-navas-sieteiglesias", "madarcos", "madrid",
    "majadahonda", "manzanares el real", "meco", "mejorada del campo",
    "miraflores de la sierra", "el molar", "los molinos", "montejo de la sierra",
    "moraleja de enmedio", "moralzarzal", "morata de tajuña", "móstoles",
    "navacerrada", "navalafuente", "navalagamella", "navalcarnero",
    "navarredonda y san mamés", "navas del rey", "nuevo baztán",
    "olmeda de las fuentes", "orusco de tajuña", "paracuellos de jarama",
    "parla", "patones", "pedrezuela", "pelayos de la presa",
    "perales de tajuña", "pezuela de las torres", "pinilla del valle",
    "piñuécar-gandullas", "pinto", "pozuelo de alarcón",
    "pozuelo del rey", "prádena del rincón", "puebla de la sierra",
    "puentes viejas", "quijorna", "rascafría", "redueña", "ribatejada",
    "rivas-vaciamadrid", "robledillo de la jara", "robledo de chavela",
    "robregordo", "las rozas de madrid", "rozas de puerto real",
    "san agustín del guadalix", "san fernando de henares",
    "san lorenzo de el escorial", "san martín de la vega",
    "san martín de valdeiglesias", "san sebastián de los reyes",
    "santa maría de la alameda", "santorcaz", "santos de la humosa",
    "la serna del monte", "serranillos del valle", "sevilla la nueva",
    "somosierra", "soto del real", "talamanca de jarama", "tielmes",
    "titulcia", "torrejón de ardoz", "torrejón de la calzada",
    "torrejón de velasco", "torrelaguna", "torrelodones",
    "torremocha de jarama", "torres de la alameda", "tres cantos",
    "valdaracete", "valdeavero", "valdelaguna", "valdemanco",
    "valdeolmos-alalpardo", "valdepiélagos", "valdetorres de jarama",
    "valdilecha", "valverde de alcalá", "velilla de san antonio",
    "el vellón", "venturada", "villa del prado", "villaconejos",
    "villalbilla", "villamanrique de tajo", "villamanta",
    "villamantilla", "villanueva de la cañada", "villanueva de perales",
    "villanueva del pardillo", "villar del olmo", "villarejo de salvanés",
    "villaviciosa de odón", "villavieja del lozoya", "zarzalejo"
]

#Array de meses en español
MESES_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
]

#Funcion que recoge la fecha y la formatea a un formato entendible para los filtros
def obtener_mes_desde_fecha(texto_fecha):
    if not texto_fecha or texto_fecha == "N/D":
        return None
    
    # Probar diferentes formatos de fecha
    formatos = [
        r"(\d{1,2})/(\d{1,2})/(\d{4})",  # dd/mm/yyyy
        r"(\d{1,2})-(\d{1,2})-(\d{4})",  # dd-mm-yyyy
        r"(\d{1,2})\.(\d{1,2})\.(\d{4})" # dd.mm.yyyy
    ]
    
    for formato in formatos:
        match = re.search(formato, texto_fecha)
        if match:
            try:
                mes_num = int(match.group(2))
                if 1 <= mes_num <= 12:
                    return MESES_ES[mes_num - 1]
            except (IndexError, ValueError):
                continue
    
    return None

#Funcion para rellenar la informacion del curso en la variable "detalles"
def obtener_detalle_curso(link):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(link, headers=headers, timeout=10)
        r.raise_for_status()
    except Exception:
        return {
            "horas": "N/D",
            "horario": "N/D",
            "fecha_inicio": "N/D",
            "titulacion": "N/D",
            "ubicacion": "N/D"
        }

    soup = BeautifulSoup(r.text, 'html.parser')
    detalles = {
        "horas": "N/D",
        "horario": "N/D",
        "fecha_inicio": "N/D",
        "titulacion": "N/D",
        "ubicacion": "N/D"
    }

    items = soup.select("ul.eael-feature-list-items li")
    for item in items:
        titulo = item.find("h2")
        contenido = item.find("p")
        if not titulo or not contenido:
            continue
        titulo_texto = titulo.get_text(strip=True).lower()
        contenido_texto = contenido.get_text(strip=True)

        if "número de horas" in titulo_texto:
            detalles["horas"] = contenido_texto
        elif "horario" in titulo_texto:
            detalles["horario"] = contenido_texto
        elif "fecha de inicio" in titulo_texto:
            detalles["fecha_inicio"] = contenido_texto
        elif "titulación" in titulo_texto:
            detalles["titulacion"] = contenido_texto
        elif "ubicación" in titulo_texto:
            detalles["ubicacion"] = contenido_texto

    return detalles

#Funcion para obtener la informacion inicial del curso desde las paginas de trabajador/desempleado de cursos00 (se implementa en la siguiente funcion)
def obtener_cursos_desde_url(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        tabla = soup.find('table')
        if not tabla:
            print(f"DEBUG: No se encontró tabla en {url}")
            return None, "No se encontró la tabla de cursos"
        
        filas = tabla.find_all('tr')[1:]
        if not filas:
            print(f"DEBUG: Tabla vacía en {url}")
            return None, "La tabla de cursos está vacía"
            
        cursos = []
        for fila in filas:
            try:
                celdas = fila.find_all('td')
                if len(celdas) < 3:
                    continue
                    
                nombre = celdas[0].get_text(strip=True)
                link = celdas[0].find('a')['href'] if celdas[0].find('a') else ''
                modalidad = celdas[1].get_text(strip=True)
                rama = celdas[2].get_text(strip=True)
                
                detalles = obtener_detalle_curso(link)
                cursos.append({
                    "nombre": nombre,
                    "link": link,
                    "modalidad": modalidad,
                    "rama": rama,
                    **detalles
                })
            except Exception as e:
                print(f"Error procesando fila: {str(e)}")
                continue
                
        return cursos, None
        
    except Exception as e:
        print(f"Error al obtener cursos: {str(e)}")
        return None, f"Error al obtener cursos: {str(e)}"

#Funcion para obtener los cursos de cursos00, junto con la funcion anterior
import time

# Variables globales para cachear los cursos
cursos_cacheados = []
cache_timestamp = 0
CACHE_DURACION = 600  # 10 minutos (600 segundos)

def obtener_cursos():
    global cursos_cacheados, cache_timestamp

    ahora = time.time()
    if cursos_cacheados and (ahora - cache_timestamp < CACHE_DURACION):
        return cursos_cacheados, None  # Retornar los cursos desde cache

    # Si no hay cache o está vencida, volver a obtenerlos
    url_desempleados = "https://cursos00.com/cursos-gratis-para-desempleados/"
    url_trabajadores = "https://cursos00.com/cursos-gratis-para-trabajadores/"

    cursos_desempleados, _ = obtener_cursos_desde_url(url_desempleados)
    cursos_trabajadores, _ = obtener_cursos_desde_url(url_trabajadores)

    cursos = []
    if cursos_desempleados:
        cursos.extend(cursos_desempleados)
    if cursos_trabajadores:
        cursos.extend(cursos_trabajadores)

    cursos_cacheados = cursos
    cache_timestamp = ahora

    return cursos, None


#Formatea los horarios a un formato legible para los filtros
def extraer_horas_completas(horario):
    """Extracción robusta que maneja formatos complejos"""
    if not horario or horario == "N/D":
        return []
    
    # Eliminar días y texto entre paréntesis
    horario_limpio = re.sub(r'\(.*?\)|[A-Za-zÁ-Úá-ú]', '', horario)
    # Extraer todas las horas
    return re.findall(r'\b(\d{1,2}:\d{2})\b', horario_limpio)

#Obtiene los cursos que son por la mañana y formatea la informacion
def es_horario_manana(horario):
    if not horario or horario == "N/D":
        return False
    
    # Extraer todas las horas del horario
    horas = re.findall(r'(\d{1,2}):(\d{2})', horario)
    if not horas:
        return False
    
    # Verificar si alguna hora es antes de las 14:00
    for hora_str, minuto_str in horas:
        try:
            hora = int(hora_str)
            if hora < 14:  # Cualquier hora antes de las 14:00 se considera mañana
                return True
        except:
            continue
    
    return False

#Obtiene los cursos que son por la tarde y formatea la informacion
def es_horario_tarde(horario):
    """Detecta si un horario es de tarde (después de las 14:00)"""
    if not horario or horario == "N/D":
        return False
    
    # Extraer horas
    horas = re.findall(r'(\d{1,2}):(\d{2})', horario)
    
    if not horas:
        return False
    
    # Buscar horas de tarde (14:00 o posterior)
    for hora_str, minuto_str in horas:
        try:
            hora = int(hora_str)
            if hora >= 14:
                return True
        except ValueError:
            continue
    
    return False

#Funcion que aplica filtros al mensaje que nos manda el usuario a traves del chat
def filtrar_cursos_por_mensaje(cursos, mensaje):
    mensaje = unidecode(mensaje.lower())
    palabras = mensaje.split()
    resultados = cursos[:]

    STOPWORDS = {"quiero", "que", "me", "des", "todos", "los", "las", "en", "de", "un", "una", "por", "para", "con", "cursos"}

    for palabra in palabras:
        if palabra in STOPWORDS:
            continue

        previos = resultados[:]

        if palabra in ["online", "distancia", "remoto"]:
            resultados = [c for c in resultados if "online" in c["modalidad"].lower() or "distancia" in c["modalidad"].lower()]
        elif palabra == "presenciales":
            resultados = [c for c in resultados if "presencial" in c["modalidad"].lower()]
        
        

        # Municipio
        elif any(palabra == unidecode(m.lower()) for m in MUNICIPIOS_MADRID):
            resultados = [c for c in resultados if palabra in unidecode(c["ubicacion"].lower())]
        
        # Mes
        elif palabra in MESES_ES:
            resultados = [c for c in resultados if obtener_mes_desde_fecha(c["fecha_inicio"]) == palabra]

        # Horas numéricas
        elif palabra.isdigit():
            min_horas = int(palabra)
            def extraer_horas(txt):
                m = re.search(r"(\d+)", txt)
                return int(m.group(1)) if m else 0
            resultados = [c for c in resultados if extraer_horas(c["horas"]) >= min_horas]

        # Nombre o rama
        else:
            resultados = [c for c in resultados if palabra in unidecode(c["nombre"].lower()) or palabra in unidecode(c["rama"].lower())]

        if not resultados:
            resultados = previos

    return resultados

#Funcion que da el formato predeterminado para mostrar el curso en el chat
def formatear_respuesta(cursos):
    if not cursos:
        return "No hay cursos disponibles en este momento."

    respuesta = ""
    for curso in cursos:
        respuesta += f"<div class='curso'>"
        respuesta += f"<b>📘 {curso['nombre']}</b><br>"
        respuesta += f"📝 Modalidad: {curso['modalidad']}<br>"
        respuesta += f"🗂 Rama: {curso['rama']}<br>"
        respuesta += f"⏱ Horas: {curso['horas']}<br>"
        respuesta += f"🕒 Horario: {curso['horario']}<br>"
        respuesta += f"📅 Inicio: {curso['fecha_inicio']}<br>"
        respuesta += f"🎓 Titulación: {curso['titulacion']}<br>"
        respuesta += f"📍 Ubicación: {curso['ubicacion']}<br>"
        respuesta += f"🔗 <a class='link_curso' href='{curso['link']}' target='_blank'>Más info</a><br>"
        respuesta += "</div><hr>"
    return respuesta

FAQ = {
    "hola": "¡Hola! 👋 Soy tu asistente de cursos gratuitos. Puedes pedirme que te muestre cursos, por ejemplo: 'Mostrar cursos online' o 'Cursos presenciales en Madrid'.",
    "buenos días": "¡Buenos días! ☀️ ¿Quieres que te muestre los cursos disponibles?",
    "buenas tardes": "¡Buenas tardes! 🌤️ ¿Quieres que te muestre los cursos disponibles?",
    "buenas noches": "¡Buenas noches! 🌙 ¿Quieres que te muestre los cursos disponibles?",
    "gracias": "¡De nada! 😊 Si tienes más preguntas, aquí estoy para ayudarte.",
    "adiós": "¡Hasta luego! 👋 Que tengas un buen día."
}

#Aqui se lanza el html al servidor para poder verlo desde localhost o desde 127.0.0.0
@app.route("/")
def index():
    html = """
<style>
  #chatbox {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: #fff;
    border-radius: 10px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    width: 360px;
    max-width: 95vw;
    display: flex;
    flex-direction: column;
    height: 600px;
    overflow: hidden;
    
    position: fixed;
    bottom: 50px;  /* Deja espacio para el botón */
    right: 20px;
    opacity: 0;
    pointer-events: none;
    transform: translateY(20px);
    transition: opacity 0.3s ease, transform 0.3s ease;
    z-index: 9999;
  }
  #chatbox.open {
    opacity: 1;
    pointer-events: auto;
    transform: translateY(0);
  }
  #chat-header {
    background: #1a73e8;
    color: white;
    padding: 12px 16px;
    font-weight: 600;
    font-size: 1.1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
  }
  #chat-close {
    background: transparent;
    border: none;
    color: white;
    font-size: 20px;
    cursor: pointer;
    line-height: 1;
    padding: 0;
  }
  #messages {
    flex-grow: 1;
    padding: 15px;
    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: #888 transparent;
  }
  #messages::-webkit-scrollbar {
    width: 6px;
  }
  #messages::-webkit-scrollbar-thumb {
    background-color: #888;
    border-radius: 3px;
  }
  .message {
    max-width: 80%;
    margin-bottom: 12px;
    padding: 10px 15px;
    border-radius: 20px;
    line-height: 1.3;
    font-size: 0.95rem;
    word-wrap: break-word;
  }
  .bot {
    background: #1a73e8; /* azul vibrante */
    color: white;
    align-self: flex-start;
    border-bottom-left-radius: 0;
    box-shadow: 0 2px 6px rgba(26, 115, 232, 0.5);
    font-weight: 500;
  }
  /* Corrección para que los cursos dentro del mensaje bot mantengan fondo blanco */
  .bot .curso {
    background: #fff;
    color: #000;
    padding: 10px 15px;
    border-radius: 10px;
    margin-top: 8px;
    display: block;
  }
  .bot .curso a {
    color: #1A73E8 !important;
    text-decoration: underline;
  }
  .user {
    background: #e2e8f0;
    color: #333;
    align-self: flex-end;
    border-bottom-right-radius: 0;
    font-weight: 500;
  }
  /* Ajustar enlaces dentro de mensajes del bot para que sean visibles */
  .bot a {
    color: #bbdefb;
    text-decoration: underline;
  }
  #input-area {
    display: flex;
    padding: 10px 15px;
    border-top: 1px solid #ddd;
    background: #fafafa;
  }
  #input {
    flex-grow: 1;
    border: none;
    border-radius: 20px;
    padding: 10px 15px;
    font-size: 1rem;
    outline: none;
    box-shadow: inset 0 0 5px #ddd;
    transition: box-shadow 0.3s ease;
  }
  #input:focus {
    box-shadow: inset 0 0 8px #007bff;
  }
  #send {
    margin-left: 10px;
    background: #007bff;
    border: none;
    color: white;
    border-radius: 20px;
    padding: 10px 18px;
    cursor: pointer;
    font-weight: 600;
    transition: background-color 0.3s ease;
  }
  #send:hover {
    background: #0056b3;
  }
  #buttons {
    padding: 8px 15px;
    background: #f0f2f5;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    border-top: 1px solid #ddd;
  }
  .btn-suggestion {
    background: #e7f1ff;
    color: #007bff;
    border: 1px solid #007bff;
    border-radius: 20px;
    padding: 6px 14px;
    font-size: 0.9rem;
    cursor: pointer;
    user-select: none;
    transition: background-color 0.3s ease, color 0.3s ease;
  }
  .btn-suggestion:hover {
    background: #007bff;
    color: white;
  }
  .curso {
    background: #f9fafb;
    padding: 10px 15px;
    border-radius: 10px;
    color: black;
  }
  a {
    color: #cce5ff;
    text-decoration: underline;
  }
  .link_curso{
    color: #1A73E8 !important;
  }

  /* Botón flotante del chat */
  #chat-toggle {
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: #1a73e8;
    border-radius: 50%;
    width: 56px;
    height: 56px;
    border: none;
    color: white;
    font-size: 28px;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(26,115,232,0.6);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10000;
    transition: background-color 0.3s ease;
  }
  #chat-toggle:hover {
    background: #155ab6;
  }
  
  /* Animación de carga */
  .loader {
    display: inline-block;
    width: 20px;
    height: 20px;
    border: 3px solid rgba(255,255,255,.3);
    border-radius: 50%;
    border-top-color: #fff;
    animation: spin 1s ease-in-out infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .loading-message {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .loading-text {
    font-style: italic;
  }
</style>

<!-- Botón para abrir chat -->
<button id="chat-toggle" aria-label="Abrir chat">🗨️</button>

<div id="chatbox" role="region" aria-live="polite" aria-label="Chat de cursos gratuitos">
  <div id="chat-header">
    <span>Asistente Virtual</span>
    <button id="chat-close" aria-label="Cerrar chat">✖</button>
  </div>
  <div id="messages"></div>
  <div id="buttons"></div>
  <div id="input-area">
    <input id="input" type="text" autocomplete="off" placeholder="Escribe aquí tu mensaje..." aria-label="Entrada de mensaje" />
    <button id="send" aria-label="Enviar mensaje">Enviar</button>
  </div>
</div>

<script>
  const messages = document.getElementById('messages');
  const input = document.getElementById('input');
  const send = document.getElementById('send');
  const buttonsDiv = document.getElementById('buttons');
  const chatbox = document.getElementById('chatbox');
  const chatToggle = document.getElementById('chat-toggle');
  const chatClose = document.getElementById('chat-close');

  // Función para mostrar animación de carga
  function showLoading() {
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message bot loading-message';
    loadingDiv.innerHTML = `
      <div class="loader"></div>
      <span class="loading-text">Escribiendo...</span>
    `;
    messages.appendChild(loadingDiv);
    messages.scrollTop = messages.scrollHeight;
    return loadingDiv;
  }

  // Abrir chat
  function openChat() {
    chatbox.classList.add('open');
    chatToggle.style.display = 'none';
    input.focus();

    // Mostrar mensaje bienvenida sólo una vez
    if (!openChat.bienvenidaMostrada) {
      const bienvenida = "¡Hola! 👋 Soy tu asistente para encontrar cursos gratuitos. Puedes escribir cosas como 'Cursos online', 'Presencial en Madrid', o hacer preguntas.";
      addMessage(bienvenida, "bot");
      setSuggestions(["Mostrar todos los cursos", "Cursos online", "Cursos presenciales"]);
      openChat.bienvenidaMostrada = true;
    }
  }
  openChat.bienvenidaMostrada = false;

  // Cerrar chat
  function closeChat() {
    chatbox.classList.remove('open');
    chatToggle.style.display = 'flex';
  }

  chatToggle.addEventListener('click', openChat);
  chatClose.addEventListener('click', closeChat);

  // Función para añadir mensaje al chat
  function addMessage(text, className) {
    const p = document.createElement('div');
    p.className = 'message ' + className;
    p.innerHTML = text;
    messages.appendChild(p);
    messages.scrollTop = messages.scrollHeight;
  }

  // Añadir botones sugeridos dinámicos
  function setSuggestions(suggestions) {
    buttonsDiv.innerHTML = '';
    if (!suggestions || suggestions.length === 0) return;
    suggestions.forEach(text => {
      const btn = document.createElement('button');
      btn.className = 'btn-suggestion';
      btn.textContent = text;
      btn.onclick = () => {
        input.value = text;
        sendMessage();
      };
      buttonsDiv.appendChild(btn);
    });
  }

  // Enviar mensaje y procesar respuesta
  function sendMessage() {
    const text = input.value.trim();
    if (!text) return;
    
    addMessage("Tú: " + text, "user");
    input.value = "";
    buttonsDiv.innerHTML = ''; // limpiar sugerencias mientras responde
    
    // Mostrar animación de carga
    const loadingElement = showLoading();
    
    fetch('/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({mensaje: text})
    }).then(res => res.json())
      .then(data => {
        // Eliminar el mensaje de carga
        messages.removeChild(loadingElement);
        addMessage(data.respuesta_html, "bot");
        setSuggestions(data.sugerencias);
      })
      .catch(() => {
        // Eliminar el mensaje de carga en caso de error
        messages.removeChild(loadingElement);
        addMessage("Error en la comunicación con el servidor.", "bot");
      });
  }

  send.onclick = sendMessage;

  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendMessage();
  });
</script>

"""
    return render_template_string(html)

#Aqui se manda el mensaje por post al chat, se aplican los filtros y devuelve la respuesta adecuada
@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        mensaje_original = data.get("mensaje", "").strip()
        
        if not mensaje_original:
            return jsonify({
                "respuesta_html": "Por favor ingresa un mensaje válido",
                "sugerencias": ["Mostrar todos los cursos"]
            })
        
        # Manejar FAQs
        if respuesta_faq := manejar_faq(mensaje_original):
            return respuesta_faq
        
        # Obtener cursos
        cursos, error = obtener_cursos()
        if error:
            return jsonify({
                "respuesta_html": f"No se pudieron obtener cursos.<br>{error}",
                "sugerencias": ["Intentar nuevamente", "Mostrar todos los cursos"]
            })
        
        # Aplicar filtros
        filtrados = filtrar_cursos_por_mensaje(cursos, mensaje_original)
        filtrados = aplicar_filtros_adicionales(filtrados, mensaje_original)
        
        # Preparar respuesta
        return preparar_respuesta(filtrados, mensaje_original)
        
    except Exception as e:
        print(f"Error en el servidor: {str(e)}")
        return jsonify({
            "respuesta_html": "Ocurrió un error al procesar tu solicitud",
            "sugerencias": ["Intentar nuevamente", "Contactar soporte"]
        }), 500

#Funcion que maneja las preguntas frecuentes dentro del chat
def manejar_faq(mensaje):
    for pregunta, respuesta in FAQ.items():
        if pregunta in mensaje:
            return jsonify({
                "respuesta_html": respuesta,
                "sugerencias": ["Mostrar todos los cursos", "Cursos online", "Cursos presenciales"]
            })
    return None

#Funcion que aplica filtros extra de busqueda para afinar los resultados mostrados
def aplicar_filtros_adicionales(cursos, mensaje):
    print(f"\n{'='*50}")
    print(f"Iniciando filtros adicionales para: '{mensaje}'")
    
    mensaje_lower = unidecode(mensaje.lower())
    palabras = mensaje_lower.split()
    print(f"Palabras del mensaje: {palabras}")
    print(f"Cursos recibidos: {len(cursos)}")

    # 1. Filtro por municipio
    cursos = filtrar_por_municipio(cursos, mensaje_lower)
    print(f"Después de municipio: {len(cursos)} cursos")

    # 2. Filtro por horario
    cursos_filtrados = []
    for curso in cursos:
        horario = curso.get("horario", "")
        horas = extraer_horas_completas(horario)
        es_m = es_horario_manana(horario)
        es_t = es_horario_tarde(horario)

        print(f"\nCurso: {curso['nombre']}")
        print(f"Horario: {horario}")
        print(f"Horas extraídas: {horas}")
        print(f"¿Mañana? {es_m}")
        print(f"¿Tarde? {es_t}")

        if "manana" in palabras:
            if es_m:
                cursos_filtrados.append(curso)
                print("→ INCLUIDO (mañana)")
            else:
                print("→ DESCARTADO (no es mañana)")
        elif "tarde" in palabras:
            if es_t:
                cursos_filtrados.append(curso)
                print("→ INCLUIDO (tarde)")
            else:
                print("→ DESCARTADO (no es tarde)")
        else:
            cursos_filtrados.append(curso)
            print("→ INCLUIDO (sin filtro horario)")

    print(f"\nTotal después de horario: {len(cursos_filtrados)} cursos")

    # Resto de filtros
    cursos_filtrados = filtrar_por_horas(cursos_filtrados, mensaje_lower)
    cursos_filtrados = filtrar_por_mes(cursos_filtrados, mensaje_lower)
    cursos_filtrados = filtrar_por_palabras_clave(cursos_filtrados, mensaje_lower)

    print(f"\nTotal final: {len(cursos_filtrados)} cursos")
    print("="*50)
    return cursos_filtrados

#Aqui se aplica un filtro por horas para poder filtrar por mas o menos de X horas
def filtrar_por_horas(cursos, mensaje):
    def extraer_horas(horas_texto):
        m = re.search(r"(\d+)", horas_texto)
        return int(m.group(1)) if m else 0
    
    match_mas = re.search(r"(mas de|minimo|al menos)\s*(\d{2,3})\s*horas?", mensaje)
    match_menos = re.search(r"(menos de|maximo|hasta)\s*(\d{2,3})\s*horas?", mensaje)
    match_exacto = re.search(r"(\d{2,3})\s*horas?", mensaje)

    if match_mas:
        horas = int(match_mas.group(2))
        return [c for c in cursos if extraer_horas(c["horas"]) > horas]
    elif match_menos:
        horas = int(match_menos.group(2))
        return [c for c in cursos if extraer_horas(c["horas"]) < horas]
    elif match_exacto:
        horas = int(match_exacto.group(1))
        return [c for c in cursos if extraer_horas(c["horas"]) >= horas]
    
    return cursos

#Aqui se aplica un filtro extra para diferenciar entre meses 
def filtrar_por_mes(cursos, mensaje):
    print(f"\nDEBUG: Filtrando por mes - Mensaje: '{mensaje}'")
    mensaje_normalizado = unidecode(mensaje.lower())
    
    for i, mes in enumerate(MESES_ES):
        mes_normalizado = unidecode(mes.lower())
        if mes_normalizado in mensaje_normalizado:
            print(f"Buscando cursos en {mes}...")
            cursos_filtrados = []
            
            for curso in cursos:
                fecha = curso.get("fecha_inicio", "N/D")
                mes_curso = obtener_mes_desde_fecha(fecha)
                print(f"Curso: {curso['nombre']} - Fecha: {fecha} - Mes extraído: {mes_curso}")
                
                if mes_curso and unidecode(mes_curso.lower()) == mes_normalizado:
                    cursos_filtrados.append(curso)
                    print("→ INCLUIDO (coincide mes)")
                else:
                    print("→ DESCARTADO (no coincide mes)")
            
            return cursos_filtrados
    
    print("No se encontró referencia a mes en el mensaje")
    return cursos

#Aqui se aplica un filtro extra para diferenciar entre municipios
def filtrar_por_municipio(cursos, mensaje):
    municipio_buscado = None

    for muni in MUNICIPIOS_MADRID:
        muni_normalizado = unidecode(muni.lower())
        if muni_normalizado in mensaje:
            municipio_buscado = muni_normalizado
            break

    if not municipio_buscado:
        return cursos

    print(f"\nDEBUG: Filtrando por municipio '{municipio_buscado}'")
    resultados = []

    for curso in cursos:
        ubicacion = unidecode(curso.get("ubicacion", "").lower())
        print(f"Curso: {curso['nombre']} - Ubicación: {ubicacion}")
        if municipio_buscado in ubicacion:
            resultados.append(curso)
            print("→ INCLUIDO (coincide municipio)")
        else:
            print("→ DESCARTADO (no coincide municipio)")

    return resultados


#Esta funcion normaliza los textos para dejarlos en minuscula, sin tildes y sin caracteres raros
def normalizar_texto(texto):
    """Normaliza texto para comparaciones: quita tildes, espacios y convierte a minúsculas"""
    if not texto:
        return ""
    texto = unidecode(texto.lower().strip())
    texto = re.sub(r'[^a-z0-9]', '', texto)  # Elimina todo excepto letras y números
    return texto

def filtrar_por_horario(cursos, mensaje):
    mensaje_normalizado = normalizar_texto(mensaje)
    resultados = []
    
    for curso in cursos:
        horario = curso.get("horario", "")
        es_m = es_horario_manana(horario)
        es_t = es_horario_tarde(horario)
        
        if "mañana" in mensaje_normalizado:
            if es_m:
                resultados.append(curso)
        elif "tarde" in mensaje_normalizado:
            if es_t:
                resultados.append(curso)
        else:
            resultados.append(curso)
    
    return resultados

#Funcion que aplica un filtro de palabras clave para afinar la busqueda
def filtrar_por_palabras_clave(cursos, mensaje):
    def contiene_palabra_clave(texto, mensaje):
        palabras = mensaje.split()
        return any(p in texto.lower() for p in palabras)
    
    if any(contiene_palabra_clave(c["nombre"], mensaje) for c in cursos):
        return [c for c in cursos if contiene_palabra_clave(c["nombre"], mensaje)]
    elif any(contiene_palabra_clave(c["rama"], mensaje) for c in cursos):
        return [c for c in cursos if contiene_palabra_clave(c["rama"], mensaje)]
    return cursos

#Aqui se dan opciones de respuestas automaticas para diferentes opciones
def preparar_respuesta(cursos, mensaje_original):
    mensaje = normalizar_texto(mensaje_original)
    
    if not cursos:
        if "mañana" in mensaje:
            return jsonify({
                "respuesta_html": "No se encontraron cursos matutinos. ¿Deseas ver cursos de otro horario?",
                "sugerencias": ["Cursos por la tarde en Madrid", "Cursos online", "Mostrar todos los cursos"]
            })
        else:
            return jsonify({
                "respuesta_html": "No se encontraron cursos que coincidan con tu búsqueda.",
                "sugerencias": ["Mostrar todos los cursos", "Cursos online",]
            })
    
    respuesta = formatear_respuesta(cursos)
    respuesta += f"<p><b>{len(cursos)} cursos encontrados.</b></p>"
    
    sugerencias = ["Mostrar todos los cursos", "Cursos online", "Cursos presenciales"]
    if "mañana" in mensaje:
        sugerencias.append("Cursos por la tarde")
    elif "tarde" in mensaje:
        sugerencias.append("Cursos por la mañana")
    
    return jsonify({"respuesta_html": respuesta, "sugerencias": sugerencias})

if __name__ == "__main__":
    app.run(debug=True)