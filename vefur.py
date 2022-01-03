#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 14 09:16:26 2021

@author: jonatli
"""

import streamlit as st

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import psycopg2
import math
import plotly.express as px
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from PIL import Image
from urllib.request import urlopen

containers = ['natthagi1','natthagi2','natthagi3','stifla']
tol = ['Forsíða', 'Ljósleiðari','Hitanemar', 'Myndir']
sidelist = st.sidebar.radio('Hitamælingar',tol)


###   Gagnagrunnstenging ###
#@st.cache(allow_output_mutation=True)
def init_connection():
    return psycopg2.connect(**st.secrets["postgres"])
conn = init_connection()
### Azure tenging ###
connect_str = st.secrets["azure"]["connect_str"]
			  
#@st.cache(ttl=600)
def run_query(query):
	with conn.cursor() as cur:
		cur.execute(query)
		return cur.fetchall()


### Ljósleiðaraplott ###
def data():   
    
    a = 350
    b = 486
        
    S= run_query("SELECT * FROM public.\"Csudur\" WHERE time = (SELECT MAX(time) FROM public.\"Csudur\");")
    N= run_query("SELECT * FROM public.\"Cnordur\" WHERE time = (SELECT MAX(time) FROM public.\"Cnordur\");")
    S= list(S)
    S = S[0]
    ts = S[0]
    S = S[1:]
    S = S[a:b]
    S = np.array(S)
    N = list(N)
    N = N[0]
    tn = N[0]
    N = N[1:]
    N = N[a:b]
    N = np.array(N)
    N = N+5
    return S,N, ts,tn



def img():
    langsnid = plt.imread('img/langsnid.png')
    fig,axs = plt.subplots(3,1)
    axs[1].imshow(langsnid)
    axs[1].axis('off')
    
    
    skali_y = [math.floor(min([S_y.min(),N_y.min()])),math.ceil(max([S_y.max(),N_y.max()]))]
    
    axs[0].plot(N_y)
    axs[0].set_ylim(skali_y)
    axs[0].set_title('Skurður með mismunandi vörnum ')
    axs[0].grid()
    axs[0].set_ylabel('°C')
    axs[0].set_xlabel('m')
    
    axs[2].plot(S_y)
    axs[2].set_ylim(skali_y)
    axs[2].set_title('Samanburðar (óvarinn) ljósleiðari')
    axs[2].grid()
    axs[2].set_ylabel('°C')
    axs[2].set_xlabel('m')
    
    fig = plt.gcf()
    fig.set_size_inches(18.5, 10.5)
    fig.suptitle('Hitamælingar mismunandi jarðvegsvarna við Nátthaga\nGögn frá '+new_date)
    return fig

### Hitanemaplott  ###





### Vefsíðan ###

if sidelist == 'Forsíða':
    st.title('Hitamælingar í Nátthaga')
    st.subheader('Veldu úr listanum hér til vinstri')

elif sidelist == 'Ljósleiðari':
    
    S_y,N_y, ts, tn=data()
    new_date = tn.strftime('%d.%m.%Y %H:%M:%S')
    plot = img()
    
    
    st.title('Nátthagi, ljósleiðaramælingar')
    st.write(str('Nýjasta mæling frá '+new_date))
    st.pyplot(plot)

elif sidelist == 'Hitanemar':
    mælar = ['A 20cm','A 40cm','A 60cm', 'A 80cm','A 100cm','B 20cm','B 40cm','B 60cm','B 80cm',
              'B 100cm','Grus efri','Grus nedri','Hellur','ROR','Sandur tre 200','Sandur tre 400',
              'Sandur tre 600','Sandur tre 800','Sandur tre 1000','Vikur tre 200','Vikur tre 400',
              'Vikur tre 800','Vikur tre 1000']
    val = st.multiselect('Veldu mæla',mælar)
    #val = ['A 20cm']
    #Stoppa síðuna ef ekkert er valið.
    if not val:
        st.stop()
    
    ### Sæki dagsetningar max og mín fyrir allar valdar töflur ###
    minnst_fylki =[]
    max_fylki = []
    for tafla in val:
        strengur_min = str('SELECT MIN("Time") FROM \"'+tafla+'\"')
        strengur_max = str('SELECT MAX("Time") FROM \"'+tafla+'\"')
        minnst_t = run_query(strengur_min)
        max_t = run_query(strengur_max)
        minnst_fylki.append(minnst_t[0][0])
        max_fylki.append(max_t[0][0])
    
    #start, stop = st.select_slider('Tímabil',options = [min(minnst_fylki),max(max_fylki)]) 
    
    start = st.date_input('Upphaf',value=min(minnst_fylki), min_value= min(minnst_fylki),max_value= max(max_fylki))
    if not start:
        stop = st.date_input('Lok',value=min(minnst_fylki),min_value = min(minnst_fylki), max_value = max(max_fylki))
    else:
        stop = st.date_input('Lok',value=min(minnst_fylki), min_value = start, max_value = max(max_fylki))       
    start = start.strftime('%Y-%m-%d')
    stop = stop.strftime('%Y-%m-%d')                 
    
    #start = '2021-07-03'
    #stop = '2021-07-15'
    ### Sæki gögn eftir vali og dagsetningu
    gogn = pd.DataFrame(columns= ['Time','Temp', 'Mælir'])
    for tafla in val:
            strengur = str('SELECT * FROM \"'+tafla+'\" WHERE \"Time\" >\''+start+'\' AND \"Time\" <\''+stop+'\'')
            data = pd.DataFrame.from_records(run_query(strengur),columns = ['Time','Temp'])
            data['Mælir'] = tafla
            gogn = gogn.append(data,ignore_index= True)
            
    fig = px.line(gogn, x='Time', y='Temp', color = 'Mælir')
    st.plotly_chart(fig,use_container_width = False)
    #conn.close()

elif sidelist == 'Myndir':
	blob_service_client = BlobServiceClient.from_connection_string(connect_str)
	camera = st.radio('Myndavél',containers)
	container_name = camera
	container_client = blob_service_client.get_container_client(container_name)
	blob_list = container_client.list_blobs()

	# Make list of files by date
	fileList = pd.DataFrame(columns=['file', 'date','year','month','day','hour','minute'])
	for blob in blob_list:
	    file_name = blob.name
	    file_date =blob.creation_time
	    file_year = file_date.date().year
	    file_month = file_date.date().month
	    file_day = file_date.date().day
	    file_hour = file_date.time().hour
	    file_minute = file_date.time().minute
	    fileList = fileList.append({'file':file_name, 'date':file_date, 'year':file_year,'month': file_month,'day':file_day,'hour':file_hour,'minute':file_minute}, ignore_index=True)
	years = fileList['year'].unique()
	selYear = st.radio('Ár',years)
	months = fileList[fileList['year']==selYear]['month'].unique()
	selMonth =st.radio('Mánuður',months)
	days = fileList[(fileList['year']==selYear) & (fileList['month']==selMonth)]['day'].unique()
	selDay = st.radio('Dagur',days)
	hours = fileList[(fileList['year']==selYear) & (fileList['month']==selMonth) & (fileList['day']==selDay)]['hour'].unique()
	selHour = st.radio('Klukkustund',hours)
	minutes = fileList[(fileList['year']==selYear) & (fileList['month']==selMonth) & (fileList['day']==selDay) & (fileList['hour']== selHour)]['minute'].unique()
	selMinute = st.radio('Mínútur',minutes)
	selFile = fileList[(fileList['year']==selYear) & (fileList['month']==selMonth) & (fileList['day']==selDay) & (fileList['hour']== selHour) & (fileList['minute'] == selMinute)].iloc[0,0]   
	imageString = str('https://csb10033fff9dc1ffe0.blob.core.windows.net/'+camera+'/'+selFile)
	st.image(Image.open(urlopen(imageString)))
	
	
			   
			   
			   
			   
			   
			   
			   
