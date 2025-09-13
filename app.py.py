# app.py - MVP Agente WhatsApp com FastAPI

import os
import re
import json
import requests
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "CHANGE_ME")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID", "CHANGE_ME")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "CHANGE_ME")
GRAPH_URL = f"https://graph.facebook.com/v21.0/{WHATSAPP_PHONE_ID}/messages"

app = FastAPI(title="Agente WhatsApp – MVP")

# Catálogo simples
CATALOGO = {
    "dipirona": {"sku": "DIP500", "preco": 12.90, "estoque": 120},
    "ibuprofeno": {"sku": "IBU200", "preco": 18.50, "estoque": 60},
    "vitamina c": {"sku": "VITC10", "preco": 9.90, "estoque": 200},
}

# Função para enviar texto
def send_text(to: str, text: str) -> None:
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text[:4096]},
    }
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    resp = requests.post(GRAPH_URL, headers=headers, json=payload, timeout=30)
    if not resp.ok:
        print("Erro ao enviar:", resp.status_code, resp.text)

# Classificação simples de intenções
def classificar_intencao(texto: str) -> str:
    t = texto.lower()
    if "quero" in t or "comprar" in t:
        return "pedido"
    if "tem" in t or "preço" in t or "estoque" in t:
        return "estoque"
    if "atendente" in t or "humano" in t:
        return "humano"
    return "fallback"

def agente_responder(telefone: str, mensagem: str) -> str:
    intent = classificar_intencao(mensagem)
    if intent == "estoque":
        return "Temos dipirona por R$ 12,90. Estoque: 120 un."
    if intent == "pedido":
        return "Pedido criado! Enviaremos o link de pagamento em breve."
    if intent == "humano":
        return "Encaminhando para um atendente humano."
    return "Não entendi. Você pode perguntar 'tem dipirona?' ou 'quero 2 dipirona'."

@app.get("/webhook", response_class=PlainTextResponse)
async def verify(hub_mode: str = None, hub_challenge: str = None, hub_verify_token: str = None):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return hub_challenge
    raise HTTPException(status_code=403, detail="Token inválido")

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    try:
        entry = data.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])
        if messages:
            msg = messages[0]
            wa_from = msg.get("from")
            if msg.get("type") == "text":
                text = msg.get("text", {}).get("body", "")
            else:
                text = "(mensagem não textual)"
            resposta = agente_responder(wa_from, text)
            send_text(wa_from, resposta)
    except Exception as e:
        print("Erro:", e)
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"status": "ok", "mensagem": "Agente WhatsApp rodando"}
