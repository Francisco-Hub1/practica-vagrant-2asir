#!/usr/bin/env python3

import json
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

JMX_URL = "http://192.168.56.10:9870/jmx"


def obtener_metricas():
    with urllib.request.urlopen(JMX_URL, timeout=5) as respuesta:
        datos = json.loads(respuesta.read().decode())

    metricas = {}

    for bean in datos.get("beans", []):
        nombre = bean.get("name", "")

        if "FSNamesystemState" in nombre:
            campos = [
                "NumLiveDataNodes",
                "NumDeadDataNodes",
                "UnderReplicatedBlocks",
                "MissingBlocks",
                "PendingReplicationBlocks",
            ]

            for campo in campos:
                if campo in bean:
                    metricas[campo] = bean[campo]

        if "FSNamesystem" in nombre:
            campos = [
                "CapacityTotal",
                "CapacityUsed",
                "CapacityRemaining",
            ]

            for campo in campos:
                if campo in bean:
                    metricas[campo] = bean[campo]

    return metricas


class Exportador(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path != "/metrics":
            self.send_response(404)
            self.end_headers()
            return

        try:
            metricas = obtener_metricas()

            salida = []

            for nombre, valor in metricas.items():
                salida.append(
                    f"hdfs_{nombre} {valor}"
                )

            contenido = ("\n".join(salida) + "\n").encode()

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "text/plain; version=0.0.4"
            )
            self.end_headers()
            self.wfile.write(contenido)

        except Exception as error:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(error).encode())


HTTPServer(("0.0.0.0", 9110), Exportador).serve_forever()
