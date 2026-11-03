
import socket
from pyspark.sql import SparkSession

spark = SparkSession.builder \
   .appName("reparto") \
   .getOrCreate()

# Leer los datos desde HDFS usando la IP del NameNode
rdd = spark.sparkContext.textFile(
   "hdfs://192.168.56.10:9000/user/prueba/datos.txt",
   8
)

# Mostrar en qué máquinas se ejecutan las particiones
reparto = rdd.mapPartitions(
   lambda it: [(socket.gethostname(), sum(1 for _ in it))]
).collect()

print("REPARTO:", reparto)

# Agrupar los números por su última cifra y guardar el resultado en HDFS
resultado = rdd.map(
   lambda x: (int(x) % 10, 1)
).reduceByKey(
   lambda a, b: a + b
)

resultado.saveAsTextFile(
   "hdfs://192.168.56.10:9000/user/prueba/salida"
)

spark.stop()
