# Práctica 2 ASIR – Clúster Big Data distribuido con Hadoop y Spark

## 1. Descripción del proyecto

Despliegue de un clúster Big Data distribuido utilizando tres tecnologías:

- **Vagrant:** creación y administración de las máquinas virtuales.
- **Ansible:** automatización de la instalación y configuración de Docker.
- **Docker:** ejecución de los servicios Hadoop HDFS y Apache Spark.

La infraestructura está formada por tres máquinas virtuales Ubuntu Server:

| Máquina | Función | Dirección IP |
|---|---|---|
| nodo1 | NameNode y Spark Master | 192.168.56.10 |
| nodo2 | DataNode 1 y Spark Worker 1 | 192.168.56.11 |
| nodo3 | DataNode 2 y Spark Worker 2 | 192.168.56.12 |

Tecnologías utilizadas:
- Hadoop 3.3.6
- Apache Spark 3.5.3
- Docker
- Ansible
- Vagrant
- Ubuntu 24.04

## 2. Arranque del clúster

Desde el directorio del proyecto, ejecutar:

```bash
vagrant up
```

Para comprobar el estado de las máquinas:

```bash
vagrant status
```

Para acceder a una máquina:

```bash
vagrant ssh nodo1
```

Para apagar las máquinas:

```bash
vagrant halt
```

## 3. Interfaces web

Una vez arrancadas las máquinas y los contenedores, se puede acceder a las interfaces desde el navegador del equipo anfitrión.

### Hadoop HDFS

| Servicio | URL |
|---|---|
| NameNode | http://192.168.56.10:9870 |
| DataNode 1 | http://192.168.56.11:9864 |
| DataNode 2 | http://192.168.56.12:9864 |

### Apache Spark

| Servicio | URL |
|---|---|
| Spark Master | http://192.168.56.10:8080 |
| Spark Worker 1 | http://192.168.56.11:8081 |
| Spark Worker 2 | http://192.168.56.12:8082 |

En la interfaz de Spark Master se puede comprobar que los dos Workers están conectados y aparecen en estado `ALIVE`.

## 4. Comprobar los contenedores Docker

Para consultar los contenedores del nodo1:

```bash
vagrant ssh nodo1 -c "sudo docker ps"
```

Para consultar los contenedores del nodo2:

```bash
vagrant ssh nodo2 -c "sudo docker ps"
```

Para consultar los contenedores del nodo3:

```bash
vagrant ssh nodo3 -c "sudo docker ps"
```

Los contenedores principales son:

- nodo1: `namenode` y `spark-master`.
- nodo2: `datanode1` y `spark-worker1`.
- nodo3: `datanode2` y `spark-worker2`.

## 5. Subir un fichero a HDFS

Primero, se crea un fichero de prueba dentro del contenedor NameNode:

```bash
vagrant ssh nodo1 -c "sudo docker exec namenode bash -c 'printf \"Hola Hadoop\nEste es un fichero de prueba\n\" > /tmp/datos.txt'"
```

Crear el directorio de entrada en HDFS:

```bash
vagrant ssh nodo1 -c "sudo docker exec namenode hdfs dfs -mkdir -p /user/prueba/entrada"
```

Subir el fichero:

```bash
vagrant ssh nodo1 -c "sudo docker exec namenode hdfs dfs -put -f /tmp/datos.txt /user/prueba/entrada/"
```

Comprobar que el fichero se ha subido:

```bash
vagrant ssh nodo1 -c "sudo docker exec namenode hdfs dfs -ls /user/prueba/entrada"
```

Consultar su contenido:

```bash
vagrant ssh nodo1 -c "sudo docker exec namenode hdfs dfs -cat /user/prueba/entrada/datos.txt"
```

## 6. Comprobar la replicación de HDFS

El clúster dispone de dos DataNodes, por lo que se utiliza un factor de replicación de 2.

Establecer la replicación:

```bash
vagrant ssh nodo1 -c "sudo docker exec namenode hdfs dfs -setrep -w 2 /user/prueba/entrada/datos.txt"
vagrant ssh nodo1 -c "sudo docker exec namenode hdfs dfs -setrep -R -w 2 /user/prueba/salida"
```
Comprobar los bloques y sus ubicaciones:

```bash
vagrant ssh nodo1 -c "sudo docker exec namenode hdfs fsck /user/prueba/entrada/datos.txt -files -blocks -locations"
```

También se puede comprobar el directorio de resultados del trabajo Spark:

```bash
vagrant ssh nodo1 -c "sudo docker exec namenode hdfs fsck /user/prueba/salida -files -blocks -locations"
```

El resultado correcto debe mostrar:

```text
Status: HEALTHY
Under-replicated blocks: 0
Missing blocks: 0
Corrupt blocks: 0
```

Los bloques deben aparecer almacenados en los dos DataNodes:

- 192.168.56.11
- 192.168.56.12

## 7. Ejecutar un trabajo distribuido con Spark

El proyecto incluye el fichero `reparto.py`, que contiene el trabajo de procesamiento distribuido.

Antes de ejecutar el trabajo, se elimina el directorio de salida si existe, ya que Spark no permite guardar resultados en un directorio HDFS que ya exista:

```bash
vagrant ssh nodo1 -c "sudo docker exec namenode hdfs dfs -rm -r -f /user/prueba/salida"
```

Ejecutar el trabajo Spark:

```bash
vagrant ssh nodo1 -c "sudo docker exec spark-master /opt/spark/bin/spark-submit --master spark://192.168.56.10:7077 --deploy-mode client --conf spark.driver.host=192.168.56.10 --conf spark.driver.bindAddress=0.0.0.0 /opt/spark-app/reparto.py"
```

El trabajo se envía al Spark Master, que distribuye las tareas entre los dos Workers.

En la ejecución se puede comprobar que los ejecutores se conectan desde:

- 192.168.56.11
- 192.168.56.12

El resultado muestra tareas repartidas entre `spark-worker1` y `spark-worker2`.

## 8. Consultar los resultados en HDFS

Listar los archivos generados:

```bash
vagrant ssh nodo1 -c "sudo docker exec namenode hdfs dfs -ls /user/prueba/salida"
```

Consultar los resultados:

```bash
vagrant ssh nodo1 -c "sudo docker exec namenode hdfs dfs -cat /user/prueba/salida/part-*"
```

Comprobar que el trabajo ha finalizado correctamente:

```bash
vagrant ssh nodo1 -c "sudo docker exec namenode hdfs dfs -ls /user/prueba/salida/_SUCCESS"
```

Spark genera varios archivos `part-*` con los resultados y un archivo `_SUCCESS` que indica que la ejecución terminó correctamente.

## 9. Comprobaciones finales

Para verificar el estado general del clúster:

1. Comprobar que las tres máquinas virtuales están arrancadas.
2. Comprobar que los contenedores Docker están activos.
3. Acceder a las interfaces web de Hadoop y Spark.
4. Verificar que los dos DataNodes están registrados.
5. Verificar que los dos Spark Workers aparecen como `ALIVE`.
6. Ejecutar el trabajo `reparto.py`.
7. Comprobar que los resultados se han guardado en HDFS.
8. Ejecutar `fsck` para comprobar la integridad y replicación de los bloques.

## 10. Resultado del despliegue

Se ha desplegado un clúster Big Data distribuido con tres máquinas virtuales. Hadoop HDFS almacena los datos distribuidos entre dos DataNodes y Spark ejecuta trabajos repartidos entre dos Workers.

Se ha comprobado el funcionamiento de la infraestructura, la ejecución distribuida del trabajo de prueba y la replicación de los datos en ambos DataNodes.

## Repositorio GitHub

https://github.com/Francisco-Hub1/practica-vagrant-2asir


## 11. Monitorización del clúster

El clúster dispone de un sistema de monitorización basado en **Prometheus, Grafana, Alertmanager, Node Exporter y cAdvisor**, junto con un exportador específico para HDFS. Este sistema permite supervisar el estado de las máquinas virtuales, los contenedores, HDFS y Spark, además de generar alertas cuando se detectan problemas.

### 11.1. Acceso a las herramientas

Una vez iniciado el clúster con `vagrant up`, se puede acceder a las siguientes interfaces desde el navegador:

| Herramienta | URL | Puerto | Función |
|---|---|---:|---|
| Grafana | http://192.168.56.10:3000 | 3000 | Visualización de métricas y dashboards |
| Prometheus | http://192.168.56.10:9090 | 9090 | Consulta y almacenamiento de métricas |
| Alertmanager | http://192.168.56.10:9093 | 9093 | Gestión y envío de alertas |
| NameNode | http://192.168.56.10:9870 | 9870 | Administración y estado de HDFS |
| Spark Master | http://192.168.56.10:8080 | 8080 | Estado del clúster Spark |
| Spark Worker 1 | http://192.168.56.11:8081 | 8081 | Estado del primer Worker |
| Spark Worker 2 | http://192.168.56.12:8082 | 8082 | Estado del segundo Worker |

Los exportadores también exponen métricas para Prometheus:

- **Node Exporter:** puerto `9100` en cada nodo. Recoge métricas del sistema operativo.
- **cAdvisor:** puerto `8085` en cada nodo. Recoge métricas de los contenedores Docker.
- **Exportador HDFS:** puerto `9110` en el nodo principal. Publica las métricas de HDFS.

### 11.2. Credenciales de Grafana

La imagen de Grafana utiliza inicialmente las credenciales predeterminadas:

- Usuario: `admin`
- Contraseña: `admin`

En el primer acceso, Grafana solicita establecer una nueva contraseña.

Para cambiarla desde la interfaz:

1. Acceder a Grafana.
2. Abrir el menú del perfil del usuario.
3. Entrar en la configuración del perfil.
4. Seleccionar la opción para cambiar la contraseña.
5. Introducir la contraseña actual y la nueva.

Si se pierde la contraseña y es necesario restablecerla, se puede ejecutar desde WSL:

```bash
vagrant ssh nodo1 -c 'sudo docker exec grafana grafana cli admin reset-admin-password "NUEVA_CONTRASEÑA"'
```

Se debe sustituir `NUEVA_CONTRASEÑA` por la contraseña deseada.

El servicio utiliza el volumen persistente `grafana-data`, donde se almacenan los datos de Grafana.

### 11.3. Métricas recogidas

Prometheus realiza una recogida de métricas cada **15 segundos** y evalúa las reglas de alertas con el mismo intervalo.

**Métricas de las máquinas virtuales**

Se obtienen mediante Node Exporter:

- Uso de CPU.
- Memoria utilizada y disponible.
- Espacio de disco utilizado y disponible.
- Estado de los sistemas de archivos.

**Métricas de los contenedores**

Se obtienen mediante cAdvisor:

- Uso de CPU por contenedor.
- Consumo de memoria.
- Actividad y recursos utilizados por los contenedores Docker.

**Métricas de HDFS**

Se obtienen mediante un exportador Python propio, situado en `monitoring/hdfs-exporter.py`.

Este exportador consulta la API JMX del NameNode:

```text
http://192.168.56.10:9870/jmx
```

A partir de la información recibida, publica las siguientes métricas:

- `hdfs_NumLiveDataNodes`: DataNodes activos.
- `hdfs_NumDeadDataNodes`: DataNodes inactivos.
- `hdfs_UnderReplicatedBlocks`: bloques con replicación insuficiente.
- `hdfs_MissingBlocks`: bloques perdidos.
- `hdfs_PendingReplicationBlocks`: bloques pendientes de replicación.
- `hdfs_CapacityTotal`: capacidad total de HDFS.
- `hdfs_CapacityUsed`: capacidad utilizada.
- `hdfs_CapacityRemaining`: capacidad disponible.

El exportador publica estas métricas en el puerto `9110`, en la ruta `/metrics`.

**Métricas de Spark**

Spark utiliza el archivo `monitoring/spark/metrics.properties`, que configura `PrometheusServlet` para exponer métricas en formato Prometheus.

Las rutas configuradas son:

- Master: `/metrics/master/prometheus`.
- Workers: `/metrics/worker/prometheus`.
- Aplicaciones: `/metrics/applications/prometheus`.

También se habilita `JvmSource` para recoger métricas de la máquina virtual Java.

Prometheus consulta los siguientes objetivos:

| Servicio | Dirección | Ruta |
|---|---|---|
| Spark Master | `192.168.56.10:8080` | `/metrics/master/prometheus` |
| Spark Worker 1 | `192.168.56.11:8081` | `/metrics/worker/prometheus` |
| Spark Worker 2 | `192.168.56.12:8082` | `/metrics/worker/prometheus` |

Entre los datos que se pueden observar se encuentran los Workers activos y las aplicaciones en ejecución.

### 11.4. Alertas configuradas

Las reglas se encuentran en `monitoring/prometheus/alert-rules.yml`.

| Alerta | Condición | Tiempo de espera | Severidad |
|---|---|---:|---|
| `ServicioCaido` | Un servicio o exportador deja de responder | 2 minutos | Crítica |
| `DataNodesInsuficientes` | Hay menos de 2 DataNodes activos | 2 minutos | Crítica |
| `BloquesSinReplicar` | Hay bloques con replicación insuficiente | 5 minutos | Aviso |
| `DiscoSeLlenara` | La predicción indica que el disco se llenará en menos de 24 horas | 10 minutos | Aviso |

Alertmanager gestiona las alertas y las envía mediante Telegram. Su configuración se encuentra en `monitoring/alertmanager/alertmanager.yml`.

La notificación se agrupa por nombre de alerta. Se espera 30 segundos antes de enviar el primer grupo, se establece un intervalo de 5 minutos entre grupos y se repiten las notificaciones cada 4 horas. También se envían notificaciones cuando las alertas se resuelven.

El token del bot se almacena en el archivo `monitoring/alertmanager/telegram-token`, separado de la configuración principal para evitar incluirlo directamente en el repositorio.

### 11.5. Dashboard de Grafana

Grafana dispone de un dashboard llamado **Clúster Big Data**, organizado en cuatro apartados:

1. **¿Está vivo?**: estado de los objetivos monitorizados, DataNodes activos y Workers de Spark.
2. **¿Van justos los recursos?**: uso de CPU, memoria y disco de las máquinas y los contenedores.
3. **¿Cómo está HDFS?**: capacidad utilizada y disponible, y bloques pendientes de replicación.
4. **¿Qué está haciendo Spark?**: aplicaciones en ejecución y consumo de CPU de los Workers.

El dashboard se encuentra en `monitoring/grafana/dashboards/cluster-big-data.json` y se configura mediante los archivos de provisioning de Grafana.

### 11.6. Reproducción de los experimentos

Los experimentos permiten comprobar el comportamiento del clúster y de la monitorización ante distintas situaciones.

**Experimento A. Comparación de Spark con dos Workers y un Worker**

1. Arrancar el clúster con `vagrant up`.
2. Comprobar en la interfaz de Spark Master que los dos Workers están activos.
3. Eliminar la salida de una ejecución anterior:

   ```bash
   vagrant ssh nodo1 -c "sudo docker exec namenode hdfs dfs -rm -r -f /user/prueba/salida"
   ```

4. Ejecutar el trabajo distribuido:

   ```bash
   vagrant ssh nodo1 -c "sudo docker exec spark-master /opt/spark/bin/spark-submit --master spark://192.168.56.10:7077 --deploy-mode client --conf spark.driver.host=192.168.56.10 --conf spark.driver.bindAddress=0.0.0.0 /opt/spark-app/reparto.py"
   ```

5. Registrar la duración de la ejecución y observar el consumo de CPU de ambos Workers en Grafana.
6. Detener el segundo Worker desde WSL:

   ```bash
   vagrant ssh nodo3 -c "sudo docker stop spark-worker2"
   ```

7. Comprobar en Spark Master que solamente queda un Worker activo.
8. Eliminar la salida anterior y volver a ejecutar el mismo trabajo:

   ```bash
   vagrant ssh nodo1 -c "sudo docker exec namenode hdfs dfs -rm -r -f /user/prueba/salida"
   ```

   ```bash
   vagrant ssh nodo1 -c "sudo docker exec spark-master /opt/spark/bin/spark-submit --master spark://192.168.56.10:7077 --deploy-mode client --conf spark.driver.host=192.168.56.10 --conf spark.driver.bindAddress=0.0.0.0 /opt/spark-app/reparto.py"
   ```

9. Registrar la duración y el consumo de CPU con un solo Worker.
10. Volver a iniciar el segundo Worker:

    ```bash
   vagrant ssh nodo3 -c "sudo docker start spark-worker2"
    ```

11. Comparar los resultados de las dos ejecuciones.

**Experimento B. Pérdida de un nodo y recuperación de HDFS**

1. Arrancar el clúster y comprobar que HDFS tiene dos DataNodes activos.
2. Guardar en HDFS un fichero con factor de replicación 2.
3. Registrar la hora de inicio del experimento.
4. Apagar el nodo 3 desde el directorio del proyecto:

   ```bash
   vagrant halt nodo3
   ```

5. Observar en Prometheus y Grafana la pérdida del DataNode y del Worker de Spark.
6. Comprobar la evolución de las alertas y las notificaciones de Alertmanager.
7. Verificar que el fichero de HDFS sigue siendo accesible desde el NameNode.
8. Volver a iniciar el nodo:

   ```bash
   vagrant up nodo3
   ```

9. Comprobar que el DataNode y el Worker vuelven a estar activos y que HDFS recupera su estado.

**Experimento C. Medición del consumo en reposo**

1. Arrancar el clúster completo.
2. Comprobar que todos los servicios están activos.
3. No ejecutar trabajos de Spark ni operaciones adicionales durante 30 minutos.
4. Seleccionar en Grafana el intervalo de los últimos 30 minutos.
5. Registrar el consumo de CPU, memoria y disco de las tres máquinas virtuales.
6. Observar también el consumo de los contenedores de monitorización y de Big Data.
7. Comparar estos datos con los obtenidos durante el experimento A para valorar el coste de mantener la infraestructura y la monitorización funcionando en reposo.

Los resultados y las capturas de los tres experimentos se recogen en el informe PDF de la práctica.

### 11.7. Despliegue de la monitorización mediante Ansible

La configuración de la monitorización está automatizada mediante el rol `monitoring`.

Para desplegar únicamente la monitorización, sin volver a desplegar los servicios de Hadoop y Spark, ejecutar desde el directorio raíz del proyecto:

```bash
ansible-playbook -i .vagrant/provisioners/ansible/inventory/vagrant_ansible_inventory provision/monitoriza.yml
```

Para desplegar la infraestructura completa mediante el playbook principal:

```bash
ansible-playbook -i .vagrant/provisioners/ansible/inventory/vagrant_ansible_inventory provision/site.yml
```

La automatización permite repetir la configuración de los servicios y de la monitorización de forma ordenada.

### Configuración de Telegram para Alertmanager

Para recibir alertas de Telegram en una instalación nueva:

1. Crear el archivo `monitoring/alertmanager/telegram-token`.
2. Introducir en él el token del bot de Telegram, sin publicarlo en Git.
3. Asignar permisos privados al archivo: `chmod 600 monitoring/alertmanager/telegram-token`.
4. Sustituir el valor de ejemplo `123456789` de `chat_id` en `monitoring/alertmanager/alertmanager.yml` por el identificador del chat correspondiente.
5. Reiniciar Alertmanager para aplicar los cambios.

El token se excluye del repositorio mediante `.gitignore`.

---

## 12. Repositorio del proyecto en GitHub

El código fuente, los playbooks de Ansible, los roles, los archivos de configuración, las reglas de alerta y el dashboard de Grafana están disponibles en el siguiente repositorio:

**[Acceder al repositorio GitHub – Práctica 2](https://github.com/Francisco-Hub1/practica-vagrant-2asir/tree/main)**

