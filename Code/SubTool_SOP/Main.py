import os
import stat
import shutil
import tkinter as tk
import tkinter.font as tkFont
import tkinter.filedialog
from pprint import pprint

path=''   # 不提前定义global的话，函数内初始化引用会出错
wpath=''
wAudiopath=''
reaperConnect=0
wwiseConnect=0
version="1.0"
title="Reaper SOP Tool"
#version="0.7.3" 来自的主版本

#---------- Set Global Vars & Functions ----------#

def ConnectToReaper():
    global reaperConnect
    print("1")
    varTextReaper.set("Trying To Connect To Reaper")
    try:
        import reapy
        #reapy.configure_reaper()   #本来想用这个来Debug,结果打包之后调用这个函数会设置错误的python路径，因此这个try废了
    except:
        PrintReaperError()
        reaperConnect=0
        PrintLog("<<<Reapy Configuration Failed. Please Check Python settings at 'Preference/Plug-ins/ReaScript' and Restart Reaper>>>")
        PrintLog("<<<请确保Reaper处于开启状态，并且Preference/Plug-ins/ReaScript中关于python的设置都正确。Reaper的网络权限也需要打开。修改设置后重启Reaper以及此工具>>>")
        return

    
    print("2")
    global RPR 
    RPR = reapy.reascript_api

    
    print("3")
    try:
        global project 
        project = reapy.Project()
        print(project)
    except:
        PrintReaperError()
        reaperConnect=0
        PrintLog("===Cannot Connect Reaper via reapy. Please Restart This Tool")
        PrintLog("===reapy模块调用失败，请打开Reaper再重启此工具。如果仍不成功，请检查Reaper设置")
        return

    
    print("4")
    global TargetTrack   # 经测试，reapy的track不能被Reascript调用，因此尽量全用Reascipt的API
    TargetTrack= RPR.GetTrack(project,0)
    print(TargetTrack)
    
    print("5")
    varTextReaper.set("Success To Connect To Reaper")
    labelReaper['fg']='green'
    reaperConnect=1
    PrintLog("----Success To Connect To Reaper----")
    PrintLog("----连接Reaper成功，请选择需要批处理的文件夹----")

def findallfiles(path):                     # 遍历文件夹的generator，包括子文件夹，返回（文件名，文件地址）
    for root,dirs,files in os.walk(path):
        for file in files:            
            yield file,root                 # 用yield而不是return，定义的是生成器，适用于遍历，占用较少内存

def Normalize(item):
    if (varCheckNormalize.get()==1):
        RPR.SetMediaItemSelected(item,1)        # Select Item
        if (varCheckFilter2.get()==1):      # 如果需要忽略silent文件
            RMS = RPR.NF_GetMediaItemAverageRMS(item)
            #PrintLog("RMS="+str(RMS))
            if RMS<-60:
                PrintLog("RMS="+str(RMS)+" so Skip Normalize")
                return
        RPR.Main_OnCommandEx(RPR.NamedCommandLookup("_BR_NORMALIZE_LOUDNESS_ITEMS_LU"),0,project)   #标准化

def RenderFileInReaper(proj,path):       # 将path文件顶头导入第一轨，渲染，最后删除这个item
    RPR.Main_OnCommandEx(40042,0,proj)   # move Cursor to 0
    RPR.InsertMedia(path,0)                 # Insert file onto selected track
    #track=proj.tracks[0]
    #item=track.items[0]
    item =RPR.GetMediaItem( project, 0 )
    Normalize(item)
    RPR.Main_OnCommandEx(42230,0,proj)   # Render with last render setting       
    track= RPR.GetMediaItem_Track( item )
    RPR.DeleteTrackMediaItem( track, item )
        
def SetReaperRenderSetting(proj,path):  # 设置Render参数
    #PrintLog("set render setting "+ str(path))
    RPR.GetSetProjectInfo(proj,"RENDER_SETTINGS",0,1)
    RPR.GetSetProjectInfo(proj,"RENDER_BOUNDSFLAG",1,1)
    RPR.GetSetProjectInfo(proj,"RENDER_ADDTOPROJ",0,1)
    RPR.GetSetProjectInfo_String(proj,"RENDER_FILE",path,1)
    RPR.GetSetProjectInfo_String(proj,"RENDER_PATTERN","temp",1)
    RPR.GetSetProjectInfo_String(proj,"RENDER_FORMAT2","",1)
    retval, mproj, desc, valuestrNeedBig,is_set= RPR.GetSetProjectInfo_String(proj,"RENDER_FORMAT","",0)
    #print(retval)
    #print(mproj)
    #print(desc)
    #print(valuestrNeedBig)
    if varCheckMp3.get()==1 :
        RPR.GetSetProjectInfo_String(proj,"RENDER_FORMAT","l3pm",1)
    else:
        RPR.GetSetProjectInfo_String(proj,"RENDER_FORMAT","evaw",1)
    
def BranchProcess():# 开始批处理
    if reaperConnect==0:
        PrintLog("Please Connect Reaper")
        return
    if path =='':
        PrintLog("<<<Please Choose a Folder>>>")
        PrintLog("<<<请先选择一个文件夹>>>")
        return
    PrintLog("Prepare to Process "+ path)
    SetReaperRenderSetting(project,path)  # 设置Reaper工程的渲染参数
    RPR.SetOnlyTrackSelected(TargetTrack)  # 强制选择第一个轨道
    for file,root in findallfiles(path):    # 遍历整个文件夹，将每个文件导入reaper，渲染之后的文件替换原来的文件。
        fullname = os.path.join(root,file)
        fullname = os.path.normpath(fullname)  #去掉反斜杠
        newfullname=fullname
        tempPath,oldext=os.path.splitext(fullname)
        
        if (varCheckFilter1.get()==1)and(oldext!='.wav'):
            PrintLog("Skip  "+fullname)
            continue
        
        PrintLog ("Processing  " + fullname)
        RenderFileInReaper(project,fullname)
        
        if varCheckMp3.get()==1 :
            ext='.mp3'
            newfullname=os.path.normpath(tempPath+ext)
        else:
            ext='.wav'
            newfullname=os.path.normpath(tempPath+ext)

        try:
            os.remove(fullname)
        except:
            #PrintLog("Try to make file writable...")
            try:
                os.chmod(fullname,stat.S_IWRITE)
            except:
                PrintLog("!!!! Failed to Process a read-only file !!!!")
                os.remove(path + r"\temp"+ext)
                return
            else:
                shutil.move(path + r"\temp"+ext ,newfullname)
                #PrintLog("Finished a read-only file")
        else:   
            shutil.move(path + r"\temp"+ext ,newfullname)
            PrintLog("Finished")

    PrintLog("---SOP Finished---")
    
def UpdatePath():                   # 用户选择文件夹路径
    global path
    PrintLog("Select Folder ...")
    path_ = tk.filedialog.askdirectory()   
    if path_=='':
        return
    path = path_
    varTextFolder.set(path)
    PrintLog ("Get Directory "+ path)

# Log
def PrintLog(string):                       # 在GUI里显示Log
    logtext.insert(tk.END, string + '\n') 
    logtext.see(tk.END)
    logtext.update()

def PrintReaperError():
    varTextReaper.set("Failed To Connect To Reaper")
    labelReaper['fg']='red'
    PrintLog("<<<Failed To Connect To Reaper>>>")

def CheckNormalize():
    if reaperConnect==1:
        if (varCheckNormalize.get()==1):
            PrintLog("+++ (SWS needed) Loudness Normalize On (change settings at 'SWS/BR:Global loudness preferences') +++")
            PrintLog("+++ 响度标准化开启(需要SWS插件)(音量数值在SWS/BR:Global loudness preferences 中设置) +++")
        else:
            PrintLog("+++ Loudness normalize off +++")

def CheckMp3():
    if reaperConnect==1:
        SetReaperRenderSetting(project,path)
        if varCheckMp3.get()==1:
            PrintLog("Output Format: Mp3")
        else:
            PrintLog("Output Format: Wave")
        
def CheckFilter1(): #过滤掉非Wave文件
    if varCheckFilter1.get()==1:
        PrintLog("Only Wave Files will be Processed")
    else:
        PrintLog("Prcess all type of files")
    
def CheckFilter2(): #过滤掉可能是底噪的文件
    if varCheckFilter2.get()==1:
        PrintLog("Don't Process files that are likely silent")
    else:
        PrintLog("Prcess silent files")

def OpenLoudnessSetting():
    if reaperConnect==0:
        return
    RPR.Main_OnCommandEx(RPR.NamedCommandLookup("_BR_LOUDNESS_PREF"),0,project)

def OpenPath():
    global path
    if path!='':
        os.startfile(path)
        
def test():
    item =RPR.GetMediaItem( project, 0 )
    print(item)
    Normalize(item)

    
#------------  Main GUI  -------------#



window=tk.Tk()
window.title(title+' @SZZ    Version: '+version)
window.geometry('800x600')


# Font
f1 = tkFont.Font(family='microsoft yahei', size=11, weight='bold')
f2 = tkFont.Font(family='times', size=10, slant='italic')
f3 = tkFont.Font(family='Helvetica', size=24)

# Frame
frameReaper=tk.Frame(window,width=300,height=600,relief=tk.SUNKEN,bd=3)
frameProcess=tk.Frame(window,width=300,height=600,relief=tk.GROOVE,bd=3)
frame3=tk.Frame(window,width=300,height=600,relief=tk.GROOVE,bd=1)

# Reaper
varTextReaper=tk.StringVar()
varTextReaper.set("...")   #reaper 连接状态
labelReaper=tk.Label(frameReaper,textvariable = varTextReaper)
labelReaper.pack(pady=10)
buttonReaper=tk.Button(frameReaper,text="Connect To Reaper",command = ConnectToReaper)
buttonReaper.pack(pady=20,padx=40)

lableNormalize=tk.Label(frameReaper,text="Normalize Loundness")
lableNormalize.pack(padx=20)
varCheckNormalize=tk.IntVar()
varCheckNormalize.set(1)
checkbuttonNormalize=tk.Checkbutton(frameReaper,variable=varCheckNormalize,command=CheckNormalize)
checkbuttonNormalize.pack()

lableMp3=tk.Label(frameReaper,text="Export Mp3")
lableMp3.pack(padx=20)
varCheckMp3=tk.IntVar()
varCheckMp3.set(1)
checkbuttonMp3=tk.Checkbutton(frameReaper,variable=varCheckMp3,command=CheckMp3)
checkbuttonMp3.pack()

buttonSetting=tk.Button(frameReaper,text="Open Loudness Setting",font=f2, command = OpenLoudnessSetting)
buttonSetting.pack(pady=10,padx=20)

#3
buttonProcess=tk.Button(frame3,text="Start Reaper Process",font=f1, command = BranchProcess)
buttonProcess.pack(pady=10,padx=20)
#buttonProcess=tk.Button(frame3,text="test",font=f1, command = test)
#buttonProcess.pack(pady=10,padx=20)



# mainProcess
varTextFolder=tk.StringVar()
varTextFolder.set("Please select a folder")
labelFolder=tk.Label(frameProcess,textvariable = varTextFolder,wraplength=260)
labelFolder.pack(pady=10)
buttonFolder=tk.Button(frameProcess,text="Change Folder",command = UpdatePath)
buttonFolder.pack(pady=20)

lableFilter1=tk.Label(frameProcess,text="Process Only Wave Files")
lableFilter1.pack(padx=20)
varCheckFilter1=tk.IntVar()
varCheckFilter1.set(1)
checkbuttonFilter1=tk.Checkbutton(frameProcess,variable=varCheckFilter1,command=CheckFilter1)
checkbuttonFilter1.pack()
lableFilter2=tk.Label(frameProcess,text="Don't Normalize Silent Files")
lableFilter2.pack(padx=20)
varCheckFilter2=tk.IntVar()
varCheckFilter2.set(1)
checkbuttonFilter2=tk.Checkbutton(frameProcess,variable=varCheckFilter2,command=CheckFilter2)
checkbuttonFilter2.pack()
buttonFolder2=tk.Button(frameProcess,text="Open Folder",command = OpenPath)
buttonFolder2.pack(pady=5)

# pack
frameReaper.place(x=25,y=30,anchor=tk.NW)
frameProcess.place(x=270,y=30,anchor=tk.NW)
frame3.place(x=550,y=30,anchor=tk.NW)

#Log
logtext=tk.Text(window,width=105,height=18)
logtext.place(x=25,y=320,anchor=tk.NW)


ConnectToReaper()
CheckMp3()

window.mainloop()


    
