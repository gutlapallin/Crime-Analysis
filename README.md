# Senior Design Project - Chicago Crime Analysis and Prediction
This project focuses on Big Data Analysis. This project runs pre-analysis/cleans data, analyzes data, loads the data into a MySQL Databse and presents it on a Web Interface that uses an LLM Chatbot to infer insights about the data, based on predefined hypothesis. This analyzed a Chicago Crime Datasest of 14 million cases. 

# Contributors:
### Neha Gutapalli
### Tanya Carillo
### Eric Via
### Arleen Kaur
### Jade Someda

# Software Architecture: 
* Apache Spark (PySpark) for distributed processing on cluster environment (class-142.cs.ucr.edu)
* MySQL for aggregated results for further analysis and queries
* Spark JDBC Connector to write processed Spark DataFrames into MySQL tables efficiently
* Flask REST API provides the data from the MySQL database
* Vite build tool used to help in creating the React.js single page web application
* Web uses 3-tier architecture with database, backend, and frontend

# Implemnetation: 
Main Data Structure: Dictionaries/Nested Dictionary

Visualized: 

       Dictionary
       |__ sub-dictionary
       |       |__questions/hypotheses
       |__sub-dictionary
       |       |__questions/hypotheses
       |__ sub-dictionary
       |       |__questions/hypotheses
       |__sub-dictionary
              |__questions/hypotheses

# The Pipeline: 
       Raw Data → Pre-Processed/Clean Data on Pyspark → Data is Analyzed/Aggregated on PySpark → Data is formatted and loaded in MySQL Database → Database Tables are Shown on Web Interface

# The Workflow: (Cleaning Data --> Web Interface)
Overview: Raw Data → Pre-Process/Clean Data → Data Analysis → Data loaded into MySQL Database → Database Tables on Webpage 

1) Clean Data:\
   spark-submit test.py

2) Run Analysis and Generate SQL Tables in MySQL Database:\
   mysql -u root -D cs179g --socket=/home/cs179g/mysql/mysql.sock
   spark-submit --jars ~/libs/mysql-connector-j-9.4.0.jar part2_analysis.py

3) Run MySQL Database:\
   mysqld --user=cs179g --datadir=/home/cs179g/mysql/data --socket=/home/ cs179g/mysql/mysql
       .sock & mysql -u root -D cs179g --socket=/home/cs179g/mysql/mysql.sock

5) Run  Webpage:\
  cd project/CS179G/backend/ (terminal 1) \
 	cd project/CS179G/frontend/ (terminal 2)\
 	in backend: python3 app.py \
 	click open browser button\
 	in frontend: npm run dev\
 	(click open browser)

### Snapshot:

Workflow of files 

clean_chicago_data/test.py -> analysis/part2_analysis.py -> analysis/schema.sql -> backend/app.py -> frontend/tables.js ; etc 

# Demo

https://github.com/user-attachments/assets/37fe2161-8920-4793-bf21-56c687d5eec4


https://github.com/user-attachments/assets/f13dbb7c-b21d-48d7-902d-467da335f864





# Application
By exploring this data, insightful inferences can generated in order to better understand how to mitigate crime and provide helpful solutions. By identifying patterns predictions can be created.

