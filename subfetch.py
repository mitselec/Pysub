# -*- coding: utf-8 -*-
"""
Created on Tue Jul 18 16:48:46 2017
First Working Version Concluded on Wed Oct 31 2018

Python Subtitle downloader
This script downloads the metadata of a Youtube video
that consist the subtitle and format them into one

Python 2.7.13

@author: Dimitris Dimopoulos
"""

import urllib2
import os,sys
from datetime import time, timedelta

#length of string of the timestamp used later in the program
timestamp_length =12

# file to be written to
file = "subtitle_file.xml"
file2 = "subtitle_option.xml"

#Ask user input
sub_var = raw_input("Please enter the youtube link: ")
#TODO:Find out if there is even subtitles for the video and give the user a choice
#It can be found from https://video.google.com/timedtext?type=list&v= +VideoId
#Or the Youtube API : https://www.youtube.com/api/timedtext?type=list&v=
#TODO:Save the subtitles with the name of the video 

#Giving the youtube link and searching for available subtitles
#Available subtitles will be printed as an option for the user
#If there are no available subtitles, the program will close.
url = "https://video.google.com/timedtext?type=list&v="+sub_var.split("=")[1]
response = urllib2.urlopen(url)
fh = open(file2,"w")
fh.write(response.read())
fh.close()

with open(file2,"rb") as infile:
    lines = infile.readlines()
infile.close()

languages =[]

if "<track" in lines == False:
    os.remove("subtitle_option.xml") #Delete the temporary file
    sys.exit("No available subtitles found!") 
else:
    options = lines[0].split('<track')
language =[]
for i in range(1,len(options)):
    language.append(options[i].split('lang_code="')[1].split('"')[0])
    
print "Available languages\n" 
for i in range(len(language)):
    print str(i)+"."+language[i]+"\n"
lang_input = raw_input("Please press the corresponding number: ")

url = "http://video.google.com/timedtext?lang="+language[int(lang_input)]+"&v="+sub_var.split("=")[1]
response = urllib2.urlopen(url)

#open the file for writing
fh = open(file, "w")

# read from request while writing to file
fh.write(response.read())
fh.close()

with open(file,"rb") as infile:
    lines = infile.readlines()
infile.close()

#Joining the text into a single string to segment easier
line_str = ''.join(map(str, lines))
#Replacing special characters and spliting the sentences
spec_char = ["&amp;#39;","&amp;quot;","&amp;lt;","&amp;gt;","&amp;"]
rep_char = ["'",'"',"<",">","&"]
for replacement in spec_char:
    if replacement in line_str:
        line_str = line_str.replace(replacement,rep_char[spec_char.index(replacement)]) 
sentence = line_str.split("<transcript>")[1].split("</text>")[:-1]

#Creating the subtitle file
file = "subtitle.srt"
fh = open(file,"w")

sentence_counter =0
time_segment = []
for sentence_part in sentence:
    sentence_counter +=1
    #Setting timestamps
    t = time(0,0,0,0)
    time_segment = sentence_part.split('>')[0].split('"')[1::2]
    #Forcing 3 decimals
    time_segment[0] = str("%5.3f" %float(time_segment[0]))
    time_segment[1] = str("%5.3f" %float(time_segment[1]))   
    t_start = timedelta(seconds = int(time_segment[0].split(".")[0]),milliseconds = int(time_segment[0].split(".")[1]))
    t_end = t_start +timedelta(seconds = int(time_segment[1].split(".")[0]),milliseconds = int(time_segment[1].split(".")[1]))
    #Writing Data into the subtitle file
    #Using the matroska format, for example
    #1
    #00:00:05.123 --> 00:00:10.456
    #Subtitle text
    #empty line
    #2
    #etc
    fh.write(str(sentence_counter) +'\n')
    #Adding missing digits to complete the timestamp string
    if len('0'+str(t_start)[:-3]) < timestamp_length:
        fh.write('0'+str(t_start)+'.000'+' --> '+'0'+str(t_end)[:-3]+'\n')
    elif len('0'+str(t_end)[:-3]) < timestamp_length:
        fh.write('0'+str(t_start)[:-3]+' --> '+'0'+str(t_end)+'.000'+'\n')
    else:
        fh.write('0'+str(t_start)[:-3]+' --> '+'0'+str(t_end)[:-3]+'\n')
    fh.write(sentence_part.split('">')[1]+'\n')
    fh.write("\n")
fh.close()
#Delete the temporary files created       
os.remove("subtitle_file.xml")
