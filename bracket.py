#!/usr/bin/python
import csv
import random
import re
import math
import sys

#################
## read args ####
#################
# weights[0] = baseline prob
# weights[1] = weight on seedings
# weights[2] = weight on pagerank
# weights[3] = weight on 3 pointers
# weights[4] = weight on free throws
# weights[5] = weight on defense
# weights[6] = cinderella team
if len(sys.argv)==7:
  weights=[0.1]
  if 0.0<=float(sys.argv[1])<=1.0: weights.append(min(0.9,max(0.1,float(sys.argv[1]))))
  else: weights.append(0.8)
  if 0.0<=float(sys.argv[2])<=1.0: weights.append(float(sys.argv[2]))
  else: weights.append(0.45)
  if 0.0<=float(sys.argv[3])<=1.0: weights.append(float(sys.argv[3]))
  else: weights.append(0.6)
  if 0.0<=float(sys.argv[4])<=1.0: weights.append(float(sys.argv[4]))
  else: weights.append(0.5)
  if 0.0<=float(sys.argv[5])<=1.0: weights.append(float(sys.argv[5]))
  else: weights.append(0.6)
  weights.append(sys.argv[6])
  
else: weights=[0.1,0.8,0.45,0.6,0.7,0.8,-1]

#####################################
## read season data and load stats ##
#####################################
season="cbb2016_noheader.csv"
id={}
with open(season, 'rb') as csvfile:
  lines = csv.reader(csvfile)
  for row in lines:
	id[row[0]]=row

#####################################
team_names="official_team_names"
names={}
with open(team_names, 'rb') as csvfile:
  lines = csv.reader(csvfile)
  for row in lines:
        names[row[0]]=row[2]

### verify that the cinderella team is valid ###
if str(weights[6]) not in id: weights[6]="0"

#########################
## read pagerank data ###
#########################
ranks="pagerank_results"
prank={}
with open(ranks, 'rb') as csvfile:
  lines = csv.reader(csvfile)
  for row in lines:
	prank[row[1]]=row[0]

###########################################
### determine winner of individual game ###
###########################################
def playgame(details,round,cindy):
  team1=details[1]
  team2=details[3]
  prob0=0.5

  ## apply seeding ##
  if details[4] in seeds[details[2]]: prob1=float(re.sub(r'%','',seeds[details[2]][details[4]]))/100
  elif details[2] in seeds[details[4]]: prob1=1-float(re.sub(r'%','',seeds[details[4]][details[2]]))/100
  else: prob1=0.5

  ## 3-point adjustment ##
  diff3 = abs(float(id[team1][23])-float(id[team2][23]))
  adj3 = max(0,1/(1+math.exp(0.0574-diff3*6.83264)) - 0.5)
  if float(id[team1][23])<=float(id[team2][23]): adj3=adj3*-1

  ## free throw adjustment ##
  diffft = abs(float(id[team1][26])-float(id[team2][26]))
  adjft = max(0,1/(1+math.exp(0.025-diffft*2.94298)) - 0.5)
  if float(id[team1][26])<=float(id[team2][26]): adjft=adjft*-1

  ## defense adjustment ##
  diffrb = abs(float(id[team1][28])/float(id[team1][2])-float(id[team2][28])/float(id[team2][2]))
  adjrb = max(0,1/(1+math.exp(-0.005-diffrb*0.07053)) - 0.5)
  if float(id[team1][28])/float(id[team1][2])<=float(id[team2][28])/float(id[team2][2]): adjrb=adjrb*-1

  ## pagerank adjustment ##
  if team1 in prank: r1=int(prank[team1])
  else: r1=999
  if team2 in prank: r2=int(prank[team2])
  else: r2=999
  diffpr=abs(r2-r1)
  if diffpr==0: adjpr=0
  elif diffpr==1: adjpr=0.01
  elif diffpr<=5: adjpr=0.02
  elif diffpr<=10: adjpr=0.03
  elif diffpr<=20: adjpr=0.04
  elif diffpr<=50: adjpr=0.05
  elif diffpr<=100: adjpr=0.06
  elif diffpr<=200: adjpr=0.07
  elif diffpr>200: adjpr=0.08
  if r2<r1: adjpr=adjpr*-1

  ## basic prob based on seeds ##
  prob = (weights[0]*prob0+weights[1]*prob1)/sum(weights[0:2])

  ### apply adjustments ###
  prob=prob+weights[3]*adj3+weights[4]*adjft+weights[5]*adjrb+weights[2]*adjpr
  if random.random()<prob: win=1
  else: win=2 

  ### cinderella override ###
  if round<=4 and team1==cindy: win=1
  elif round<=4 and team2==cindy: win=2

  ## return winning team and seed ##
  if win==1: return team1,details[2]
  else: return team2,details[4]

#####################################
### read historical seed matchups ###
#####################################
seedfile="seeds.csv"
seeds={}
with open(seedfile, 'rb') as csvfile:
  lines = csv.reader(csvfile)
  for row in lines:
    if row[0] not in seeds: seeds[row[0]]={}
    if row[1] not in seeds[row[0]]: seeds[row[0]][row[1]]=row[2]
	

#######################################################
## ROUND 0 (play-in round) requires special handling ##
#######################################################
round0={}
bracket0 = "bracket2016_round0.csv"
with open(bracket0, 'rb') as csvfile:
  lines = csv.reader(csvfile)
  for row in lines:
     winner,rank = playgame(row,0,str(weights[6]))
     print row[0],": ",winner,names[winner]
     round0[row[5]]=winner+","+rank

#####################################
## ROUND 1 also requires handling ###
#####################################
bracket = "bracket2016.csv"
games={}
with open(bracket, 'rb') as csvfile:
  lines = csv.reader(csvfile)
  for row in lines:
     ### complete bracket from round1 ###
     if row[0] in round0: 
	for a in round0[row[0]].split(','):
	  row.append(a)
     winner,rank = playgame(row,1,str(weights[6]))
     print row[0],": ",winner,names[winner]
     ### move winner to the next round ###
     rnum,gnum = re.sub(r'g','',row[0]).split('_')
     rnew = int(rnum)+1
     gnew = int(math.ceil(float(gnum)/2))
     if rnew not in games: games[rnew]={}
     if gnew not in games[rnew]: 
	games[rnew][gnew]=[]
	games[rnew][gnew].append("g"+str(rnew)+"_"+str(gnew))
     games[rnew][gnew].append(winner)
     games[rnew][gnew].append(rank)

################
## ROUNDS 2-6 ##
################
for r in 2,3,4,5,6:
  for a in games[r]:
    winner,rank = playgame(games[r][a],r,str(weights[6]))
    print games[r][a][0],": ",winner,names[winner]
    rnum,gnum = re.sub(r'g','',games[r][a][0]).split('_')
    rnew = int(rnum)+1
    gnew = int(math.ceil(float(gnum)/2))
    if rnew not in games: games[rnew]={}
    if gnew not in games[rnew]:
      games[rnew][gnew]=[]
      games[rnew][gnew].append("g"+str(rnew)+"_"+str(gnew))
    games[rnew][gnew].append(winner)
    games[rnew][gnew].append(rank)

