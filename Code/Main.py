import os
import stat
import time
import shutil
import tkinter as tk
import tkinter.filedialog
from wwisemanager import WwiseManager

path=''   # 不提前定义global的话，函数内初始化引用会出错

#---------- Set Global Vars & Functions ----------#

def ConnectToReaper():
    print("1")
    varText2.set("Trying To Connect To Reaper")
    PrintLog("Trying To Connect To Reaper")
    try:
        import reapy
        reapy.configure_reaper()
    except:
        PrintReaperError()
        PrintLog("Reapy Configuration Failed. Please Check Python settings at 'Preference/Plug-ins/ReaScript' and Restart Reaper")
        PrintLog("请确保Reaper处于开启状态，并且Preference/Plug-ins/ReaScript中关于python的设置都正确。修改设置后重启Reaper以及此工具")
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
        PrintLog("Please Restart This Tool")
        PrintLog("请重启此工具")
        return

    
    print("4")
    global TargetTrack   # 经测试，reapy的track不能被Reascript调用，因此尽量全用Reascipt的API
    TargetTrack= RPR.GetTrack(project,0)

    
    print("5")
    varText2.set("Success To Connect To Reaper")
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
    if path =='':
        PrintLog("----Please Choose a Folder First----")
        PrintLog("----请先选择一个文件夹----")
        return
    PrintLog("Prepare to Process "+ path)
    SetReaperRenderSetting(project,path)  # 设置Reaper工程的渲染参数
    RPR.SetOnlyTrackSelected(TargetTrack)  # 强制选择第一个轨道
    for file,root in findallfiles(path):    # 遍历整个文件夹，将每个文件导入reaper，渲染之后的文件替换原来的文件。
        fullname = os.path.join(root,file)
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
    
def UpdatePath():                   # 用户选择文件夹路径
    global path
    PrintLog("Select Folder ...")
    path_ = tk.filedialog.askdirectory()   
    if path_=='':
        return
    path = path_
    varText1.set(path)
    PrintLog ("Get Directory "+ path)

def PrintLog(string):                       # 在GUI里显示Log
    logtext.insert(tk.END, string + '\n') 
    logtext.see(tk.END)
    logtext.update()

def PrintReaperError():
    varText2.set("Failed To Connect To Reaper")
    PrintLog("<<<Failed To Connect To Reaper>>>")


def ConnectToWwise():
    try:
        w=WwiseManager()        
    except:
        PrintLog("<<Failed To Connect To Wwise>>")
        return
    PrintLog("Success To Connect To Wwise")

def Check1():
    print("Check: "+str(varCheck1.get()))
    if varCheck1.get()==1:
        print("Enable Wwise Input")

def ImportAudioToWwise():
    print("prepare to import audio to Wwise")

#------------  Main GUI  -------------#



window=tk.Tk()
window.title('Peaper Branch Render Tool @SZZ')
window.geometry('600x300')

varText1=tk.StringVar()
varText1.set("please select a folder")
label1=tk.Label(window,textvariable = varText1)
label1.pack()


button1=tk.Button(window,text="Change Folder",command = UpdatePath)
button1.pack()

varText2=tk.StringVar()
varText2.set("...")
label2=tk.Label(window,textvariable = varText2)
label2.pack()


button2=tk.Button(window,text="ReConnect To Reaper",command = ConnectToReaper)
button2.pack()

button3=tk.Button(window,text="Start Branch Process",command = BranchProcess)
button3.pack()

button4=tk.Button(window,text="Check Wwise Connection",command = ConnectToWwise)
button4.pack()

button5=tk.Button(window,text="Import Audio To Wwise",command = ImportAudioToWwise)
button5.pack()

varCheck1=tk.IntVar()
checkbutton1=tk.Checkbutton(window,variable=varCheck1,command=Check1)
checkbutton1.pack()

logtext=tk.Text(window,width=20,height=20)
logtext.pack(expand=1,fill=tk.BOTH,side=tk.TOP)




ConnectToReaper()



window.mainloop()


    
