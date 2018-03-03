#!/usr/bin/env python3
#

from .uikit_bindings import *
from . import gui
from . import heartbeat
from . import utils
import ElectronCash.app

bgTask = UIBackgroundTaskInvalid

def cleanup_possible_bg_task_stuff() -> str:
    global bgTask
    msg = ""
    if heartbeat.IsRunning():
        heartbeat.Stop()
        msg += ", sent stop to heartbeat"
    else:
        msg += ", heartbeat was not running"
    if bgTask != UIBackgroundTaskInvalid:
        UIApplication.sharedApplication.endBackgroundTask_(bgTask)
        bgTask = UIBackgroundTaskInvalid
        msg += ", told UIKit to end our bgTask."
    else:
        msg += ", we did not have a bgTask active."
    return msg
    
def on_bg_task_expiration() -> None:
    msg = "Background: Expiration handler called"
    msg += cleanup_possible_bg_task_stuff()
        
    print(msg)

def startup_bg_task_stuff(application : ObjCInstance) -> None:
    print("Background: Entered background, notifying iOS about bgTask, starting up heartbeat.")
    global bgTask
    wasRunning = heartbeat.IsRunning()
    bgTask = application.beginBackgroundTaskWithName_expirationHandler_(at("Electron_Cash_Background_Task"), on_bg_task_expiration)        
    heartbeat.Start() # hopefully will cause us to continue to download and do stuff..
    if wasRunning: print("Background: Heartbeat was already active in foreground. FIXME!")    


class PythonAppDelegate(UIResponder):
    
    @objc_method
    def application_willFinishLaunchingWithOptions_(self, application : ObjCInstance, launchOptions : ObjCInstance) -> bool:
        # tell iOS that our app refreshes content in the background
        application.setMinimumBackgroundFetchInterval_(UIApplicationBackgroundFetchIntervalMinimum)
        bgStatus = "Enabled for this app." if UIBackgroundRefreshStatusAvailable == int(application.backgroundRefreshStatus) else "DISABLED"
        print("Background refresh status: %s\nBackground fetch minimum interval: %f s\nMinimum Keep Alive Timeout: %f s"%(bgStatus,UIApplicationBackgroundFetchIntervalMinimum,UIMinimumKeepAliveTimeout))
        
        return True

    @objc_method
    def application_didFinishLaunchingWithOptions_(self, application : ObjCInstance, launchOptions : ObjCInstance) -> bool:
        print("App finished launching.")

        ElectronCash.app.main()

        return True
    
    @objc_method
    def application_performFetchWithCompletionHandler_(self, application : ObjCInstance, completionHandler : ObjCInstance) -> None:
        print("Background: In fetch appDelegate handler!")
        def startHB() -> None:
            print("Background: fetch start")
            heartbeat.Start()
        def cleanup() -> None:
            print("Background: fetch cleanup")
            heartbeat.Stop()
            print("Background: About to call completion handler.. lord have mercy!")
            completionHandler(UIBackgroundFetchResultNewData)
        utils.do_in_main_thread(startHB)
        utils.call_later(9.5,cleanup)
            

    @objc_method
    def application_didChangeStatusBarOrientation_(self, application, oldStatusBarOrientation: int) -> None:
        print("ROTATED", oldStatusBarOrientation)
        gui.ElectrumGui.gui.on_rotated()

## BG/FG management... do some work in the BG

    @objc_method
    def applicationDidBecomeActive_(self, application : ObjCInstance) -> None:
        msg = "App became active" + cleanup_possible_bg_task_stuff()
        print(msg)

    @objc_method
    def applicationDidEnterBackground_(self, application : ObjCInstance) -> None:
        startup_bg_task_stuff(application)
