# Basic Waapi Usage
import os
from waapi import WaapiClient
from pprint import pprint


class WwiseManager:

    #设置默认路径
    defaultSelectedObject={
        'name': 'Default Work Unit',
        'path': '\\Actor-Mixer Hierarchy\\Default Work Unit',
        'type': 'WorkUnit'
        }

    _lastSelectedObject=''

    toolname="Tool"
    info=''
    
    def __init__(self):
        self._lastSelectedObject=self.defaultSelectedObject
        print_args={
            "message": self.toolname +": Connect To Tool via Waapi"
        }        
        with WaapiClient() as client:                
            client.call("ak.soundengine.postMsgMonitor",print_args)

           
    def _msgToArgs(self,msg):
        args={
            "message": "Tool: "+msg
        }
        return args
    
    def getSelectedWwiseObjects(self):
        args_info={
            "options":{
                "return":["path", "name", "type","parent","id"]
            }
        }
        with WaapiClient() as client:
            result=client.call("ak.wwise.ui.getSelectedObjects",args_info)
            client.call("ak.soundengine.postMsgMonitor",self._msgToArgs("Choose Selected Objects"))
        print("=====Update Selected Objects====")
        #pprint(result)
        print("================================")
        try:
            self._lastSelectedObject=result['objects'][0]
        except:
            print("Please Select a Wwise Object, Use DefualtWorkUnit Instead")
            self._lastSelectedObject=self.defaultSelectedObject
            return
        return result

    def getLastSelectedWwiseObjectPath(self):        
        try:            
            self.getSelectedWwiseObjects()
            path=self._lastSelectedObject['path']
        except:
            print("!!faild get path!!")
            return
        return path

    def importAudioUnderSelectedWwiseObject(self,audiofilepath,targetfolder):
        if self._lastSelectedObject['type']=='Sound':
            print("---Please Select a legal Object to import---")
            return
        filepath,fullname=os.path.split(audiofilepath)
        fname,ext=os.path.splitext(fullname)
        print("prepare to import: "+fname+ "|| from: "+audiofilepath+ " to "+targetfolder)
        args={
            "importOperation": "replaceExisting",
            "autoAddToSourceControl": True,
            "default":{
                "importLanguage": "SFX"
            },
            "imports":[
                {
                    "objectPath":self._lastSelectedObject['path']+"\\<Sound>"+fname,
                    "audioFile": audiofilepath,
                    "originalsSubFolder": targetfolder
                }
            ]
        }
        print("------------------")
        pprint(args)
        print("------------------")
        with WaapiClient() as client:
            client.call("ak.wwise.core.audio.import",args)
            client.call("ak.soundengine.postMsgMonitor",self._msgToArgs("Import "+fname))

    def getInfo(self):
        with WaapiClient() as client:
            self.info = client.call("ak.wwise.core.getInfo")
        pprint(self.info)
        
    def smartCreateRandomContainer(self):
        count=0
        lastNamejoin=''       
        itemList=[]
        selectItems=self.getSelectedWwiseObjects()
        selectItems=selectItems['objects']
        parentId=selectItems[0]['parent']['id']
        
        for item in selectItems:
            namei=item['name']
            namesplit=namei.split('_')
            del namesplit[-1]
            namejoin='_'.join(str(i) for i in namesplit)
            if namejoin==lastNamejoin or lastNamejoin=='':
                itemList.append(item)
                lastNamejoin=namejoin
            if namejoin!=lastNamejoin : #完成一个列表
                if len(itemList)>1:
                    self.createRandomContainerAndMoveObjectsIn(lastNamejoin,itemList,parentId)
                    count=count+1
                itemList=[]
                itemList.append(item)
                lastNamejoin=namejoin

        if len(itemList)>1:
            self.createRandomContainerAndMoveObjectsIn(lastNamejoin,itemList,parentId)
            count=count+1
        return count

    def createRandomContainerAndMoveObjectsIn(self,in_name,in_items,in_parentId):

        createArgs={
            "parent": in_parentId,
            "onNameConflict": "replace",
            "autoAddToSourceControl": True,
            "type": "RandomSequenceContainer",
            "name": in_name,
        }

        with WaapiClient() as client:
            createResult=client.call("ak.wwise.core.object.create",createArgs)
            
            for item in in_items:
                itemName=item['id']
                moveArges={
                    "parent": createResult['id'],
                    "object": itemName,
                    "onNameConflict": "replace"
                }
                #pprint(moveArges)
                client.call("ak.wwise.core.object.move",moveArges)
        return

    def foldSelectedItemsIntoARandomContainer(self):
        selectItems=self.getSelectedWwiseObjects()
        selectItems=selectItems['objects']
        parentId=selectItems[0]['parent']['id']
        name0=selectItems[0]['name']
        namesplit=name0.split('_')
        del namesplit[-1]
        namejoin='_'.join(str(i) for i in namesplit)
        self.createRandomContainerAndMoveObjectsIn(namejoin,selectItems,parentId)
        return namejoin


    def findallfiles(self,path):                     # 遍历文件夹的generator，包括子文件夹，返回（文件名，文件地址）
        for root,dirs,files in os.walk(path):
            for file in files:            
                yield file,root 

    def branchImportDirectoryUnderSelectedWwisePath(self,in_osPath,in_originalPath):
        args={
            "importOperation": "replaceExisting",
            "autoAddToSourceControl": True,
            "default":{
                "importLanguage": "SFX"
            },
            "imports":[]
        }
        
        for file,root in self.findallfiles(in_osPath):
            _fullname = os.path.join(root,file)
            _fullname = os.path.normpath(_fullname)  #去掉反斜杠
            
            filepath,fullname=os.path.split(_fullname)
            fname,ext=os.path.splitext(fullname)

            newImport={
                    "objectPath":self._lastSelectedObject['path']+"\\<Sound>"+fname,
                    "audioFile": _fullname,
                    "originalsSubFolder": in_originalPath
                }

            args['imports'].append(newImport)
            
        print("---------Import---------")
        pprint(args)
        print("------------------")
        with WaapiClient() as client:
            client.call("ak.wwise.core.audio.import",args)
            client.call("ak.soundengine.postMsgMonitor",self._msgToArgs("Import "+in_osPath))


        return