from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when
from pyspark.ml.feature import VectorAssembler, StringIndexer
from pyspark.ml.classification import DecisionTreeClassifier
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import roc_curve, auc
from pyspark.ml import PipelineModel
from sklearn.tree import plot_tree
import pandas as pd

# Créer une session Spark
spark = SparkSession.builder.appName("TitanicAnalysis").getOrCreate()

# Charger le dataset Titanic depuis HDFS
df = spark.read.option("header", "true").option("sep", ";").csv("hdfs://namenode:8020/spark-data/titanic-passengers.csv")

# Afficher les premières lignes du dataset
print("\n" + "*" * 50 + "\nAffichage du dataset de départ !\n" + "*" * 50)
df.show(25)

# Vérifier les informations sur les colonnes du dataset
df.printSchema()

# -------------------- Pré-traitement et gestion des valeurs manquantes --------------------

# Remplir les valeurs manquantes dans 'Age' avec la moyenne et dans 'Embarked' avec la valeur la plus fréquente
mean_age = df.agg({"Age": "mean"}).collect()[0][0]
mode_embarked = df.groupby("Embarked").count().orderBy("count", ascending=False).first()[0]

df_cleaned = df.fillna({"Age": mean_age, "Embarked": mode_embarked})
df_cleaned = df.dropna(subset=["Pclass", "Age", "SibSp", "Parch", "Embarked", "Sex"])

# -------------------- Transformation des données --------------------

# Conversion des colonnes numériques en types appropriés
df_cleaned = df_cleaned.withColumn("Pclass", col("Pclass").cast("int"))
df_cleaned = df_cleaned.withColumn("Age", col("Age").cast("float"))
df_cleaned = df_cleaned.withColumn("SibSp", col("SibSp").cast("int"))
df_cleaned = df_cleaned.withColumn("Parch", col("Parch").cast("int"))

# Encodage de 'Embarked'
df_cleaned = df_cleaned.withColumn(
    "Embarked",
    when(col("Embarked") == "C", 0)
    .when(col("Embarked") == "Q", 1)
    .when(col("Embarked") == "S", 2)
    .otherwise(None)
)

# Encodage de 'Sex'
df_cleaned = df_cleaned.withColumn(
    "Sex",
    when(col("Sex") == "male", 1)
    .when(col("Sex") == "female", 0)
    .otherwise(None)
)

# Encodage de 'Survived'
df_cleaned = df_cleaned.withColumn(
    "Survived",
    when(col("Survived") == "No", 0)
    .when(col("Survived") == "Yes", 1)
    .otherwise(None)
)

# Afficher le dataset traité
print("\n" + "*" * 50 + "\nAffichage du dataset traité et encodé !\n" + "*" * 50)
df_cleaned.show(25)
df_cleaned.printSchema()


# -------------------- Transformation avec VectorAssembler --------------------

assembler = VectorAssembler(
    inputCols=["Pclass", "Age", "SibSp", "Parch", "Embarked", "Sex"],
    outputCol="features", 
    handleInvalid="skip"
)
df_transformed = assembler.transform(df_cleaned)

# Affichage des données transformées
print("\n" + "*" * 50 + "\nAffichage des données transformées avec VectorAssembler!\n" + "*" * 50)
df_transformed.select("features").show(truncate=False)


# -------------------- MapReduce avec Spark --------------------

# 1. MapReduce : Comptage des passagers par classe (Pclass)
pclass_count = df_cleaned.rdd.map(lambda row: (row["Pclass"], 1)) \
                            .reduceByKey(lambda a, b: a + b)

# 2. Calcul de la moyenne des âges par classe (Pclass)
pclass_age_avg = df_cleaned.rdd.map(lambda row: (row["Pclass"], row["Age"])) \
                              .groupByKey() \
                              .mapValues(lambda ages: sum(ages) / len(ages))

# 3. Pourcentage de survie par sexe (Sex)
survival_rate_by_sex = df_cleaned.rdd.map(lambda row: (row["Sex"], (row["Survived"], 1))) \
                                    .reduceByKey(lambda a, b: (a[0] + b[0], a[1] + b[1])) \
                                    .mapValues(lambda v: v[0] / v[1])

# Afficher les résultats de MapReduce avec formatage dans un seul print
results = "\n" + "*" * 50 + "\n"
results += "Affichage des résultats de MapReduce\n"
results += "*" * 50 + "\n\n"

# Comptage des passagers par classe (Pclass)
results += "Comptage des passagers par classe (Pclass):\n"
for pclass, count in pclass_count.collect():
    results += f"  - Classe {pclass} : {count} passagers\n"

# Moyenne des âges par classe (Pclass)
results += "\nMoyenne des âges par classe (Pclass):\n"
for pclass, avg_age in pclass_age_avg.collect():
    results += f"  - Classe {pclass} : Âge moyen = {avg_age:.2f} ans\n"

# Pourcentage de survie par sexe (Sex)
results += "\nPourcentage de survie par sexe (Sex):\n"
for sex, survival_rate in survival_rate_by_sex.collect():
    sexe_label = "Homme" if sex == 0 else "Femme"
    results += f"  - {sexe_label} : {survival_rate * 100:.2f}% de survie\n"

results += "\n" + "*" * 50

# Imprimer tous les résultats en une seule fois
print(results)


# -------------------- Entraînement du modèle d'Arbre de Décision --------------------

print("\n" + "*" * 50 + "\nEntraînement du modèle d'Arbre de Décision...\n" + "*" * 50)

train_data, test_data = df_transformed.randomSplit([0.8, 0.2], seed=1234)

dt_classifier = DecisionTreeClassifier(labelCol="Survived", featuresCol="features")
dt_model = dt_classifier.fit(train_data)

# Prédire sur l'ensemble de test
predictions = dt_model.transform(test_data)

# Afficher quelques résultats
print("\n" + "*" * 50 + "\nAperçu des prédictions :\n" + "*" * 50)
predictions.select("Survived", "prediction").show(10)

# Évaluer le modèle
evaluator = MulticlassClassificationEvaluator(
    labelCol="Survived", predictionCol="prediction", metricName="accuracy"
)
accuracy = evaluator.evaluate(predictions)
print("\n" + "*" * 50 + f"\nÉvaluation du modèle...\nAccuracy: {accuracy:.2f}\n" + "*" * 50)

# Générer le graphique des prédictions vs réel
pandas_df = predictions.select("Survived", "prediction").toPandas()

plt.figure(figsize=(6, 4))
plt.hist(pandas_df["prediction"], bins=2, alpha=0.7, label="Predictions", color="blue")
plt.hist(pandas_df["Survived"], bins=2, alpha=0.7, label="Actuals", color="orange")
plt.legend()
plt.title("Comparaison : Prédictions vs Réel")
plt.xlabel("Classes (0 = Non-Survécu, 1 = Survécu)")
plt.ylabel("Nombre d'occurrences")
plt.savefig("/tmp/predictions_vs_actuals.png")
plt.close()
print("\n" + "*" * 50 + "\nGraphique des prédictions vs réel généré avec succès et enregistré dans '/tmp/predictions_vs_actuals.png'.\n" + "*" * 50)


# -------------------- Visualisation : Courbe ROC --------------------

print("\n" + "*" * 50 + "\nGénération de la courbe ROC...\n" + "*" * 50)

survived_values = predictions.select("Survived").toPandas()
prob_values = predictions.select("probability").rdd.map(lambda row: row['probability'][1]).collect()
fpr, tpr, _ = roc_curve(survived_values, prob_values)
roc_auc = auc(fpr, tpr)

plt.figure(figsize=(8, 6))
plt.plot(fpr, tpr, color='darkorange', lw=2, label='ROC curve (area = %0.2f)' % roc_auc)
plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Receiver Operating Characteristic')
plt.legend(loc='lower right')
plt.savefig("/tmp/roc_curve.png")
plt.close()
print("\n" + "*" * 50 + "\nGraphique ROC généré avec succès et enregistré dans '/tmp/roc_curve.png'.\n" + "*" * 50)


# -------------------- Histogramme des âges --------------------

print("\n" + "*" * 50 + "\nGénération de l' Histogramme des âges...\n" + "*" * 50)

# Histogramme des âges
sns.histplot(df_cleaned.select("Age").toPandas(), kde=True)
plt.title("Distribution des âges des passagers")
plt.xlabel("Âge")
plt.ylabel("Fréquence")
plt.savefig("/tmp/age_distribution.png")
plt.close()
print("\n" + "*" * 50 + "\nHistogramme des âges généré avec succès et enregistré dans '/tmp/age_distribution.png'.\n" + "*" * 50)

# -------------------- Répartition des survivants --------------------

print("\n" + "*" * 50 + "\nGénération du Graphe de Répartition des survivants...\n" + "*" * 50)

# Répartition des survivants
survival_counts = df_cleaned.groupBy("Survived").count().toPandas()
sns.barplot(x="Survived", y="count", data=survival_counts, palette="Set2")
plt.title("Répartition des survivants")
plt.xlabel("Survécu (0 = Non, 1 = Oui)")
plt.ylabel("Nombre de passagers")
plt.savefig("/tmp/survival_distribution.png")
plt.close()
print("\n" + "*" * 50 + "\nGraphe de Répartition des survivants généré avec succès et enregistrédans '/tmp/survival_distribution.png'.\n" + "*" * 50)

# -------------------- Répartition par sexe et survie --------------------

print("\n" + "*" * 50 + "\nGénération du Graphe de Répartition par sexe et survie...\n" + "*" * 50)

# Répartition par sexe et survie
sex_survival = df_cleaned.groupBy("Sex", "Survived").count().toPandas()
sns.barplot(x="Sex", y="count", hue="Survived", data=sex_survival, palette="Set1")
plt.title("Répartition par sexe et survie")
plt.xlabel("Sexe")
plt.ylabel("Nombre de passagers")
plt.savefig("/tmp/sex_survival_distribution.png")
plt.close()
print("\n" + "*" * 50 + "\nGraphe de Répartion par sexe et survie généré avec succès et enregistré dans '/tmp/sex_survival_distribution.png'.\n" + "*" * 50)

# -------------------- Arbre de décision --------------------

from sklearn.tree import DecisionTreeClassifier
print("\n" + "*" * 50 + "\nGénération de l'Arbre de décision...\n" + "*" * 50)

# Préparer les données sous forme de DataFrame Pandas
df_copy = df_cleaned.toPandas()
X = df_copy[['Pclass', 'Age', 'SibSp', 'Parch', 'Sex', 'Embarked']]  # Features
y = df_copy['Survived']  # Target

# Créer un modèle Scikit-learn et l'entraîner
sklearn_dt_model = DecisionTreeClassifier(criterion='entropy', # Critère pour mesurer la qualité de la division (utilisation de l'entropie)
min_samples_leaf=3, # Nombre minimum d'échantillons requis pour qu'un nœud devienne une feuille
max_depth=3, # Limiter la profondeur maximale de l'arbre
)
sklearn_dt_model.fit(X, y)

plt.figure(figsize=(40, 40))
plot_tree(
    sklearn_dt_model,
    feature_names=X.columns.values,
    class_names=["Non-Survived", "Survived"],
    filled=True,
    rounded=True,
    impurity=False
)
plt.title("Visualisation de l'Arbre de Décision")

# Enregistrer l'image de l'arbre dans un fichier
output_path = "/tmp/decision_tree_model.png"
plt.savefig(output_path, bbox_inches='tight')
plt.close()
print("\n" + "*" * 50 + "\nSchéma de l'Arbre de décision généré avec succès et enregistré dans '/tmp/decision_tree_model.png'.\n" + "*" * 50)



# -------------------- Fin --------------------
spark.stop()
print("\n" + "*" * 50 + "\nScript terminé avec succès !\n" + "*" * 50)

