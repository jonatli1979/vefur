#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 14 09:16:26 2021

@author: jonatli
"""

import streamlit as st

import matplotlib.pyplot as plt
import numpy as np

import psycopg2
import math

sidelist = st.sidebar('Hitamælingar',['Ljósleiðari', 'Hitanemar'])


#@st.cache(allow_output_mutation=True, hash_funcs={"_thread.RLock": lambda _: None})
def init_connection():
    return psycopg2.connect(**st.secrets["postgres"])
conn = init_connection()


def run_query(query):
	with conn.cursor() as cur:
		cur.execute(query)
		return cur.fetchall()
conn = init_connection()   
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
    #fig.savefig('ljosleidari.github.io/natthagi.svg', format='svg', dpi=1200)
    
    return fig
if sidelist == 'Ljósleiðari':
    
    S_y,N_y, ts, tn=data()
    new_date = tn.strftime('%d.%m.%Y %H:%M:%S')
    plot = img()
    
    
    st.title('Nátthagi, ljósleiðaramælingar')
    st.write(str('Nýjasta mæling frá '+new_date))
    st.pyplot(plot)

elif sidelist == 'Hitanemar':
    st.text('Í vinnslu')
#conn.close()
