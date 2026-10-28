import socket
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("reparto").getOrCreate()
rdd = spark.sparkContext.textFile("hdfs://namenode:9000/user/prueba/datos.txt", 8)

print("REPARTO:", rdd.mapPartitions(lambda it: [(socket.gethostname(), sum(1 for _ in it))]).collect())

rdd.map(lambda x: (int(x) % 10, 1)).reduceByKey(lambda a, b: a + b) \
   .saveAsTextFile("hdfs://namenode:9000/user/prueba/salida")
spark.stop()