import os
import reapy
import time
import shutil
import tkinter as tk
import tkinter.filedialog

#---------- Set Global Vars & Functions ----------#
RPR = reapy.reascript_api
project = reapy.Project()
TargetTrack= RPR.GetTrack(project,0)   # 经测试，reapy的track不能被Reascript调用，因此尽量全用Reascipt的API

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
    print("set render setting "+ str(path))
    RPR.GetSetProjectInfo(proj,"RENDER_SETTINGS",0,1)
    RPR.GetSetProjectInfo(proj,"RENDER_BOUNDSFLAG",1,1)
    RPR.GetSetProjectInfo(proj,"RENDER_ADDTOPROJ",0,1)
    RPR.GetSetProjectInfo_String(proj,"RENDER_FILE",path,1)
    RPR.GetSetProjectInfo_String(proj,"RENDER_PATTERN","temp",1)
    
def BranchProcess():                        # 开始批处理
    print ("Prepare to Process "+ path)
    SetReaperRenderSetting(project,path)  # 设置Reaper工程的渲染参数
    RPR.SetOnlyTrackSelected(TargetTrack)  # 强制选择第一个轨道
    for file,root in findallfiles(path):    # 遍历整个文件夹，将每个文件导入reaper，渲染之后的文件替换原来的文件。
        fullname = os.path.join(root,file)
        print ("Processing  " + fullname)
        RenderFileInReaper(project,fullname)
        os.remove(fullname)    
        shutil.move(path + r"\temp.wav" ,fullname)
        print ("Finished")
    
def UpdatePath():                   # 用户选择文件夹路径
    global path
    print ("ask folder")
    path_ = tk.filedialog.askdirectory()
    path = path_
    var.set(path)
    if path=='':
        var.set(default)
    print ("get directory "+ path)





#------------  Main GUI  -------------#

    
default = "please select a folder"


window=tk.Tk()
window.title('Peaper Branch Render Tool @SZZ')
window.geometry('600x100')

var=tk.StringVar()
var.set(default)

label1=tk.Label(window,textvariable = var)
label1.pack()


button1=tk.Button(window,text="Change Folder",command = UpdatePath)
button1.pack()


button2=tk.Button(window,text="Start Branch Process",command = BranchProcess)
button2.pack()


window.mainloop()


    
