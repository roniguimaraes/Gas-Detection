#!/usr/bin/env python3
import datetime
import os

print("Alerta de vazamento de gas detectado! Script Python executado com sucesso.")
print("return to dock")
print(f"Current working directory: {os.getcwd()}")

# Log the execution time
current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
try:
    with open("backend/alert log.txt", "a") as log_file:
        log_file.write(f"Script executed at: {current_time}\n")
    print("Log written successfully")
except Exception as e:
    print(f"Error writing log: {e}")

# Aqui você pode adicionar mais lógica no futuro
