#!/usr/bin/env python
# coding: utf-8

# In[71]:


import pandas as pd, numpy as np, requests, re, html5lib
from datetime import date, timedelta, datetime
from bs4 import BeautifulSoup


# In[72]:


def LinksPartidas(Bsoup):
    # dado uma página de partidas "Bsoup" do vlr.gg, pega o link de cada partida
    # no formato 'https://www.vlr.gg/'+links[i]
    # detalhe que a função inverte a ordem das partidas, pra pegar da mais antiga pra mais nova
    linksnovo_pro_antigo = []
    links = []
    for tag in Bsoup.find_all('a', href = True):
        try:
            if int(tag['href'][1]):
                linksnovo_pro_antigo.append(tag['href'])
        except:
            #print('url pulada: ', tag['href'])
            pass
    for i in range(len(linksnovo_pro_antigo)):
        links.append(linksnovo_pro_antigo[len(linksnovo_pro_antigo)-1-i])
    return links


# In[83]:


df = pd.DataFrame()
url = 'https://www.vlr.gg/matches/results/'
url_pag = 'https://www.vlr.gg/matches/results/?page='

# # pegar partidas desta data, ou seja, ontem
data_pegar = date.today() - timedelta(days = 1)
# # garante que pega todas as partidas de ontem, com folga
pagina_inicial = 3
nome_col = 0

for k in range(pagina_inicial, 0, -1): 
    print('pag. ', str(k+1), ' completa')
    matches_page = requests.get(url_pag + str(k))
    Bsoup = BeautifulSoup(matches_page.text, 'html.parser')
    Links = LinksPartidas(Bsoup)
    m = 0
    comeco = 0
    while m < len(Links):
        if comeco == 0:
            for p in range(len(Links)):
                match_url = 'https://www.vlr.gg' + Links[p]
                match_soup = BeautifulSoup(requests.get(match_url).text, 'html.parser')
                data_partida = (datetime.strptime(
                                        match_soup('div', class_ = 'moment-tz-convert')[0]
                                        .get('data-utc-ts'), "%Y-%m-%d %H:%M:%S")
                                        .date())
                if data_partida == data_pegar:
                    m = p
                    comeco = 1
                    break
            if m == 0:
                m = len(Links)
        variavel = m
        
        for h in range(variavel,len(Links)):
            match_url = 'https://www.vlr.gg' + Links[h]
            match_soup = BeautifulSoup(requests.get(match_url).text, 'html.parser')
            print(match_url)
            try:
                if (match_soup('div', class_ = 'wf-title-med')[0].text.find('TBD') == -1 and
                        match_soup('div', class_ = 'wf-title-med')[1].text.find('TBD') == -1 and
                        match_soup('div', class_ = 'vm-stats-container')[0].text.find('No data available for this match') == -1 and
                        len(match_soup('tbody')[2]('tr')[0]('td')[1]('div')[0].contents) > 1):
                        #and
                        #match_soup('tbody')[2]('tr')[0]('td')[3]('span')[1].text != ' ' and
                        #match_soup('tbody')[3]('tr')[0]('td')[3]('span')[1].text != ' '):
                    break
            except:
                exceptions.append(match_url)
                pass
            m += 1
        
        
        if m >= len(Links):
            break
            
        panda = pd.read_html(match_url)        
        temp = pd.concat([panda[2], panda[3]], ignore_index=True)
        
        try:
            temp2 = {'scores_team_1':[int(match_soup('div', class_ = 'js-spoiler')[0]('span')[0].text)] ,
                    'scores_team_2':[int(match_soup('div', class_ = 'js-spoiler')[0]('span')[2].text)]}
        except:
            temp2 = {'scores_team_1' : [], 'scores_team_2' : []}
            print('erro placar pag: ', k)
            pass
        for i in range(0, len(panda)-2, 2):
            temp2['scores_team_1'].append(int(match_soup('div', class_ = 'score')[i].text))
            temp2['scores_team_2'].append(int(match_soup('div', class_ = 'score')[i+1].text))
            
        temp2 = pd.DataFrame(temp2)
        temp = pd.concat([temp, temp2], axis = 1)
        
        if nome_col == 0:
            colunas_v = panda[2].columns.tolist()
            colunas_n = [[],[],[],[],[]]
            for coluna in colunas_v:
                colunas_n[0].append('Map 1'+coluna)
                colunas_n[1].append('Map 2'+coluna)
                colunas_n[2].append('Map 3'+coluna)
                colunas_n[3].append('Map 4'+coluna)
                colunas_n[4].append('Map 5'+coluna)
            nome_col += 1
            
        panda[0].rename(columns = dict(zip(colunas_v, colunas_n[0])), inplace = True)
        panda[1].rename(columns = dict(zip(colunas_v, colunas_n[0])), inplace = True)
        
        temp = pd.concat([temp, pd.concat([panda[0], panda[1]], ignore_index=True)], axis = 1)
        for j in range(4, len(panda), 2):
            panda[j].rename(columns = dict(zip(colunas_v, colunas_n[j//2-1])), inplace = True)
            panda[j+1].rename(columns = dict(zip(colunas_v, colunas_n[j//2-1])), inplace = True)
            temp = pd.concat([temp, pd.concat([panda[j], panda[j+1]], ignore_index=True)], axis = 1)
        
        df = pd.concat([df, temp], ignore_index = True)
        df = pd.concat([df, pd.DataFrame(np.full(df.shape[1], np.nan)[None], columns = df.columns)])
        print(df.shape)

        m += 1
    
print('pag. ', str(1), ' completa')
df.to_csv(f'jogos_por_dia\{str(data_pegar)}.csv')
            

