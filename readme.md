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