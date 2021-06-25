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
                "return":["path", "name", "type"]
            }
        }
        with WaapiClient() as client:
            result=client.call("ak.wwise.ui.getSelectedObjects",args_info)
            client.call("ak.soundengine.postMsgMonitor",self._msgToArgs("Choose Selected Objects"))
        print("=====Update Selected Objects====")
        pprint(result)
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
        
