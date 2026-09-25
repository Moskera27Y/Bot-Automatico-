"""Guiones: IA (Groq/OpenAI-compatible, gratis) con fallback a plantillas."""
import json
import os
import random

HOOKS = [
    "Para. {tema} te va a volar la cabeza en 30 segundos.",
    "Nadie te conto esto sobre {tema}.",
    "Esto es lo que todos estan buscando hoy: {tema}.",
    "Si ves esto, es por algo: {tema}.",
    "El 99% se equivoca en {tema}.",
]

CTAS = [
    "Guarda este video para cuando lo necesites y mandaselo a quien le sirva.",
    "Comenta PARTE 2 si quieres la continuacion.",
    "Si te sorprendio, compartelo con alguien ahora mismo.",
    "Guardalo o lo vas a olvidar.",
]

SYSTEM_ES = (
    "Eres guionista de YouTube Shorts en espanol neutro (Latam). "
    "Formula: HOOK en la primera frase (maximo 1.5 segundos al leer, idealmente pregunta "
    "o 'para/stop': ej 'Para. Sabias que...?' o 'Deja de...'). Desarrollo en 3 puntos "
    "con logica (primero/segundo/tercero), un resultado o dato final memorable, y cierre "
    "con pregunta para comentarios QUE CONECTE CON LA PRIMERA FRASE (loop: el final debe "
    "fluir hacia el inicio si el video se repite). 100 a 130 palabras. Frases cortas de maximo 15 palabras, "
    "tono conversacional, usa puntos, comas y puntos suspensivos para marcar pausas de voz. "
    "Sin emojis en el guion. Cierra invitando a GUARDAR o COMPARTIR (nunca a seguir/suscribirse). "
    "PROHIBIDO inventar cifras, fechas o "
    "nombres propios falsos: si no conoces el dato exacto, habla en general. "
    "TITULO estilo hook ('Asi es como...', 'Nadie te conto...', 'Para. ...') + 1 emoji + #shorts, max 90 caracteres. "
    "Si el tema gira en torno a UNA persona publica concreta, incluyela en campo persona con su nombre exacto. "
    "Incluye campo fondos: array de 3 consultas EN INGLES (2-4 palabras cada una) para buscar "
    "videoclips stock que ilustren el INICIO, el DESARROLLO y el FINAL (ej: [\"mexico city aerial\", \"money counting hands\", \"stock market chart\"]). "
    "Respondes SOLO JSON valido: {\"titulo\": ..., \"guion\": ..., \"descripcion\": ..., \"tags\": [...], \"persona\": ..., \"fondos\": [...]}}. "
    "Descripcion 2 lineas + hashtags. Tags: 6 max."
)

SYSTEM_EN = (
    "You are a YouTube Shorts scriptwriter. Same formula but the VIDEO IS NARRATED IN ENGLISH "
    "with SPANISH subtitles: hook in the first sentence (max 1.5s read, question or stop-style), "
    "3-point development, memorable payoff, closing question that LOOPS back to the first sentence. "
    "70-90 words (short video), short sentences (max 15 words), conversational, punctuation marks pauses. "
    "No emojis in script. Close inviting to SAVE or SHARE (never follow/subscribe). "
    "NEVER invent figures, dates or names. "
    "TITLE in hook style + 1 emoji + #shorts, max 90 chars. "
    "Descripcion SEO: 2 keyword-rich sentences (what/when/where) + save/share CTA + 5-10 niche hashtags. "
    "Also provide guion_es: the SAME script translated to neutral Latin American Spanish, "
    "split into sentences separated by | in the SAME order and count as the English sentences. "
    "Also provide fondos: array of 3 queries IN ENGLISH (2-4 words each) for stock footage "
    "covering the START, MIDDLE and END. "
    "If the topic is about ONE specific public figure, add field persona with their exact name. "
    "Reply ONLY valid JSON: {\"titulo\": ..., \"guion\": ..., \"guion_es\": ..., \"descripcion\": ..., \"tags\": [...], \"persona\": ..., \"fondos\": [...]}}. "
    "Descripcion: 1 line English + 1 line Spanish + hashtags. Tags: 6 max, in English."
)


def _plantilla(tema, nicho, serie=""):
    tema = tema.strip().replace('"', "")[:120]
    hook = random.choice(HOOKS).format(tema=tema)
    if nicho == "noticias":
        cuerpo = (
            f"{hook} Te lo resumo en menos de un minuto, con lo mas importante primero. "
            f"Esto es lo que esta pasando con {tema}, punto por punto. "
            f"Primero el hecho: que ocurrio y cuando. "
            f"Segundo el contexto: por que esta pasando ahora. "
            f"Tercero la consecuencia: como te afecta a ti directamente. "
            f"Y al final te digo que esperar en los proximos dias. "
            f"Comenta tu opinion, quiero leerte."
        )
        titulo = f"ULTIMA HORA: {tema} #shorts #noticias"
    elif nicho == "gaming":
        cuerpo = (
            f"{hook} Esto tiene que ver con {tema}, y el final no te lo esperas. "
            f"Primero parece facil, pero mira el giro que viene. "
            f"Los profesionales hacen esto diferente, y por eso ganan las partidas. "
            f"El truco esta en tres cosas: posicion, timing y calma. "
            f"Practica esto diez minutos al dia y vas a notar la diferencia hoy mismo. "
            f"Reta en comentarios a un amigo a hacerlo mejor que tu."
        )
        titulo = f"{tema} #shorts #gaming"
    elif nicho == "anime":
        cuerpo = (
            f"{hook} Hoy te hablo de {tema}, sin spoilers. "
            f"De que trata: una historia que te atrapa desde el primer capitulo. "
            f"Lo que mas destaca es su animacion y sus personajes, que se sienten reales. "
            f"Mi veredicto: si te gustan las historias intensas, este es para ti. "
            f"Ya lo viste? Dime en comentarios que te parecio, sin spoilers."
        )
        titulo = f"{tema} #shorts #anime"
    elif nicho == "futbol":
        cuerpo = (
            f"{hook} Resumen rapido de {tema}. "
            f"Asi quedo el marcador y estos fueron los goles del partido. "
            f"El momento clave llego cuando todo parecia definido. "
            f"Con este resultado, asi queda el panorama para los dos equipos. "
            f"Quien fue la figura? Te leo en comentarios."
        )
        titulo = f"{tema} #shorts #futbol"
    elif nicho == "economia":
        cuerpo = (
            f"{hook} Te explico {tema} en menos de un minuto. "
            f"Primero: que esta pasando, en palabras simples. "
            f"Segundo: por que esta pasando ahora. "
            f"Tercero: como afecta directamente a tu bolsillo. "
            f"Y al final, que esperar en los proximos dias. "
            f"Comenta si a ti ya te esta afectando."
        )
        titulo = f"{tema} #shorts #economia"
    elif nicho == "finanzas":
        cuerpo = (
            f"{hook} Hablemos de {tema}, porque te cuesta dinero. "
            f"El error: casi todos hacen esto sin darse cuenta. "
            f"Por que pasa: asi esta disenado el sistema, y te explico como. "
            f"La solucion en una frase, apuntatela. "
            f"Si aplicas esto desde hoy, tu bolsillo lo nota este mes. "
            f"Comenta DINERO si quieres la segunda parte."
        )
        titulo = f"{tema} #shorts #finanzas"
    elif nicho == "historia":
        cuerpo = (
            f"{hook} Esta es la historia de {tema}. "
            f"Todo empezo un dia normal, hasta que paso lo impensable. "
            f"El giro que nadie esperaba cambio el rumbo de todo. "
            f"Y la consecuencia llega hasta nuestros dias. "
            f"La historia siempre cobra: comenta que hubieras hecho tu."
        )
        titulo = f"{tema} #shorts #historia"
    elif nicho == "ia_tech":
        cuerpo = (
            f"{hook} Esto acaba de pasar con {tema}. "
            f"Que es: te lo explico en una frase, sin tecnicismos. "
            f"Para que sirve en tu vida real, con ejemplo concreto. "
            f"Y por que esto cambia las reglas del juego desde hoy. "
            f"Comenta IA si quieres el tutorial completo."
        )
        titulo = f"{tema} #shorts #ia"
    else:
        cuerpo = (
            f"{hook} Primero: lo que creias sobre {tema} esta incompleto, y te explico por que. "
            f"Segundo: el detalle que cambia todo es este, presta atencion. "
            f"Sobre {tema}, lo que descubrieron esta semana lo confirma con pruebas. "
            f"Tercero: la mayoria ignora este punto y por eso se equivoca. "
            f"Y el dato final es el mas sorprendente de todos, quedate a escucharlo. "
            f"Ahora dime en comentarios cual de los tres te sorprendio mas."
        )
        titulo = f"{tema} #shorts"
    cta = random.choice(CTAS)
    guion = f"{cuerpo} {cta}"
    palabras = guion.split()
    if len(palabras) > 135:
        guion = " ".join(palabras[:135])
    if serie:
        titulo = f"{serie}: {titulo}"
    return {
        "titulo": titulo[:95],
        "guion": guion,
        "descripcion": (f"{tema}: resumen rapido y claro. {cta}\n\n"
                        f"Video diario de {nicho}: datos, noticias y tendencias explicadas en 30 segundos.\n"
                        f"#shorts #viral #{nicho} #parati #fyp #kalador"),
        "tags": ["shorts", "viral", "tendencia", "parati", "fyp", "kalador", nicho],
    }


NICHO_EXTRA = {
    "anime": "Es una RESENA de anime sin spoilers mayores: de que trata en 1 frase, que destaca (animacion, historia, personajes), veredicto y a quien se lo recomiendas.",
    "futbol": "Es un RESUMEN de partido: narra el resultado, los goles en orden y el momento clave. Cierra con que sigue para cada equipo.",
    "noticias": "Es un resumen informativo: hecho, contexto y consecuencia.",
    "gaming": "Tono gamer energetico, truco o momento epico.",
    "curiosidades": "Tono de dato sorprendente, 3 puntos.",
    "economia": "Es una noticia ECONOMICA: que paso, por que importa y como afecta al bolsillo. Sin cifras inventadas.",
    "finanzas": "Son FINANZAS PERSONALES: un error comun, por que pasa, y la solucion concreta en 1 frase. Tono directo, sin humo.",
    "historia": "Es HISTORIA narrativa estilo documental: el momento, el giro inesperado y la consecuencia. Tono epico pero sobrio.",
    "ia_tech": "Es noticia TECH/IA: que hace la herramienta o anuncio, para que sirve en la vida real y por que importa ahora.",
}


def _via_ia(tema, nicho, hechos="", lang="es", serie=""):
    from openai import OpenAI

    key = os.getenv("LLM_API_KEY", "")
    if not key:
        raise RuntimeError("sin LLM_API_KEY")
    client = OpenAI(api_key=key, base_url=os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1"))
    extra = NICHO_EXTRA.get(nicho, "")
    datos = f"\nDATOS VERIFICADOS (usalos tal cual, no inventes otros): {hechos}" if hechos else ""
    ser = f"\nEs episodio de la serie '{serie}': mencionala en el hook y titula '{serie}: ...'." if serie else ""
    resp = client.chat.completions.create(
        model=os.getenv("LLM_MODEL", "qwen/qwen3.8-27b"),
        messages=[
            {"role": "system", "content": SYSTEM_EN if lang == "en" else SYSTEM_ES},
            {"role": "user", "content": f"Nicho: {nicho}. {extra} Tema en tendencia: {tema}.{datos}{ser} Escribe el guion."},
        ],
        temperature=0.9,
        max_tokens=600,
    )
    txt = resp.choices[0].message.content.strip()
    if txt.startswith("```"):
        txt = txt.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    if not txt.startswith("{"):
        # Extraer el primer objeto JSON (algunos modelos agregan texto)
        import re
        m = re.search(r"\{.*\}", txt, re.DOTALL)
        if not m:
            raise ValueError("IA no devolvio JSON")
        txt = m.group(0)
    data = json.loads(txt)
    if not data.get("guion") or len(data["guion"].split()) < 40:
        raise ValueError("guion IA demasiado corto")
    data["titulo"] = data.get("titulo", f"{tema} #shorts")[:95]
    data["persona"] = (data.get("persona") or "").strip()[:60]
    fondos = [f.strip() for f in (data.get("fondos") or []) if isinstance(f, str) and f.strip()]
    data["fondos"] = fondos[:4]
    tags = data.get("tags", [])
    if "kalador" not in tags:
        tags.append("kalador")
    data["tags"] = tags[:7]
    return data


def generar_guion(tema, nicho="curiosidades", hechos="", lang="es", serie=""):
    try:
        data = _via_ia(tema, nicho, hechos, lang, serie)
        print(f"Guion: IA ({lang})" + (" [serie]" if serie else ""))
        if lang == "en" and not data.get("guion_es"):
            raise ValueError("IA no devolvio guion_es")
        return data
    except Exception as e:
        print(f"Guion: plantilla (IA no disponible: {e})")
        data = _plantilla(tema, nicho, serie)
        data["lang"] = "es"  # plantilla siempre en español
        return data
