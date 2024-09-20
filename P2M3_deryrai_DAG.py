'''
    =================================================


    Nama  : dery rai 


    Program ini dibuat untuk melakukan automatisasi transform dan load data dari PostgreSQL ke ElasticSearch. 
    Adapun dataset yang dipakai adalah dataset mengenai data student performance di salah satu sekolah.
    =================================================
'''
import datetime as dt
from datetime import timedelta

from elasticsearch import Elasticsearch

from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator

import pandas as pd
import psycopg2 as db

def loadingdata():
    '''
     Fungsi Fetch Data.

        - terhubung ke database PostgreSQL menggunakan modul psycopg2 menggunakan database, user, pass, host, dan port yang sudah disesuikan pada def fecth_data()
        - mengambil semua data dari tabel table_m3 
        - Anda menyimpan data tersebut ke dalam file CSV dengan nama P2M3_dery_data_raw.csv
'''
    conn=db.connect(dbname="airflow", user="airflow",host="postgres", password="airflow",port="5432")  
    df = pd.read_sql_query('SELECT * FROM table_m3', conn)
    df.to_csv('/opt/airflow/csv/P2M3_Dery_dataraw.csv')
    conn.close()

def cleaningdata():
    '''
     Fungsi Data Cleaning.
        - Data yang sudah di ambil dan di save dari Postgree akan di load kembali
        - Membersihkan nama kolom dengan mengubah huruf kapital menjadi huruf kecil dan menggunakan underscoring sebagai pengganti spasi`
        - Hasil data cleaning akan di save kedalam bentuk csv dengan nama P2M3_dery_data_clean.csv
'''
    df = pd.read_csv('/opt/airflow/csv/P2M3_Dery_dataraw.csv')    
    df.columns = df.columns.str.lower()
    df.columns = df.columns.str.replace(' ', '_')
    df.fillna(0, inplace=True)
    df.to_csv('P2M3_Dery_data_clean.csv') 

def posttoelasticsearch():
    '''
     Fungsi Insert into elastic search - with airflow.
        - Data yang sudah di dicleaning dan di save akan di load kembali
        - Anda menggunakan pustaka elasticsearch untuk berinteraksi dengan Elasticsearch
        - Setelah itu, memasukkan setiap baris data ke dalam Elasticsearch dengan menggunakan es.index()
        - es = Elasticsearch('http://elasticsearch:9200') URL di mana instansi Elasticsearch Anda sedang berjalan. Elasticsearch biasanya berjalan pada port 9200 secara default, dan URL yang Anda berikan menunjukkan bahwa 
        berjalan pada mesin yang sama (elasticsearch) di mana kode Anda berjalan.
'''
    es=Elasticsearch('http://elasticsearch:9200')
    df=pd.read_csv('/opt/airflow/csv/P2M3_Dery_data_clean.csv')  
    for i,r in df.iterrows():
        doc= r.to_json()
        res=es.index(index="p2m3",doc_type="doc",body=doc) 


default_args = {
    'owner': 'dery',
    'start_date': dt.datetime(2024, 9, 13, 10, 10,0) - dt.timedelta(hours=7),
    'retries': 1,
    'retry_delay': dt.timedelta(minutes=1),
}

with DAG('P2M3CleanData',
         default_args=default_args,
         schedule_interval='30 6 * * *',  # Setiap hari jam 06:30,
         catchup=False
         ) as dag:
    

    Fetchfromsql = PythonOperator(task_id='load',
                                 python_callable=loadingdata)
    
    Cleandata = PythonOperator(task_id='cleaning',
                                 python_callable=cleaningdata)

    upload = PythonOperator(task_id='upload',
                                 python_callable=posttoelasticsearch)


'''
     Fungsi Data Pipeline with Apache Airflow.
        - mendefinisikan  sebuah default_args untuk DAG tersebut seperti pemilik, tanggal mulai, jumlah percobaan, dan penundaan antar percobaan
        - lalu, mendefinisikan sebuah DAG (Directed Acyclic Graph) dengan nama 'p2m3'.
        - DAG dijadwalkan untuk dijalankan setiap hari pada jam 6: 30 menit
            - node_start: Membaca pesan bahwa proses membaca file CSV
            - node_fetcfromsql: Menjalankan fungsi loadingdata() untuk mengambil data dari PostgreSQL
            - node_cleandata: Menjalankan fungsi cleaningdata() untuk membersihkan data yang telah diambil.
            - node_upload: Menjalankan fungsi posttoelasticsearch() untuk memasukkan data yang telah dibersihkan ke Elasticsearch.
     Setelah mendefinisikan DAG, lalu membuat aliran antara node-node tersebut, dimulai dari node_fetchfromsql dan berakhir di node_upload.

    workflow : mengambil data dari database > membersihkan pada Data Cleaning > Menyimpan pada Elasticsearch menggunakan apache airflow
'''
Fetchfromsql >> Cleandata >> upload