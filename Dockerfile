# Use an official OpenJDK runtime as a parent image
FROM maven:3.9-eclipse-temurin-23 As build

# Set the working directory in the container
WORKDIR /app

COPY . .

RUN mvn clean install



FROM eclipse-temurin:23-jre-alpine AS deploy

ARG JAR_FILE="/app/target/BackDemo-0.0.1-SNAPSHOT.jar"

# Définir les variables d'environnement pour l'exécution

ENV SPRING_PROFILES_ACTIVE=azure


COPY --from=build ${JAR_FILE} /opt/app/app.jar

RUN chmod u+x /opt/app/app.jar

WORKDIR /opt/app


EXPOSE 8080

CMD ["java", "-jar", "/opt/app/app.jar"]