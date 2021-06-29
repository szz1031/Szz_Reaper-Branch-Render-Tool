﻿import os
import stat
import time
import shutil
import tkinter as tk
import tkinter.filedialog
from wwisemanager import WwiseManager
from pprint import pprint

path=''   # 不提前定义global的话，函数内初始化引用会出错
wpath=''
wAudiopath=''
reaperConnect=0
wwiseConnect=0

#---------- Set Global Vars & Functions ----------#

def ConnectToReaper():
    global reaperConnect
    print("1")
    varTextReaper.set("Trying To Connect To Reaper")
    PrintLog("Trying To Connect To Reaper")
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
    except:
        PrintReaperError()
        reaperConnect=0
        PrintLog("===Cannot Connect Reaper via reapy. Please Restart This Tool")
        PrintLog("===reapy模块调用失败，请打开Reaper再重启此工具。如果仍不成功，请检查Reaper设置")
        return

    
    print("4")
    global TargetTrack   # 经测试，reapy的track不能被Reascript调用，因此尽量全用Reascipt的API
    TargetTrack= RPR.GetTrack(project,0)

    
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

def RenderFileInReaper(project,path):       # 将path文件顶头导入第一轨，渲染，最后删除这个item
    RPR.Main_OnCommandEx(40042,0,project)   # move Cursor to 0
    RPR.InsertMedia(path,0)                 # Insert file onto selected track
    RPR.Main_OnCommandEx(42230,0,project)   # Render with last render setting       
    track=project.tracks[0]
    item=track.items[0]
    item.delete()
        
def SetReaperRenderSetting(proj,path):  # 设置Render参数
    #PrintLog("set render setting "+ str(path))
    RPR.GetSetProjectInfo(proj,"RENDER_SETTINGS",0,1)
    RPR.GetSetProjectInfo(proj,"RENDER_BOUNDSFLAG",1,1)
    RPR.GetSetProjectInfo(proj,"RENDER_ADDTOPROJ",0,1)
    RPR.GetSetProjectInfo_String(proj,"RENDER_FILE",path,1)
    RPR.GetSetProjectInfo_String(proj,"RENDER_PATTERN","temp",1)
    
def BranchProcess():# 开始批处理
    if reaperConnect==0:
        PrintLog("Please Connect Reaper")
        return
    if path =='':
        PrintLog("<<<Please Choose a Folder First>>>")
        PrintLog("<<<请先选择一个文件夹>>>")
        return
    PrintLog("Prepare to Process "+ path)
    SetReaperRenderSetting(project,path)  # 设置Reaper工程的渲染参数
    RPR.SetOnlyTrackSelected(TargetTrack)  # 强制选择第一个轨道
    for file,root in findallfiles(path):    # 遍历整个文件夹，将每个文件导入reaper，渲染之后的文件替换原来的文件。
        fullname = os.path.join(root,file)
        fullname = os.path.normpath(fullname)  #去掉反斜杠
        PrintLog ("Processing  " + fullname)
        RenderFileInReaper(project,fullname)
        try:
            os.remove(fullname)
        except:
            PrintLog("Try to make file writable...")
            try:
                os.chmod(fullname,stat.S_IWRITE)
            except:
                PrintLog("!!!! Failed to Process a read-only file !!!!")
                os.remove(path + r"\temp.wav")
                return
            else:
                shutil.move(path + r"\temp.wav" ,fullname)
                PrintLog("Finished a read-only file")
        else:   
            shutil.move(path + r"\temp.wav" ,fullname)
            PrintLog("Finished")

        if (varCheckProcess.get()==1) and (wwiseConnect==1):
            ImportAudioToWwise(fullname,path,wAudiopath)    
    
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


# Wwise
def ConnectToWwise():
    global w
    global wwiseConnect
    try:
        w=WwiseManager()        
    except:
        PrintLog("<<Failed To Connect To Wwise>>")
        wwiseConnect=0
        varTextWwise1.set("Failed To Connect To Wwise")
        labelWwise1['fg']='red'
        return
    wwiseConnect=1
    varTextWwise1.set("Success To Connect To Wwise")
    labelWwise1['fg']='green'
    PrintLog("---Success To Connect To Wwise---")
    PrintLog("---成功连接到Wwise，可进行导入---")
    return w

def Check1():
    print("Check: "+str(varCheckProcess.get()))
    if varCheckProcess.get()==1:
        PrintLog("Enable Automatic Wwise Input")
        PrintLog("打勾此选项之后，Reaper渲染出的文件将自动导入Wwise:")
    if (wwiseConnect==0) or (reaperConnect==0):
        PrintLog("Warning: Please ensure the connection of 2 software")

def BranchImportAudioToWwise():
    if (wwiseConnect==0):
        PrintLog("Please Connect To Wwise")
        return
    if path =='':
        PrintLog("----Please Choose a Folder First----")
        PrintLog("----请先选择一个文件夹----")
        return
    PrintLog("prepare to import audio to Wwise")
    for file,root in findallfiles(path):
        _fullname = os.path.join(root,file)
        _fullname = os.path.normpath(_fullname)  #去掉反斜杠
        ImportAudioToWwise(_fullname,path,wAudiopath)

def ImportAudioToWwise(fullpath,folderpath,wroot):
    _relativePath=os.path.relpath(fullpath,folderpath)
    _filepath,_fullname=os.path.split(_relativePath)
    _wfullpath=os.path.join(wroot,_filepath)
    try:
        w.importAudioUnderSelectedWwiseObject(fullpath,_wfullpath)
    except:
        PrintLog("Faild to import file: " +_relativePath)
        print("Wwise Root:" +wpath)
        print("Wwise Originals Folder:" +wAudiopath)
        print()
    PrintLog("Success import: " +_relativePath)

def UpdateWwisePath():    
    global wpath
    global wAudiopath
    if wwiseConnect==0:
        PrintLog("Please Connect Wwise")
        return
    try:
        wpath=w.getLastSelectedWwiseObjectPath()
        wAudiopath=wpath.replace("\\Actor-Mixer Hierarchy\\",'',1)
    except:
        wpath="Wwise Object Path Unselected"
        
    varTextWwise2.set(wpath)
    print("Get selected Wwise target: "+wpath)
    print("Get orignal file path: "+wAudiopath)


    
#------------  Main GUI  -------------#



window=tk.Tk()
window.title('Peaper Branch Render Tool @SZZ')
window.geometry('780x500')

#frame = tk.Frame(window)
#frame.pack()

frameReaper=tk.Frame(window,highlightthickness=5,width=200,height=200)
frameWwise=tk.Frame(window,width=200,height=300)
frameProcess=tk.Frame(window)

# Reaper
varTextReaper=tk.StringVar()
varTextReaper.set("...")   #reaper 连接状态
labelReaper=tk.Label(frameReaper,textvariable = varTextReaper)
labelReaper.pack()
buttonReaper=tk.Button(frameReaper,text="ReConnect To Reaper",command = ConnectToReaper)
buttonReaper.pack()


# Wwise
varTextWwise1=tk.StringVar()
varTextWwise1.set("...")   #Wwise 连接状态
labelWwise1=tk.Label(frameWwise,textvariable = varTextWwise1)
labelWwise1.pack()

buttonWwise1=tk.Button(frameWwise,text="Check Wwise Connection",command = ConnectToWwise)
buttonWwise1.pack()

varTextWwise2=tk.StringVar()
varTextWwise2.set("Wwise Object Path Unset")   #Wwise 路径
labelWwise2=tk.Label(frameWwise,textvariable = varTextWwise2)
labelWwise2.pack()

buttonWwise2=tk.Button(frameWwise,text="Update Wwise Path",command = UpdateWwisePath)
buttonWwise2.pack()

buttonWwise3=tk.Button(frameWwise,text="Branch Import Audio To Wwise",command = BranchImportAudioToWwise)
buttonWwise3.pack()


# mainProcess
varTextFolder=tk.StringVar()
varTextFolder.set("please select a folder")
labelFolder=tk.Label(frameProcess,textvariable = varTextFolder)
labelFolder.pack()
buttonFolder=tk.Button(frameProcess,text="Change Folder",command = UpdatePath)
buttonFolder.pack()

lableProcess=tk.Label(frameProcess,text="是否用Reaper批处理的时候同时导入Wwise")
lableProcess.pack()
varCheckProcess=tk.IntVar()
checkbuttonProcess=tk.Checkbutton(frameProcess,variable=varCheckProcess,command=Check1)
checkbuttonProcess.pack()

buttonProcess=tk.Button(frameProcess,text="Start Branch Process",command = BranchProcess)
buttonProcess.pack()

# pack
frameReaper.place(x=25,y=30,anchor=tk.NW)
frameWwise.place(x=550,y=30,anchor=tk.NW)
frameProcess.place(x=250,y=100,anchor=tk.NW)

#Log
logtext=tk.Text(window,width=150,height=100)
logtext.place(x=0,y=250,anchor=tk.NW)


ConnectToReaper()
w=ConnectToWwise()
UpdateWwisePath()

window.mainloop()


    
