import os
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
version="0.7.0"

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
    track=project.tracks[0]
    item=track.items[0]
    if (varCheckNormalize.get()==1):
        RPR.SetMediaItemSelected(item,1)        # Select Item
        RPR.Main_OnCommandEx(RPR.NamedCommandLookup("_BR_NORMALIZE_LOUDNESS_ITEMS_LU"),0,project)   #标准化
    RPR.Main_OnCommandEx(42230,0,project)   # Render with last render setting       
    item.delete()
        
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
        
        newfullname=fullname
        tempPath,oldext=os.path.splitext(fullname)
        
        if varCheckMp3.get()==1 :
            ext='.mp3'
            newfullname=os.path.normpath(tempPath+ext)
        else:
            ext='.wav'
            newfullname=os.path.normpath(tempPath+ext)

        try:
            os.remove(fullname)
        except:
            PrintLog("Try to make file writable...")
            try:
                os.chmod(fullname,stat.S_IWRITE)
            except:
                PrintLog("!!!! Failed to Process a read-only file !!!!")
                os.remove(path + r"\temp"+ext)
                return
            else:
                shutil.move(path + r"\temp"+ext ,newfullname)
                PrintLog("Finished a read-only file")
        else:   
            shutil.move(path + r"\temp"+ext ,newfullname)
            PrintLog("Finished")

        if (varCheckProcess.get()==1) and (wwiseConnect==1):
            ImportAudioToWwise(newfullname,path,wAudiopath)    
    PrintLog("---Branch Process Finished---")
    
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
        PrintLog("===Enable Automatic Wwise Import===")
        PrintLog("===打勾此选项之后，Reaper渲染出的文件将自动导入Wwise===")
        if (wwiseConnect==0) or (reaperConnect==0):
            PrintLog("!!!Warning: Please Connect BOTH Reaper & Wwise!!!")

def CheckNormalize():
    if (varCheckNormalize.get()==1):
        PrintLog("+++ (SWS needed) RMS Normalize (change settings at 'SWS/BR:Global loudness preferences') +++")
        PrintLog("+++ (需要SWS插件) Reaper 导出时会同时做音量标准化(音量数值在SWS/BR:Global loudness preferences 中设置) +++")

def CheckMp3():
    SetReaperRenderSetting(project,path)
    if varCheckMp3.get()==1:
        PrintLog("Output Format: Mp3")
    else:
        PrintLog("Output Format: Wave")
        

def BranchImportAudioToWwise():
    if (wwiseConnect==0):
        PrintLog("Please Connect To Wwise")
        return
    if path =='':
        PrintLog("----Please Choose a Folder First----")
        PrintLog("----请先选择一个文件夹----")
        return
    PrintLog("Prepare to import audio files")
    #for file,root in findallfiles(path):
        #_fullname = os.path.join(root,file)
        #_fullname = os.path.normpath(_fullname)  #去掉反斜杠
        #ImportAudioToWwise(_fullname,path,wAudiopath)

    w.branchImportDirectoryUnderSelectedWwisePath(path,wAudiopath)
    PringLog("Branch Import Finished")
    

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
    PrintLog("Get Wwise target: "+wpath)
    PrintLog("Get Orignal file path: "+wAudiopath)

def SmartCreateRandomContainer():
    if (wwiseConnect==0):
        PrintLog("Please Connect To Wwise")
        return

    num=w.smartCreateRandomContainer()
    PrintLog("Create "+ str(num)+" Random Containers successfully")
    return

def CreateRandomContainerForSelectedItems():
    if (wwiseConnect==0):
        PrintLog("Please Connect To Wwise")
        return

    containerName=w.foldSelectedItemsIntoARandomContainer()
    PrintLog("Create Random Containers Named: "+containerName)
    return

#------------  Main GUI  -------------#



window=tk.Tk()
window.title('Peaper Branch Render Tool @SZZ    Version: '+version)
window.geometry('1300x600')


# Frame
frameReaper=tk.Frame(window,width=300,height=600,relief=tk.SUNKEN,bd=3)
frameWwise=tk.Frame(window,width=200,height=600,relief=tk.SUNKEN,bd=3)
frameProcess=tk.Frame(window,width=200,height=100,relief=tk.GROOVE,bd=3)

# Reaper
varTextReaper=tk.StringVar()
varTextReaper.set("...")   #reaper 连接状态
labelReaper=tk.Label(frameReaper,textvariable = varTextReaper)
labelReaper.pack(pady=10)
buttonReaper=tk.Button(frameReaper,text="ReConnect To Reaper",command = ConnectToReaper)
buttonReaper.pack(pady=20,padx=40)

lableNormalize=tk.Label(frameReaper,text="Normalize Loundness")
lableNormalize.pack(padx=20)
varCheckNormalize=tk.IntVar()
checkbuttonNormalize=tk.Checkbutton(frameReaper,variable=varCheckNormalize,command=CheckNormalize)
checkbuttonNormalize.pack()

lableMp3=tk.Label(frameReaper,text="Export Mp3")
lableMp3.pack(padx=20)
varCheckMp3=tk.IntVar()
checkbuttonMp3=tk.Checkbutton(frameReaper,variable=varCheckMp3,command=CheckMp3)
checkbuttonMp3.pack()


# Wwise
varTextWwise1=tk.StringVar()
varTextWwise1.set("...")   #Wwise 连接状态
labelWwise1=tk.Label(frameWwise,textvariable = varTextWwise1)
labelWwise1.pack()

buttonWwise1=tk.Button(frameWwise,text="Check Wwise Connection",command = ConnectToWwise)
buttonWwise1.pack(pady=5)

varTextWwise2=tk.StringVar()
varTextWwise2.set("Wwise Object Path Unset")   #Wwise 路径
labelWwise2=tk.Label(frameWwise,textvariable = varTextWwise2)
labelWwise2.pack()

buttonWwise2=tk.Button(frameWwise,text="Update Wwise Path",command = UpdateWwisePath)
buttonWwise2.pack()

buttonWwise3=tk.Button(frameWwise,text="Branch Import Audio To Wwise",command = BranchImportAudioToWwise)
buttonWwise3.pack(pady=20,padx=10)

buttonWwise4=tk.Button(frameWwise,text="Smart Create Random Container",command = SmartCreateRandomContainer)
buttonWwise4.pack(pady=0,padx=10)

buttonWwise5=tk.Button(frameWwise,text="Create Random Container For Selected Items",command = CreateRandomContainerForSelectedItems)
buttonWwise5.pack(pady=5,padx=10)

# mainProcess
varTextFolder=tk.StringVar()
varTextFolder.set("please select a folder")
labelFolder=tk.Label(frameProcess,textvariable = varTextFolder)
labelFolder.pack()
buttonFolder=tk.Button(frameProcess,text="Change Folder",command = UpdatePath)
buttonFolder.pack(pady=10)

lableProcess=tk.Label(frameProcess,text="是否用Reaper批处理的时候同时导入Wwise")
lableProcess.pack(padx=20)
varCheckProcess=tk.IntVar()
checkbuttonProcess=tk.Checkbutton(frameProcess,variable=varCheckProcess,command=Check1)
checkbuttonProcess.pack()

buttonProcess=tk.Button(frameProcess,text="Start Branch Process",command = BranchProcess)
buttonProcess.pack(pady=10)

# pack
frameReaper.place(x=25,y=30,anchor=tk.NW)
frameWwise.place(x=580,y=30,anchor=tk.NW)
frameProcess.place(x=270,y=30,anchor=tk.NW)

#Log
logtext=tk.Text(window,width=140,height=18)
logtext.place(x=25,y=310,anchor=tk.NW)


ConnectToReaper()
w=ConnectToWwise()

window.mainloop()


    
